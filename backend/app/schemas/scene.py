from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class SceneCreate(BaseModel):
    scene_number: int = Field(..., gt=0, description="Scene number must be greater than 0")
    raw_text: str = Field(..., min_length=0, description="Raw screenplay text (may be empty for new blank scenes)")

class SceneUpdate(BaseModel):
    raw_text: str = Field(..., min_length=1, description="Raw screenplay text cannot be empty")

class SceneResponse(BaseModel):
    id: str
    project_id: str
    scene_number: int
    raw_text: str
    source_document_id: Optional[str] = None
    source_page_start: Optional[int] = None
    source_page_end: Optional[int] = None
    source_type: str = "MANUAL"
    is_analyzed: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
