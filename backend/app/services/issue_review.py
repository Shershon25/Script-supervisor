import logging
import hashlib
from datetime import datetime, timezone
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.db.models import Issue, IssueReview, Project, Scene
from app.schemas.issue_review import IssueReviewCreate, IssueReviewResponse, IssueSummaryResponse

logger = logging.getLogger("script_supervisor.issue_review")

def utc_now():
    return datetime.now(timezone.utc)

def compute_issue_fingerprint(project_id: str, issue_type: str, entity_name: str, evidence_scene_numbers: List[int]) -> str:
    """
    Computes a deterministic SHA-256 fingerprint for deduplication & decision suppression.
    Fingerprint = sha256(project_id : issue_type : normalized_entity : sorted_scene_numbers)
    """
    sorted_scenes = ",".join(str(s) for s in sorted(set(evidence_scene_numbers)))
    raw_str = f"{project_id}:{issue_type.upper()}:{entity_name.strip().lower()}:{sorted_scenes}"
    return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()

def review_issue(db: Session, project_id: str, issue_id: str, review_in: IssueReviewCreate) -> Tuple[Issue, IssueReview]:
    """
    Core Issue Review Service:
    Atomically updates issue status, resolution metadata, and records audit history.
    Validates state transitions (OPEN -> ACCEPTED/IGNORED/RESOLVED, REOPEN -> OPEN).
    """
    logger.info(f"Reviewing issue_id='{issue_id}' for project_id='{project_id}' with action='{review_in.action}'")

    issue = db.query(Issue).filter(Issue.id == issue_id, Issue.project_id == project_id).first()
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Issue '{issue_id}' not found for project '{project_id}'."
        )

    action = review_in.action.upper()
    previous_status = issue.status
    new_status = previous_status

    # Validate state transitions
    if action == "ACCEPT":
        if previous_status not in ("OPEN", "NEEDS_REVIEW"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot ACCEPT issue in '{previous_status}' status. Must be OPEN."
            )
        new_status = "ACCEPTED"

    elif action == "IGNORE":
        if previous_status in ("RESOLVED", "IGNORED"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot IGNORE issue already in '{previous_status}' status."
            )
        new_status = "IGNORED"

    elif action == "RESOLVE":
        if previous_status in ("RESOLVED", "IGNORED"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot RESOLVE issue already in '{previous_status}' status."
            )
        if not review_in.note or not review_in.note.strip():
            review_in.note = f"Resolved by writer for {issue.title}"
        new_status = "RESOLVED"

    elif action == "REOPEN":
        if previous_status == "OPEN":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Issue is already OPEN."
            )
        new_status = "OPEN"

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid review action '{action}'. Allowed actions: ACCEPT, IGNORE, RESOLVE, REOPEN."
        )

    try:
        # 1. Create IssueReview history record
        review_record = IssueReview(
            issue_id=issue.id,
            project_id=project_id,
            action=action,
            note=review_in.note.strip() if review_in.note else None,
            previous_status=previous_status,
            new_status=new_status,
            created_at=utc_now()
        )
        db.add(review_record)

        # 2. Update Issue fields
        issue.status = new_status
        issue.reviewed_at = utc_now()
        issue.reviewed_by = "writer"
        if review_in.resolution_type:
            issue.resolution_type = review_in.resolution_type.upper()
        elif action == "IGNORE" and not issue.resolution_type:
            issue.resolution_type = "FALSE_POSITIVE"
        elif action == "ACCEPT" and not issue.resolution_type:
            issue.resolution_type = "NEEDS_REVIEW"

        if review_in.note:
            issue.resolution_note = review_in.note.strip()

        # 3. If writer marks as ACCEPT / INTENTIONAL, register as an active Story World Rule
        if action == "ACCEPT" and (issue.resolution_type == "INTENTIONAL" or (review_in.resolution_type and review_in.resolution_type.upper() == "INTENTIONAL")):
            from app.db.models import StoryWorldRule
            rule_text = issue.title if len(issue.title) > 10 else issue.description[:200]
            existing_rule = db.query(StoryWorldRule).filter(
                StoryWorldRule.project_id == project_id,
                StoryWorldRule.rule_text == rule_text
            ).first()
            if not existing_rule:
                new_rule = StoryWorldRule(
                    project_id=project_id,
                    rule_text=rule_text,
                    active=True
                )
                db.add(new_rule)
                logger.info(f"Automatically registered active StoryWorldRule '{rule_text}' from writer review decision.")

        db.commit()
        db.refresh(issue)
        db.refresh(review_record)

        logger.info(f"Successfully reviewed issue '{issue_id}': '{previous_status}' -> '{new_status}'.")
        return issue, review_record

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error reviewing issue '{issue_id}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process issue review: {str(e)}"
        )

def get_issue_history(db: Session, project_id: str, issue_id: str) -> List[IssueReview]:
    """Returns chronological audit trail of all writer review actions for an issue."""
    return db.query(IssueReview).filter(
        IssueReview.issue_id == issue_id,
        IssueReview.project_id == project_id
    ).order_by(IssueReview.created_at.asc()).all()

def get_issue_summary(db: Session, project_id: str) -> IssueSummaryResponse:
    """Returns status & severity breakdown counts for UI dashboard badges."""
    issues = db.query(Issue).filter(Issue.project_id == project_id).all()
    
    total = len(issues)
    open_count = sum(1 for i in issues if i.status == "OPEN")
    accepted_count = sum(1 for i in issues if i.status == "ACCEPTED")
    resolved_count = sum(1 for i in issues if i.status == "RESOLVED")
    ignored_count = sum(1 for i in issues if i.status == "IGNORED")

    errors_count = sum(1 for i in issues if i.severity == "ERROR")
    warnings_count = sum(1 for i in issues if i.severity == "WARNING")
    info_count = sum(1 for i in issues if i.severity == "INFO")

    return IssueSummaryResponse(
        total=total,
        open=open_count,
        accepted=accepted_count,
        resolved=resolved_count,
        ignored=ignored_count,
        errors=errors_count,
        warnings=warnings_count,
        info=info_count
    )
