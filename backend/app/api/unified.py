from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.unified import UnifiedAnalysisResponse
from app.services.unified_supervisor import process_scene_unified
from app.db.models import SceneAnalysisRun, Scene

router = APIRouter(prefix="/api/projects", tags=["unified"])

@router.post("/{project_id}/scenes/{scene_id}/analyze", response_model=UnifiedAnalysisResponse, status_code=status.HTTP_200_OK)
def analyze_scene_unified_endpoint(
    project_id: str,
    scene_id: str,
    clear_project_entities: bool = False,
    db: Session = Depends(get_db)
):
    """
    Triggers end-to-end Unified Script Supervisor Analysis for a scene.
    Orchestrates parsing, historical boundary checking, hybrid retrieval, deterministic checks,
    AI story reasoning, gated external research, and issue deduplication.
    """
    try:
        return process_scene_unified(db, project_id, scene_id, clear_project_entities=clear_project_entities)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unified analysis failed: {str(e)}")


@router.get("/{project_id}/scenes/{scene_id}/analysis")
def get_scene_analysis_run_endpoint(
    project_id: str,
    scene_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieves latest SceneAnalysisRun status and summary.
    """
    scene = db.query(Scene).filter(Scene.id == scene_id, Scene.project_id == project_id).first()
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scene '{scene_id}' not found in project '{project_id}'."
        )

    run = db.query(SceneAnalysisRun).filter(
        SceneAnalysisRun.project_id == project_id,
        SceneAnalysisRun.scene_id == scene_id
    ).order_by(SceneAnalysisRun.completed_at.desc()).first()

    if not run:
        return {"scene_id": scene_id, "status": "IDLE", "summary": None}

    return {
        "run_id": run.id,
        "project_id": run.project_id,
        "scene_id": run.scene_id,
        "status": run.status,
        "summary": {
            "entities_count": run.entities_count,
            "facts_count": run.facts_count,
            "events_count": run.events_count,
            "issues_count": run.issues_count,
            "claims_count": run.claims_count,
            "research_reused_count": run.research_reused_count
        },
        "error_message": run.error_message,
        "started_at": run.started_at,
        "completed_at": run.completed_at
    }
