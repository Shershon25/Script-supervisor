import time
import logging
from collections import defaultdict
from typing import Dict, List, Tuple
from fastapi import Request, HTTPException, status
from app.config import settings

logger = logging.getLogger("script_supervisor.rate_limiter")

class IPRateLimiter:
    """
    In-memory IP rate limiter supporting:
    1. Sliding window per-minute rate limits by request category (cheap, write, analysis, research, import).
    2. 24-hour rolling daily usage caps per IP for expensive operations (analysis, research, import).
    """
    def __init__(self):
        # Maps (ip, category) -> list of request timestamps (seconds)
        self._minute_requests: Dict[Tuple[str, str], List[float]] = defaultdict(list)
        # Maps (ip, category) -> list of 24h action timestamps (seconds)
        self._daily_actions: Dict[Tuple[str, str], List[float]] = defaultdict(list)

    def reset_all(self):
        """Clears all tracked IP rate limit records (used in tests)."""
        self._minute_requests.clear()
        self._daily_actions.clear()

    def _clean_old_records(self, now: float):
        # Clean minute records older than 60s
        for key in list(self._minute_requests.keys()):
            self._minute_requests[key] = [t for t in self._minute_requests[key] if now - t < 60.0]
            if not self._minute_requests[key]:
                del self._minute_requests[key]

        # Clean daily records older than 86400s (24 hours)
        for key in list(self._daily_actions.keys()):
            self._daily_actions[key] = [t for t in self._daily_actions[key] if now - t < 86400.0]
            if not self._daily_actions[key]:
                del self._daily_actions[key]

    def get_client_ip(self, request: Request) -> str:
        """Extracts client IP address handling X-Forwarded-For when behind proxy."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "127.0.0.1"

    def check_rate_limit(self, request: Request, category: str = "cheap"):
        """
        Checks both per-minute limits and 24-hour daily usage caps.
        Raises HTTP 429 status exception with Retry-After header if limits are exceeded.
        """
        now = time.time()
        self._clean_old_records(now)
        client_ip = self.get_client_ip(request)

        # 1. Determine per-minute threshold
        if category == "analysis":
            minute_limit = settings.RATE_LIMIT_ANALYSIS_PER_MIN
        elif category == "research":
            minute_limit = settings.RATE_LIMIT_RESEARCH_PER_MIN
        elif category == "import":
            minute_limit = settings.RATE_LIMIT_IMPORT_PER_MIN
        elif category == "write":
            minute_limit = settings.RATE_LIMIT_WRITE_PER_MIN
        else:
            minute_limit = settings.RATE_LIMIT_CHEAP_PER_MIN

        # Check minute window
        min_key = (client_ip, category)
        min_times = self._minute_requests[min_key]
        recent_min_times = [t for t in min_times if now - t < 60.0]
        
        if len(recent_min_times) >= minute_limit:
            oldest = recent_min_times[0]
            retry_after = max(1, int(60.0 - (now - oldest)))
            logger.warning(f"Rate limit exceeded for IP {client_ip} on category '{category}'. Limit: {minute_limit}/min. Retry-After: {retry_after}s")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded for category '{category}'. Try again in {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)}
            )

        # 2. Determine 24-hour daily threshold for expensive operations
        daily_limit = None
        if category == "analysis":
            daily_limit = settings.MAX_ANALYSES_PER_IP_PER_DAY
        elif category == "research":
            daily_limit = settings.MAX_RESEARCH_REQUESTS_PER_IP_PER_DAY
        elif category == "import":
            daily_limit = settings.MAX_IMPORTS_PER_IP_PER_DAY

        if daily_limit is not None:
            day_key = (client_ip, category)
            day_times = self._daily_actions[day_key]
            recent_day_times = [t for t in day_times if now - t < 86400.0]
            
            if len(recent_day_times) >= daily_limit:
                oldest = recent_day_times[0]
                retry_after = max(1, int(86400.0 - (now - oldest)))
                logger.warning(f"Daily usage cap exceeded for IP {client_ip} on category '{category}'. Daily Limit: {daily_limit}. Retry-After: {retry_after}s")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Daily usage quota exceeded for category '{category}' ({daily_limit}/day limit). Try again in {retry_after // 3600} hours.",
                    headers={"Retry-After": str(retry_after)}
                )

        # Record action
        self._minute_requests[min_key].append(now)
        if daily_limit is not None:
            self._daily_actions[(client_ip, category)].append(now)

limiter = IPRateLimiter()
