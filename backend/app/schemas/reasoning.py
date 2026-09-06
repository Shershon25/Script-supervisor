from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.retrieval import RetrievedItem

class ReasoningRequest(BaseModel):
    scene_id: str
    task_type: str = Field(default="CONTINUITY", description="CONTINUITY | KNOWLEDGE | OBJECT | LOCATION | REALITY")
    question: Optional[str] = None
    target_entity_names: List[str] = Field(default_factory=list)

class ReasoningResult(BaseModel):
    task_type: str
    scene_id: str
    conclusion: str
    verdict: str = Field(default="NO_CONFLICT", description="NO_CONFLICT | CONFLICT | AMBIGUOUS | VERIFIED | CONTRADICTED")
    confidence: float = Field(default=0.90)
    summary: str
    reasoning_summary: str
    evidence_items: List[RetrievedItem] = Field(default_factory=list)
    writer_decision_context: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
