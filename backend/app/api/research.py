from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import ResearchTask, ResearchResult, ResearchEvaluation, Claim, Scene
from app.schemas.research import ResearchTaskResponse, ResearchSourceResponse, ResearchEvaluationResponse
from app.schemas.claim import ClaimResponse

router = APIRouter(prefix="/api/projects/{project_id}/research", tags=["External Research Tasks"])

@router.get("/{research_task_id}", response_model=ResearchTaskResponse)
def get_research_task(
    project_id: str,
    research_task_id: str,
    db: Session = Depends(get_db)
):
    """
    Returns complete research task details including objective, search sources, and Gemini evaluation.
    """
    task = db.query(ResearchTask).filter(
        ResearchTask.id == research_task_id,
        ResearchTask.project_id == project_id
    ).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research task '{research_task_id}' not found for project '{project_id}'."
        )

    scene_num = db.query(Scene.scene_number).filter(Scene.id == task.scene_id).scalar()
    claim_resp = None
    if task.claim:
        claim_resp = ClaimResponse(
            id=task.claim.id,
            project_id=task.claim.project_id,
            scene_id=task.claim.scene_id,
            scene_number=scene_num,
            claim_text=task.claim.claim_text,
            claim_type=task.claim.claim_type,
            subject=task.claim.subject,
            predicate=task.claim.predicate,
            object=task.claim.object,
            temporal_context=task.claim.temporal_context,
            location_context=task.claim.location_context,
            requires_research=task.claim.requires_research,
            research_priority=task.claim.research_priority,
            status=task.claim.status,
            claim_fingerprint=task.claim.claim_fingerprint,
            created_at=task.claim.created_at,
            updated_at=task.claim.updated_at
        )

    sources_resp = [ResearchSourceResponse.model_validate(r) for r in task.results]

    eval_resp = None
    if task.evaluations:
        e = task.evaluations[0]
        eval_resp = ResearchEvaluationResponse(
            id=e.id,
            research_task_id=e.research_task_id,
            claim_id=e.claim_id,
            verdict=e.verdict,
            confidence=e.confidence,
            summary=e.summary,
            reasoning=e.reasoning,
            supporting_source_ids=e.supporting_source_ids_json or [],
            contradicting_source_ids=e.contradicting_source_ids_json or [],
            created_at=e.created_at
        )

    return ResearchTaskResponse(
        id=task.id,
        project_id=task.project_id,
        scene_id=task.scene_id,
        claim_id=task.claim_id,
        objective=task.objective,
        status=task.status,
        provider=task.provider,
        requested_at=task.requested_at,
        completed_at=task.completed_at,
        error_message=task.error_message,
        claim=claim_resp,
        sources=sources_resp,
        evaluation=eval_resp,
        created_at=task.created_at,
        updated_at=task.updated_at
    )


@router.get("", response_model=List[ResearchTaskResponse])
def list_research_tasks(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    Returns all research tasks for a project, including sources and evaluations.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project '{project_id}' not found.")

    tasks = db.query(ResearchTask).filter(
        ResearchTask.project_id == project_id
    ).order_by(ResearchTask.created_at.desc()).all()

    response_list = []
    for task in tasks:
        scene_num = db.query(Scene.scene_number).filter(Scene.id == task.scene_id).scalar()
        claim_resp = None
        if task.claim:
            claim_resp = ClaimResponse(
                id=task.claim.id,
                project_id=task.claim.project_id,
                scene_id=task.claim.scene_id,
                scene_number=scene_num,
                claim_text=task.claim.claim_text,
                claim_type=task.claim.claim_type,
                subject=task.claim.subject,
                predicate=task.claim.predicate,
                object=task.claim.object,
                temporal_context=task.claim.temporal_context,
                location_context=task.claim.location_context,
                requires_research=task.claim.requires_research,
                research_priority=task.claim.research_priority,
                status=task.claim.status,
                claim_fingerprint=task.claim.claim_fingerprint,
                created_at=task.claim.created_at,
                updated_at=task.claim.updated_at
            )

        sources_resp = [ResearchSourceResponse.model_validate(r) for r in task.results]

        eval_resp = None
        if task.evaluations:
            e = task.evaluations[0]
            eval_resp = ResearchEvaluationResponse(
                id=e.id,
                research_task_id=e.research_task_id,
                claim_id=e.claim_id,
                verdict=e.verdict,
                confidence=e.confidence,
                summary=e.summary,
                reasoning=e.reasoning,
                supporting_source_ids=e.supporting_source_ids_json or [],
                contradicting_source_ids=e.contradicting_source_ids_json or [],
                created_at=e.created_at
            )

        response_list.append(ResearchTaskResponse(
            id=task.id,
            project_id=task.project_id,
            scene_id=task.scene_id,
            claim_id=task.claim_id,
            objective=task.objective,
            status=task.status,
            provider=task.provider,
            requested_at=task.requested_at,
            completed_at=task.completed_at,
            error_message=task.error_message,
            claim=claim_resp,
            sources=sources_resp,
            evaluation=eval_resp,
            created_at=task.created_at,
            updated_at=task.updated_at
        ))

    return response_list
