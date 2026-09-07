from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Claim, Scene, ResearchTask, Project
from app.schemas.claim import ClaimResponse
from app.services.research_service import execute_research_for_claim

router = APIRouter(prefix="/api/projects/{project_id}/claims", tags=["External Claims & Reality"])

@router.get("", response_model=List[ClaimResponse])
def list_claims(
    project_id: str,
    claim_type: Optional[str] = Query(None, description="REAL_WORLD_CLAIM | FICTIONAL_WORLD_RULE | STORY_FACT"),
    status: Optional[str] = Query(None, description="UNVERIFIED | VERIFIED | CONTRADICTED | INCONCLUSIVE"),
    requires_research: Optional[bool] = Query(None, description="Filter claims requiring research"),
    db: Session = Depends(get_db)
):
    """Lists all extracted claims for a project with optional filters."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project '{project_id}' not found.")

    query = db.query(Claim, Scene.scene_number).join(Scene, Claim.scene_id == Scene.id)\
        .filter(Claim.project_id == project_id)

    if claim_type:
        query = query.filter(Claim.claim_type == claim_type.upper())
    if status:
        query = query.filter(Claim.status == status.upper())
    if requires_research is not None:
        query = query.filter(Claim.requires_research == requires_research)

    results = query.order_by(Scene.scene_number.asc(), Claim.created_at.desc()).all()

    # Pre-fetch completed research tasks to attach sources & evaluations directly to claims
    claim_ids = [c.id for c, _ in results]
    tasks = (
        db.query(ResearchTask)
        .filter(ResearchTask.claim_id.in_(claim_ids), ResearchTask.status == "COMPLETED")
        .order_by(ResearchTask.created_at.desc())
        .all()
    ) if claim_ids else []

    task_by_claim = {}
    for t in tasks:
        if t.claim_id not in task_by_claim:
            task_by_claim[t.claim_id] = t

    resp = []
    for c, scene_num in results:
        t = task_by_claim.get(c.id)
        sources_resp = [
            {
                "id": r.id,
                "research_task_id": r.research_task_id,
                "title": r.title,
                "url": r.url,
                "domain": r.domain,
                "excerpt": r.excerpt,
                "relevance_score": r.relevance_score,
                "retrieved_at": r.retrieved_at.isoformat() if r.retrieved_at else None,
            }
            for r in t.results
        ] if t and t.results else []

        eval_resp = None
        if t and t.evaluations:
            e = t.evaluations[0]
            eval_resp = {
                "id": e.id,
                "research_task_id": e.research_task_id,
                "claim_id": e.claim_id,
                "verdict": e.verdict,
                "confidence": e.confidence,
                "summary": e.summary,
                "reasoning": e.reasoning,
                "supporting_source_ids": e.supporting_source_ids_json or [],
                "contradicting_source_ids": e.contradicting_source_ids_json or [],
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }

        resp.append(ClaimResponse(
            id=c.id,
            project_id=c.project_id,
            scene_id=c.scene_id,
            scene_number=scene_num,
            claim_text=c.claim_text,
            claim_type=c.claim_type,
            subject=c.subject,
            predicate=c.predicate,
            object=c.object,
            temporal_context=c.temporal_context,
            location_context=c.location_context,
            requires_research=c.requires_research,
            research_priority=c.research_priority,
            status=c.status,
            claim_fingerprint=c.claim_fingerprint,
            sources=sources_resp,
            evaluation=eval_resp,
            created_at=c.created_at,
            updated_at=c.updated_at
        ))

    return resp


@router.post("/{claim_id}/research")
def trigger_claim_research(
    project_id: str,
    claim_id: str,
    force_refresh: bool = Query(False, description="Force re-query Parallel Search API"),
    db: Session = Depends(get_db)
):
    """
    Core Research Endpoint:
    Triggers or re-runs Parallel web research for a specific claim.
    """
    task, eval_obj = execute_research_for_claim(
        db=db,
        project_id=project_id,
        claim_id=claim_id,
        force_refresh=force_refresh
    )

    return {
        "status": "ok",
        "task_id": task.id,
        "verdict": eval_obj.verdict,
        "confidence": eval_obj.confidence,
        "summary": eval_obj.summary
    }
