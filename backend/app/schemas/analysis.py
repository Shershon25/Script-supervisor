from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

# --- Gemini Structured Extraction Sub-Models ---

class AttributePair(BaseModel):
    key: str = Field(..., description="Attribute name e.g. occupation, age")
    value: str = Field(..., description="Attribute value e.g. doctor, 35")

class EntityExtraction(BaseModel):
    type: str = Field(..., description="Type of entity: character | location | object | organization")
    name: str = Field(..., description="Name or canonical title of the entity")
    attributes: List[AttributePair] = Field(default_factory=list, description="Key-value attribute pairs")

class FactExtraction(BaseModel):
    subject: str = Field(..., description="Name of the subject entity")
    predicate: str = Field(..., description="Relationship or attribute predicate, e.g. lives_in, status")
    value: str = Field(..., description="Value of the predicate, e.g. Chennai, deceased")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score 0.0 to 1.0")

class EventExtraction(BaseModel):
    event_type: str = Field(..., description="Action category, e.g. ENTER, LEAVE, TRAVEL, TAKE_OBJECT, ACQUIRE_OBJECT, LOSE_OBJECT, GIVE_OBJECT, RECEIVE_OBJECT, MEET")
    actor: Optional[str] = Field(default=None, description="Entity name performing action")
    target: Optional[str] = Field(default=None, description="Entity name receiving action or object")
    location: Optional[str] = Field(default=None, description="Location entity name where action happens")
    description: str = Field(..., description="Clear summary of what occurs")

class KnowledgeChangeExtraction(BaseModel):
    character: str = Field(..., description="Character entity name")
    knowledge: str = Field(..., description="What the character discovered, learned, or knows")
    knowledge_type: str = Field(default="explicitly_established", description="explicitly_established | witnessed | told_by_character | inferred | unknown")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

class RelationshipExtraction(BaseModel):
    source: str = Field(..., description="Source entity name")
    relationship_type: str = Field(..., description="Relationship type e.g. owns, possesses, brother_of, sister_of, parent_of, child_of, spouse_of, friend_of, works_for, knows, located_at, contains")
    target: Optional[str] = Field(default=None, description="Target entity name")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

class ClaimExtraction(BaseModel):
    claim: str = Field(..., description="Factual claim made that may require research")
    stated_by: Optional[str] = Field(default=None, description="Character making the claim")

class SceneAnalysisResponse(BaseModel):
    scene_summary: str = Field(..., description="Concise overview of the screenplay scene")
    entities: List[EntityExtraction] = Field(default_factory=list)
    facts: List[FactExtraction] = Field(default_factory=list)
    events: List[EventExtraction] = Field(default_factory=list)
    relationships: List[RelationshipExtraction] = Field(default_factory=list)
    knowledge_changes: List[KnowledgeChangeExtraction] = Field(default_factory=list)
    claims: List[ClaimExtraction] = Field(default_factory=list)


# --- Persisted DB Models API Responses ---

class EntityResponse(BaseModel):
    id: str
    project_id: str
    type: str
    name: str
    attributes_json: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class FactResponse(BaseModel):
    id: str
    project_id: str
    subject_entity_id: str
    subject_entity_name: Optional[str] = None
    predicate: str
    value: str
    scene_id: str
    scene_number: Optional[int] = None
    confidence: float
    source_type: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class EventResponse(BaseModel):
    id: str
    scene_id: str
    scene_number: Optional[int] = None
    event_type: str
    actor_entity_id: Optional[str] = None
    actor_name: Optional[str] = None
    target_entity_id: Optional[str] = None
    target_name: Optional[str] = None
    location_entity_id: Optional[str] = None
    location_name: Optional[str] = None
    description: str
    attributes_json: Dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class RelationshipResponse(BaseModel):
    id: str
    project_id: str
    source_entity_id: str
    source_entity_name: Optional[str] = None
    relationship_type: str
    target_entity_id: Optional[str] = None
    target_entity_name: Optional[str] = None
    scene_id: str
    scene_number: Optional[int] = None
    confidence: float
    source_type: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class KnowledgeStateResponse(BaseModel):
    id: str
    project_id: str
    character_entity_id: str
    character_name: Optional[str] = None
    knowledge: str
    source_scene_id: str
    source_scene_number: Optional[int] = None
    knowledge_type: str
    confidence: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class StoryDataResponse(BaseModel):
    entities: List[EntityResponse]
    facts: List[FactResponse]
    events: List[EventResponse]

class AnalyzeSceneResult(BaseModel):
    scene: Dict[str, Any]
    analysis: SceneAnalysisResponse
    story_state: Optional[Dict[str, Any]] = None
    issues: List[Dict[str, Any]] = Field(default_factory=list)
