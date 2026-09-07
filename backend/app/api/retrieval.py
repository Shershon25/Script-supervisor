from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Scene
from app.schemas.retrieval import RetrievalRequest, RetrievalResponse
from app.services.retriever import hybrid_retrieve_context

router = APIRouter(prefix="/api/projects/{project_id}/retrieve-context", tags=["Context Retrieval"])

@router.post("", response_model=RetrievalResponse)
def retrieve_context_endpoint(
    project_id: str,
    body: RetrievalRequest,
    db: Session = Depends(get_db)
):
    """
    Context Retrieval Endpoint:
    Returns ranked hybrid retrieved evidence items (SQL facts, events, writer decisions, research evidence) for a scene.
    """
    scene = db.query(Scene).filter(Scene.id == body.scene_id, Scene.project_id == project_id).first()
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scene '{body.scene_id}' not found for project '{project_id}'."
        )

    items = hybrid_retrieve_context(
        db=db,
        project_id=project_id,
        scene_number=scene.scene_number,
        scene_text=body.query_text or scene.raw_text,
        task_type=body.task_type,
        entity_names=body.entity_names
    )

    return RetrievalResponse(
        project_id=project_id,
        scene_id=scene.id,
        scene_number=scene.scene_number,
        task_type=body.task_type,
        total_retrieved=len(items),
        items=items
    )
