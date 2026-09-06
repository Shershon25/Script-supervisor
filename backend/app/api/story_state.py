from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.story_state import build_story_state, get_story_state_summary
from app.schemas.story_state import StoryStateResponse, StoryStateSummaryResponse

router = APIRouter(prefix="/api/projects/{project_id}/story-state", tags=["Story State"])

@router.get("", response_model=StoryStateResponse)
def get_story_state(project_id: str, db: Session = Depends(get_db)):
    """
    Returns the complete, derived persistent Story State for a project.
    Aggregates Characters, Locations, Objects, Facts, Events, Relationships,
    and Character Knowledge States across all scenes.
    """
    return build_story_state(db=db, project_id=project_id)

@router.get("/summary", response_model=StoryStateSummaryResponse)
def get_story_state_summary_endpoint(project_id: str, db: Session = Depends(get_db)):
    """Returns quick counts overview of current Story State elements."""
    return get_story_state_summary(db=db, project_id=project_id)
