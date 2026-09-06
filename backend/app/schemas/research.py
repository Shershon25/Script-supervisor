from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.claim import ClaimResponse

class ResearchSourceResponse(BaseModel):
    id: str
    research_task_id: str
    title: str
    url: str
    domain: str
    excerpt: str
    relevance_score: float
    retrieved_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ResearchEvaluationResponse(BaseModel):
    id: str
    research_task_id: str
    claim_id: str
    verdict: str  # VERIFIED | LIKELY_TRUE | CONTRADICTED | INCONCLUSIVE | INSUFFICIENT_EVIDENCE
    confidence: float
    summary: str
    reasoning: str
    supporting_source_ids: List[str] = Field(default_factory=list)
    contradicting_source_ids: List[str] = Field(default_factory=list)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ResearchTaskResponse(BaseModel):
    id: str
    project_id: str
    scene_id: str
    claim_id: str
    objective: str
    status: str  # PENDING | RUNNING | COMPLETED | FAILED | CANCELLED
    provider: str
    requested_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    claim: Optional[ClaimResponse] = None
    sources: List[ResearchSourceResponse] = Field(default_factory=list)
    evaluation: Optional[ResearchEvaluationResponse] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
