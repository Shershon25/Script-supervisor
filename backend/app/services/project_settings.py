import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.models import Project, ProjectSettings, StoryWorldRule

logger = logging.getLogger("script_supervisor.project_settings_service")

def get_or_create_project_settings(db: Session, project_id: str) -> ProjectSettings:
    """Retrieves or automatically creates default settings (reality_level=5, continuity_strictness=5) for a project."""
    settings = db.query(ProjectSettings).filter(ProjectSettings.project_id == project_id).first()
    if not settings:
        logger.info(f"Creating default ProjectSettings for project '{project_id}'")
        settings = ProjectSettings(
            project_id=project_id,
            reality_level=5,
            continuity_strictness=5,
            settings_version=1
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings

def bump_settings_version(db: Session, project_id: str) -> ProjectSettings:
    """Increments project settings version to mark existing scene analysis runs as stale."""
    settings = get_or_create_project_settings(db, project_id)
    settings.settings_version += 1
    db.commit()
    db.refresh(settings)
    return settings

def get_active_world_rules(db: Session, project_id: str) -> List[StoryWorldRule]:
    """Retrieves all active Story World Rules for a specific project."""
    return db.query(StoryWorldRule).filter(
        StoryWorldRule.project_id == project_id,
        StoryWorldRule.active == True
    ).order_by(StoryWorldRule.created_at.asc()).all()
