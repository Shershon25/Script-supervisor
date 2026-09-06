from datetime import datetime
from pydantic import BaseModel, ConfigDict

class ProjectCreate(BaseModel):
    title: str

class ProjectUpdate(BaseModel):
    title: str

class ProjectResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
