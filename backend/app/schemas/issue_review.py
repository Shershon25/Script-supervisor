from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class IssueReviewCreate(BaseModel):
    action: str = Field(..., description="Action to perform: ACCEPT | IGNORE | RESOLVE | REOPEN")
    resolution_type: Optional[str] = Field(default=None, description="Resolution category: INTENTIONAL | FIXED | FALSE_POSITIVE | ACCEPTED_AS_IS | NEEDS_REVIEW")
    note: Optional[str] = Field(default=None, description="Writer explanation or review note")

class IssueReviewResponse(BaseModel):
    id: str
    issue_id: str
    project_id: str
    action: str
    note: Optional[str] = None
    previous_status: str
    new_status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class IssueSummaryResponse(BaseModel):
    total: int
    open: int
    accepted: int
    resolved: int
    ignored: int
    errors: int
    warnings: int
    info: int
