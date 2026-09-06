from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.reasoning import ReasoningRequest, ReasoningResult
from app.services.reasoning import execute_targeted_reasoning

router = APIRouter(prefix="/api/projects/{project_id}/reason", tags=["AI Story Reasoning"])

@router.post("", response_model=ReasoningResult)
def execute_reasoning_endpoint(
    project_id: str,
    body: ReasoningRequest,
    db: Session = Depends(get_db)
):
    """
    Day 6 Reasoning Endpoint:
    Executes hybrid retrieval, assembles task-specific context with provenance tags,
    and returns targeted Gemini story reasoning.
    """
    result = execute_targeted_reasoning(
        db=db,
        project_id=project_id,
        scene_id=body.scene_id,
        task_type=body.task_type,
        target_entity_names=body.target_entity_names,
        question=body.question
    )

    return result
