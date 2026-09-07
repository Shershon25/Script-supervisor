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

    resp = []
    for c, scene_num in results:
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
