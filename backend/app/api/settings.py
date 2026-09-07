from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Project, ProjectSettings, StoryWorldRule
from app.schemas.settings import (
    ProjectSettingsResponse, ProjectSettingsUpdate,
    StoryWorldRuleCreate, StoryWorldRuleUpdate, StoryWorldRuleResponse
)
from app.services.project_settings import (
    get_or_create_project_settings, bump_settings_version, get_active_world_rules
)

router = APIRouter(prefix="/api/projects/{project_id}/settings", tags=["Settings"])

def verify_project_exists(db: Session, project_id: str) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project '{project_id}' not found.")
    return project

@router.get("", response_model=ProjectSettingsResponse)
def get_project_settings_endpoint(project_id: str, db: Session = Depends(get_db)):
    """Retrieves settings and story world rules for a project."""
    verify_project_exists(db, project_id)
    settings = get_or_create_project_settings(db, project_id)
    rules = db.query(StoryWorldRule).filter(StoryWorldRule.project_id == project_id).order_by(StoryWorldRule.created_at.asc()).all()
    
    return ProjectSettingsResponse(
        id=settings.id,
        project_id=settings.project_id,
        reality_level=settings.reality_level,
        continuity_strictness=settings.continuity_strictness,
        auto_background_analysis_enabled=settings.auto_background_analysis_enabled,
        settings_version=settings.settings_version,
        world_rules=[StoryWorldRuleResponse.model_validate(r) for r in rules],
        created_at=settings.created_at,
        updated_at=settings.updated_at
    )

@router.put("", response_model=ProjectSettingsResponse)
@router.patch("", response_model=ProjectSettingsResponse)
def update_project_settings_endpoint(
    project_id: str,
    payload: ProjectSettingsUpdate,
    db: Session = Depends(get_db)
):
    """Updates reality level (0-10), continuity strictness (0-10), and auto_background_analysis_enabled for a project."""
    verify_project_exists(db, project_id)
    settings = get_or_create_project_settings(db, project_id)

    updated = False
    if payload.reality_level is not None:
        if not (0 <= payload.reality_level <= 10):
            raise HTTPException(status_code=400, detail="reality_level must be between 0 and 10")
        settings.reality_level = payload.reality_level
        updated = True

    if payload.continuity_strictness is not None:
        if not (0 <= payload.continuity_strictness <= 10):
            raise HTTPException(status_code=400, detail="continuity_strictness must be between 0 and 10")
        settings.continuity_strictness = payload.continuity_strictness
        updated = True

    if payload.auto_background_analysis_enabled is not None:
        settings.auto_background_analysis_enabled = payload.auto_background_analysis_enabled
        updated = True

    if updated:
        settings.settings_version += 1
        db.commit()
        db.refresh(settings)

    rules = db.query(StoryWorldRule).filter(StoryWorldRule.project_id == project_id).order_by(StoryWorldRule.created_at.asc()).all()
    return ProjectSettingsResponse(
        id=settings.id,
        project_id=settings.project_id,
        reality_level=settings.reality_level,
        continuity_strictness=settings.continuity_strictness,
        auto_background_analysis_enabled=settings.auto_background_analysis_enabled,
        settings_version=settings.settings_version,
        world_rules=[StoryWorldRuleResponse.model_validate(r) for r in rules],
        created_at=settings.created_at,
        updated_at=settings.updated_at
    )

@router.get("/world-rules", response_model=List[StoryWorldRuleResponse])
def list_world_rules_endpoint(project_id: str, db: Session = Depends(get_db)):
    """Lists all story world rules for a project."""
    verify_project_exists(db, project_id)
    rules = db.query(StoryWorldRule).filter(StoryWorldRule.project_id == project_id).order_by(StoryWorldRule.created_at.asc()).all()
    return rules

@router.post("/world-rules", response_model=StoryWorldRuleResponse, status_code=status.HTTP_201_CREATED)
def create_world_rule_endpoint(
    project_id: str,
    payload: StoryWorldRuleCreate,
    db: Session = Depends(get_db)
):
    """Creates a user-authored Story World Rule for a project."""
    verify_project_exists(db, project_id)
    rule_text = payload.rule_text.strip()
    if not rule_text:
        raise HTTPException(status_code=400, detail="rule_text cannot be empty")

    rule = StoryWorldRule(
        project_id=project_id,
        rule_text=rule_text,
        active=payload.active
    )
    db.add(rule)
    bump_settings_version(db, project_id)
    db.commit()
    db.refresh(rule)
    return rule

@router.patch("/world-rules/{rule_id}", response_model=StoryWorldRuleResponse)
def update_world_rule_endpoint(
    project_id: str,
    rule_id: str,
    payload: StoryWorldRuleUpdate,
    db: Session = Depends(get_db)
):
    """Updates a Story World Rule (text or active status). Verifies rule ownership against project_id."""
    verify_project_exists(db, project_id)
    rule = db.query(StoryWorldRule).filter(
        StoryWorldRule.id == rule_id,
        StoryWorldRule.project_id == project_id
    ).first()

    if not rule:
        raise HTTPException(status_code=404, detail=f"World rule '{rule_id}' not found for project '{project_id}'")

    if payload.rule_text is not None:
        text = payload.rule_text.strip()
        if not text:
            raise HTTPException(status_code=400, detail="rule_text cannot be empty")
        rule.rule_text = text

    if payload.active is not None:
        rule.active = payload.active

    bump_settings_version(db, project_id)
    db.commit()
    db.refresh(rule)
    return rule

@router.delete("/world-rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_world_rule_endpoint(
    project_id: str,
    rule_id: str,
    db: Session = Depends(get_db)
):
    """Deletes a Story World Rule. Verifies rule ownership against project_id."""
    verify_project_exists(db, project_id)
    rule = db.query(StoryWorldRule).filter(
        StoryWorldRule.id == rule_id,
        StoryWorldRule.project_id == project_id
    ).first()

    if not rule:
        raise HTTPException(status_code=404, detail=f"World rule '{rule_id}' not found for project '{project_id}'")

    db.delete(rule)
    bump_settings_version(db, project_id)
    db.commit()
    return None
