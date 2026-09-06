from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class EntityReference(BaseModel):
    id: str
    name: str

class RelationshipState(BaseModel):
    id: str
    source: EntityReference
    relationship_type: str
    target: Optional[EntityReference] = None
    source_scene_id: str
    source_scene_number: Optional[int] = None
    confidence: float = 1.0

class KnowledgeStateItem(BaseModel):
    id: str
    character: EntityReference
    knowledge: str
    source_scene_id: str
    source_scene_number: Optional[int] = None
    knowledge_type: str = "explicitly_established"
    confidence: float = 1.0

class CharacterState(BaseModel):
    id: str
    name: str
    attributes: Dict[str, Any] = {}
    residence: Optional[str] = None
    current_location: Optional[EntityReference] = None
    possessions: List[EntityReference] = []
    relationships: List[RelationshipState] = []
    knowledge: List[KnowledgeStateItem] = []

class LocationState(BaseModel):
    id: str
    name: str
    type: Optional[str] = "location"
    attributes: Dict[str, Any] = {}

class ObjectState(BaseModel):
    id: str
    name: str
    type: Optional[str] = "object"
    attributes: Dict[str, Any] = {}
    current_owner: Optional[EntityReference] = None
    current_location: Optional[EntityReference] = None

class FactState(BaseModel):
    id: str
    subject: EntityReference
    predicate: str
    value: Any
    source_scene_id: str
    source_scene_number: Optional[int] = None
    confidence: float = 1.0

class EventState(BaseModel):
    id: str
    scene_id: str
    scene_number: Optional[int] = None
    event_type: str
    actor: Optional[EntityReference] = None
    target: Optional[EntityReference] = None
    location: Optional[EntityReference] = None
    description: str
    attributes: Dict[str, Any] = {}

class StoryStateResponse(BaseModel):
    project_id: str
    characters: List[CharacterState] = []
    locations: List[LocationState] = []
    objects: List[ObjectState] = []
    facts: List[FactState] = []
    events: List[EventState] = []
    relationships: List[RelationshipState] = []
    knowledge_states: List[KnowledgeStateItem] = []

class StoryStateSummaryResponse(BaseModel):
    character_count: int
    location_count: int
    object_count: int
    fact_count: int
    event_count: int
    relationship_count: int
    knowledge_count: int
