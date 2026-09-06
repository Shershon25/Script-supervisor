from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class AnalysisRunSummary(BaseModel):
    entities_count: int = 0
    facts_count: int = 0
    events_count: int = 0
    issues_count: int = 0
    claims_count: int = 0
    research_reused_count: int = 0

class UnifiedAnalysisResponse(BaseModel):
    run_id: str
    project_id: str
    scene_id: str
    scene_number: int
    status: str  # IDLE | ANALYZING | COMPLETED | PARTIAL | FAILED
    summary: AnalysisRunSummary
    entities_detected: List[str] = []
    issues_created: int = 0
    research_tasks_created: int = 0
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: datetime
