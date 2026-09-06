from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, model_validator

class ClaimExtraction(BaseModel):
    claim_text: str = Field(default="", description="Sentence or assertion from screenplay")
    claim_type: str = Field(default="REAL_WORLD_CLAIM", description="STORY_FACT | REAL_WORLD_CLAIM | FICTIONAL_WORLD_RULE")
    subject: Optional[str] = None
    predicate: Optional[str] = None
    object: Optional[str] = None
    temporal_context: Optional[str] = None
    location_context: Optional[str] = None
    requires_research: bool = Field(default=False)
    research_priority: str = Field(default="MEDIUM", description="HIGH | MEDIUM | LOW")

    @model_validator(mode='before')
    @classmethod
    def normalize_keys(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Normalize claim_text aliases
            text_val = data.get('claim_text') or data.get('text') or data.get('claim') or data.get('statement') or ""
            data['claim_text'] = str(text_val)

            # Normalize claim_type aliases
            type_val = data.get('claim_type') or data.get('type') or data.get('category') or "REAL_WORLD_CLAIM"
            norm_type = str(type_val).upper().replace(' ', '_')
            if norm_type not in ("STORY_FACT", "REAL_WORLD_CLAIM", "FICTIONAL_WORLD_RULE"):
                norm_type = "REAL_WORLD_CLAIM" if "REAL" in norm_type else "STORY_FACT"
            data['claim_type'] = norm_type

            # Normalize requires_research boolean
            req_val = data.get('requires_research')
            if req_val is None:
                data['requires_research'] = (data['claim_type'] == "REAL_WORLD_CLAIM")
        return data

class ClaimResponse(BaseModel):
    id: str
    project_id: str
    scene_id: str
    scene_number: Optional[int] = None
    claim_text: str
    claim_type: str
    subject: Optional[str] = None
    predicate: Optional[str] = None
    object: Optional[str] = None
    temporal_context: Optional[str] = None
    location_context: Optional[str] = None
    requires_research: bool
    research_priority: str
    status: str
    claim_fingerprint: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
