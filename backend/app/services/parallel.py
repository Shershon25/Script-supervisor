import logging
import httpx
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
from fastapi import HTTPException, status
from app.config import settings

logger = logging.getLogger("script_supervisor.parallel")

class ParallelSource:
    def __init__(self, title: str, url: str, domain: str, excerpt: str, relevance_score: float = 1.0, raw_metadata: dict = None):
        self.title = title
        self.url = url
        self.domain = domain
        self.excerpt = excerpt
        self.relevance_score = relevance_score
        self.raw_metadata = raw_metadata or {}

def extract_domain(url: str) -> str:
    try:
        parsed = urlparse(url)
        return parsed.netloc or "external-source"
    except Exception:
        return "external-source"


def execute_parallel_search(objective: str) -> List[ParallelSource]:
    """
    Executes a web research query using the Parallel API.
    Raises HTTPException if API key is unconfigured or request fails.
    """
    api_key = settings.PARALLEL_API_KEY.strip() if settings.PARALLEL_API_KEY else ""

    if not api_key or api_key.lower() in ("", "mock", "none", "your_parallel_api_key_here"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Parallel API key is not configured. Please set PARALLEL_API_KEY in .env."
        )

    logger.info(f"Invoking Parallel API for objective: '{objective[:80]}...'")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "search_queries": [objective],
        "objective": objective
    }

    endpoint = "https://api.parallel.ai/v1/search"

    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(endpoint, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                raw_results = data.get("results") or data.get("sources") or data.get("data") or []
                
                sources = []
                for item in raw_results:
                    title = item.get("title") or item.get("name") or "Search Evidence Result"
                    url = item.get("url") or item.get("link") or "https://parallel.ai"
                    domain = item.get("domain") or extract_domain(url)
                    
                    excerpts_list = item.get("excerpts") or []
                    if isinstance(excerpts_list, list) and excerpts_list:
                        excerpt = excerpts_list[0]
                    else:
                        excerpt = item.get("excerpt") or item.get("snippet") or item.get("text") or ""
                        
                    score = float(item.get("relevance_score") or item.get("score") or 1.0)

                    if excerpt or title:
                        sources.append(ParallelSource(
                            title=title,
                            url=url,
                            domain=domain,
                            excerpt=excerpt or title,
                            relevance_score=score,
                            raw_metadata=item
                        ))

                if sources:
                    logger.info(f"Successfully retrieved {len(sources)} live sources from Parallel API.")
                    return sources
            
            raise ValueError(f"Parallel API returned HTTP {resp.status_code}: {resp.text[:200]}")

    except Exception as e:
        logger.error(f"Parallel API call to {endpoint} failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Parallel Search API call failed: {str(e)}"
        )

