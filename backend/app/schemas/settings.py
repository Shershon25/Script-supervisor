from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

class StoryWorldRuleCreate(BaseModel):
    rule_text: str = Field(..., min_length=1, description="Text of the world rule")
    active: bool = True

class StoryWorldRuleUpdate(BaseModel):
    rule_text: Optional[str] = Field(None, min_length=1)
    active: Optional[bool] = None

class StoryWorldRuleResponse(BaseModel):
    id: str
    project_id: str
    rule_text: str
    active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ProjectSettingsUpdate(BaseModel):
    reality_level: Optional[int] = Field(None, ge=0, le=10, description="Reality checking strictness 0-10")
    continuity_strictness: Optional[int] = Field(None, ge=0, le=10, description="Continuity evaluation strictness 0-10")
    auto_background_analysis_enabled: Optional[bool] = Field(None, description="Automatically evaluate previous scene when adding a new scene")

class ProjectSettingsResponse(BaseModel):
    id: str
    project_id: str
    reality_level: int = Field(..., ge=0, le=10)
    continuity_strictness: int = Field(..., ge=0, le=10)
    auto_background_analysis_enabled: bool = True
    settings_version: int
    world_rules: List[StoryWorldRuleResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
