from typing import Optional, List
from pydantic import BaseModel, Field

class PlotEventItem(BaseModel):
    event_id: str = Field(..., description="Unique event identifier e.g. scene_3_event_1")
    scene_number: int = Field(..., description="Screenplay scene number")
    title: str = Field(..., description="Short descriptive event title")
    description: str = Field(..., description="What materially happens and why it advances the story")
    track_type: str = Field(..., description="MAIN_PLOT | SUBPLOT")
    track_name: str = Field(..., description="Stable descriptive track name e.g. Core Mystery, Maya's Hidden Agenda")
    importance_score: str = Field(..., description="CRITICAL | HIGH | MEDIUM")
    excerpt: str = Field(..., description="Exact contiguous screenplay text demonstrating the event")
    connected_to_event: Optional[str] = Field(None, description="event_id of target event or null")
    connection_type: Optional[str] = Field(None, description="TRIGGERS | CONVERGES_WITH | REVEALS | CONTRADICTS | null")

class PlotTimelineResponse(BaseModel):
    plot_events: List[PlotEventItem]

class TimelineViewResponse(BaseModel):
    project_id: str
    events: List[PlotEventItem]
    tracks: List[str]
