from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.continuity import get_project_issues
from app.services.issue_review import review_issue, get_issue_history, get_issue_summary
from app.schemas.issue import IssueResponse, IssueEvidence
from app.schemas.issue_review import IssueReviewCreate, IssueReviewResponse, IssueSummaryResponse
from app.db.models import Issue, Scene, IssueReview

router = APIRouter(prefix="/api/projects/{project_id}/issues", tags=["Continuity Issues"])

@router.get("", response_model=List[IssueResponse])
def list_issues(
    project_id: str,
    status: Optional[str] = Query(None, description="Filter by status e.g. OPEN, ACCEPTED, IGNORED, RESOLVED"),
    severity: Optional[str] = Query(None, description="Filter by severity e.g. INFO, WARNING, ERROR"),
    db: Session = Depends(get_db)
):
    """
    Returns list of continuity issues detected for a project.
    Supports status and severity query parameter filters.
    """
    return get_project_issues(db=db, project_id=project_id, status_filter=status, severity_filter=severity)

@router.get("/summary", response_model=IssueSummaryResponse)
def get_issues_summary(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Returns summary counts of open, accepted, resolved, ignored, and error issues for UI badges."""
    return get_issue_summary(db=db, project_id=project_id)

@router.get("/{issue_id}", response_model=IssueResponse)
def get_issue_by_id(
    project_id: str,
    issue_id: str,
    db: Session = Depends(get_db)
):
    """Returns single continuity issue by ID with full grounded evidence and review history."""
    result = db.query(Issue, Scene.scene_number).join(Scene, Issue.scene_id == Scene.id)\
        .filter(Issue.id == issue_id, Issue.project_id == project_id).first()

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Issue '{issue_id}' not found for project '{project_id}'."
        )

    issue_obj, scene_num = result
    evidence_items = [IssueEvidence(**e) for e in (issue_obj.evidence_json or [])]
    reviews = db.query(IssueReview).filter(IssueReview.issue_id == issue_obj.id).order_by(IssueReview.created_at.asc()).all()
    review_responses = [IssueReviewResponse.model_validate(r) for r in reviews]

    return IssueResponse(
        id=issue_obj.id,
        project_id=issue_obj.project_id,
        scene_id=issue_obj.scene_id,
        scene_number=scene_num,
        issue_type=issue_obj.issue_type,
        severity=issue_obj.severity,
        title=issue_obj.title,
        description=issue_obj.description,
        confidence=issue_obj.confidence,
        status=issue_obj.status,
        evidence=evidence_items,
        reviewed_at=issue_obj.reviewed_at,
        reviewed_by=issue_obj.reviewed_by,
        resolution_type=issue_obj.resolution_type,
        resolution_note=issue_obj.resolution_note,
        issue_fingerprint=issue_obj.issue_fingerprint,
        reviews=review_responses,
        created_at=issue_obj.created_at
    )

@router.post("/{issue_id}/review")
def review_issue_endpoint(
    project_id: str,
    issue_id: str,
    review_in: IssueReviewCreate,
    db: Session = Depends(get_db)
):
    """
    Day 4 Core Endpoint:
    Submits a writer review action (ACCEPT | IGNORE | RESOLVE | REOPEN) with resolution note.
    Atomically updates issue status and records audit history.
    """
    updated_issue, review_record = review_issue(
        db=db,
        project_id=project_id,
        issue_id=issue_id,
        review_in=review_in
    )

    # Fetch scene number for response
    scene_num = db.query(Scene.scene_number).filter(Scene.id == updated_issue.scene_id).scalar()
    evidence_items = [IssueEvidence(**e) for e in (updated_issue.evidence_json or [])]
    all_reviews = db.query(IssueReview).filter(IssueReview.issue_id == updated_issue.id).order_by(IssueReview.created_at.asc()).all()

    issue_resp = IssueResponse(
        id=updated_issue.id,
        project_id=updated_issue.project_id,
        scene_id=updated_issue.scene_id,
        scene_number=scene_num,
        issue_type=updated_issue.issue_type,
        severity=updated_issue.severity,
        title=updated_issue.title,
        description=updated_issue.description,
        confidence=updated_issue.confidence,
        status=updated_issue.status,
        evidence=evidence_items,
        reviewed_at=updated_issue.reviewed_at,
        reviewed_by=updated_issue.reviewed_by,
        resolution_type=updated_issue.resolution_type,
        resolution_note=updated_issue.resolution_note,
        issue_fingerprint=updated_issue.issue_fingerprint,
        reviews=[IssueReviewResponse.model_validate(r) for r in all_reviews],
        created_at=updated_issue.created_at
    )

    return {
        "issue": issue_resp,
        "review": IssueReviewResponse.model_validate(review_record)
    }

@router.get("/{issue_id}/history", response_model=List[IssueReviewResponse])
def get_issue_history_endpoint(
    project_id: str,
    issue_id: str,
    db: Session = Depends(get_db)
):
    """Returns chronological audit trail of all review decisions for an issue."""
    history = get_issue_history(db=db, project_id=project_id, issue_id=issue_id)
    return [IssueReviewResponse.model_validate(r) for r in history]
