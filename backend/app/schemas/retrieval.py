from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class RetrievedItem(BaseModel):
    item_type: str = Field(..., description="FACT | EVENT | RELATIONSHIP | KNOWLEDGE | WRITER_DECISION | RESEARCH | SCENE")
    source_id: str
    scene_id: Optional[str] = None
    scene_number: Optional[int] = None
    title: str
    content: str
    provenance_tag: str
    relevance_score: float = Field(default=1.0)
    retrieval_reason: str = Field(default="entity_match")
    raw_metadata: Dict[str, Any] = Field(default_factory=dict)

class RetrievalRequest(BaseModel):
    scene_id: str
    task_type: str = Field(default="CONTINUITY", description="CONTINUITY | KNOWLEDGE | OBJECT | LOCATION | REALITY")
    entity_names: List[str] = Field(default_factory=list)
    query_text: Optional[str] = None

class RetrievalResponse(BaseModel):
    project_id: str
    scene_id: str
    scene_number: Optional[int] = None
    task_type: str
    total_retrieved: int
    items: List[RetrievedItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
