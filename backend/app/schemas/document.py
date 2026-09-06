from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class ParsedSceneResponse(BaseModel):
    temporary_id: str
    scene_number: int
    heading: str
    raw_text: str
    source_page_start: Optional[int] = None
    source_page_end: Optional[int] = None
    confidence: float = 1.0

class ImportPreviewResponse(BaseModel):
    document_id: str
    filename: str
    file_type: str
    file_size: int
    status: str
    page_count: Optional[int] = None
    character_count: int
    scene_count: int
    scenes: List[ParsedSceneResponse]
    warnings: List[str] = Field(default_factory=list)
    existing_scenes_count: int = 0

class ConfirmImportRequest(BaseModel):
    mode: str = Field(default="append", description="Import mode: 'append' or 'replace'")

class ImportedDocumentResponse(BaseModel):
    id: str
    project_id: str
    filename: str
    file_type: str
    file_size: int
    status: str
    parser_version: str
    scene_detection_version: str
    error_message: Optional[str] = None
    page_count: Optional[int] = None
    character_count: Optional[int] = None
    scene_count: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
