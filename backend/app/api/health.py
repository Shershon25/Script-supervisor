import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.database import get_db
from app.db.models import Project, Scene, Entity, Fact, Event, Relationship, KnowledgeState, Issue

logger = logging.getLogger("script_supervisor.health")

router = APIRouter(prefix="/api", tags=["Health & Maintenance"])

@router.get("/health")
def health_check():
    return {"status": "ok", "service": "Script Supervisor Backend"}

from app.config import settings

@router.delete("/reset-db")
def reset_database(
    project_id: Optional[str] = Query(None, description="Optional project ID to reset. If provided, clears only scenes and state for this project."),
    include_projects: bool = Query(False, description="If True and project_id is None, also deletes all Project records."),
    db: Session = Depends(get_db)
):
    """
    Resets screenplay data. Restricted to development mode.
    """
    if settings.ENVIRONMENT == "production" or not settings.DEBUG:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Database reset endpoint is disabled in production environment."
        )

    try:
        if project_id:
            logger.info(f"Resetting database scenes & story state for project_id='{project_id}'...")
            
            # Delete dependent records for specific project
            db.query(Issue).filter(Issue.project_id == project_id).delete(synchronize_session=False)
            db.query(KnowledgeState).filter(KnowledgeState.project_id == project_id).delete(synchronize_session=False)
            db.query(Relationship).filter(Relationship.project_id == project_id).delete(synchronize_session=False)
            db.query(Fact).filter(Fact.project_id == project_id).delete(synchronize_session=False)
            
            # Events join with Scene
            scene_ids = [s.id for s in db.query(Scene.id).filter(Scene.project_id == project_id).all()]
            if scene_ids:
                db.query(Event).filter(Event.scene_id.in_(scene_ids)).delete(synchronize_session=False)

            db.query(Entity).filter(Entity.project_id == project_id).delete(synchronize_session=False)
            db.query(Scene).filter(Scene.project_id == project_id).delete(synchronize_session=False)

            if include_projects:
                db.query(Project).filter(Project.id == project_id).delete(synchronize_session=False)

            db.commit()
            return {"status": "ok", "message": f"Successfully cleared scenes and story state for project '{project_id}'."}

        else:
            logger.info("Resetting scenes & story state across all projects...")
            db.query(Issue).delete()
            db.query(KnowledgeState).delete()
            db.query(Relationship).delete()
            db.query(Fact).delete()
            db.query(Event).delete()
            db.query(Entity).delete()
            db.query(Scene).delete()

            if include_projects:
                db.query(Project).delete()

            db.commit()
            return {"status": "ok", "message": "Successfully cleared all scenes and story state."}

    except Exception as e:
        db.rollback()
        logger.error(f"Error resetting database: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database reset failed: {str(e)}"
        )
