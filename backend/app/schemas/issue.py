from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.issue_review import IssueReviewResponse

class IssueEvidence(BaseModel):
    scene_id: str
    scene_number: Optional[int] = None
    type: str  # ESTABLISHED_FACT | CONFLICTING_FACT | PREVIOUS_LOCATION | CURRENT_LOCATION | PREVIOUS_OWNER | NEW_OWNER | MISSING_KNOWLEDGE
    text: str

class IssueResponse(BaseModel):
    id: str
    project_id: str
    scene_id: str
    scene_number: Optional[int] = None
    issue_type: str
    severity: str
    title: str
    description: str
    confidence: float
    status: str
    evidence: List[IssueEvidence] = Field(default_factory=list)
    
    # Day 4 Human Review Fields
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    resolution_type: Optional[str] = None
    resolution_note: Optional[str] = None
    issue_fingerprint: Optional[str] = None
    reviews: List[IssueReviewResponse] = Field(default_factory=list)

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ContinuityCandidate(BaseModel):
    id: str
    issue_type: str
    entity_name: str
    current_scene_id: str
    current_scene_number: int
    current_text: str
    previous_scene_id: str
    previous_scene_number: int
    previous_text: str
    reason: str

class GeminiCandidateEvaluation(BaseModel):
    candidate_id: str = Field(..., description="ID matching candidate evaluation")
    classification: str = Field(..., description="CONFLICT | NO_CONFLICT | AMBIGUOUS")
    severity: str = Field(default="WARNING", description="INFO | WARNING | ERROR")
    confidence: float = Field(default=0.90, ge=0.0, le=1.0)
    title: str = Field(..., description="Short clear headline of the issue")
    description: str = Field(..., description="Detailed explainable description citing evidence")
    reasoning: str = Field(..., description="Why this constitutes a conflict or deliberate change")

class GeminiContinuityResponse(BaseModel):
    evaluations: List[GeminiCandidateEvaluation] = Field(default_factory=list)
