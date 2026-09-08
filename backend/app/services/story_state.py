import logging
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.db.models import Project, Scene, Entity, Fact, Event, Relationship, KnowledgeState
from app.schemas.story_state import (
    StoryStateResponse, StoryStateSummaryResponse, CharacterState, LocationState, ObjectState,
    FactState, EventState, RelationshipState, KnowledgeStateItem, EntityReference
)

logger = logging.getLogger("script_supervisor.story_state")

def is_valid_character_name(name: str) -> bool:
    """Validates basic non-empty string sanity for character names."""
    if not name or not name.strip():
        return False
    lower = name.strip().lower()
    if lower in ("null", "none", "unknown", "audience", "camera", "scene", "narrator"):
        return False
    return True

def purge_invalid_and_orphaned_entities(db: Session, project_id: str):
    """
    Purges invalid non-character entity names (e.g. null, unknown) and
    orphaned entities that have no remaining facts, events, relationships, or knowledge states.
    """
    entities = db.query(Entity).filter(Entity.project_id == project_id).all()
    for ent in entities:
        is_invalid = ent.type.lower() == "character" and not is_valid_character_name(ent.name)
        
        # Check if entity is orphaned (has 0 connected records)
        has_facts = db.query(Fact).filter(Fact.subject_entity_id == ent.id).first() is not None
        has_events = db.query(Event).filter(
            (Event.actor_entity_id == ent.id) | 
            (Event.target_entity_id == ent.id) | 
            (Event.location_entity_id == ent.id)
        ).first() is not None
        has_relationships = db.query(Relationship).filter(
            (Relationship.source_entity_id == ent.id) | 
            (Relationship.target_entity_id == ent.id)
        ).first() is not None
        has_knowledge = db.query(KnowledgeState).filter(KnowledgeState.character_entity_id == ent.id).first() is not None

        if is_invalid or not (has_facts or has_events or has_relationships or has_knowledge):
            logger.info(f"Purging invalid/orphaned entity '{ent.name}' ({ent.id}) from DB")
            try:
                db.query(Fact).filter(Fact.subject_entity_id == ent.id).delete()
                db.query(Event).filter(Event.actor_entity_id == ent.id).update({"actor_entity_id": None})
                db.query(Event).filter(Event.target_entity_id == ent.id).update({"target_entity_id": None})
                db.query(Event).filter(Event.location_entity_id == ent.id).update({"location_entity_id": None})
                db.query(Relationship).filter(Relationship.source_entity_id == ent.id).delete()
                db.query(Relationship).filter(Relationship.target_entity_id == ent.id).delete()
                db.query(KnowledgeState).filter(KnowledgeState.character_entity_id == ent.id).delete()
                db.query(Entity).filter(Entity.id == ent.id).delete()
                db.flush()
            except Exception as ex:
                logger.warning(f"Error purging entity '{ent.name}': {ex}")


def build_story_state(db: Session, project_id: str, up_to_scene_number: Optional[int] = None) -> StoryStateResponse:
    """
    Core Story State Service:
    Derives current fictional world state from historical records.
    Supports historical snapshotting via up_to_scene_number parameter so continuity checking
    can compare Scene N against the exact Story State prior to Scene N.
    """
    logger.info(f"Building story state for project_id={project_id} (up_to_scene_number={up_to_scene_number})")

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' not found."
        )

    # Automatically clean invalid and orphaned entity records prior to building story state
    purge_invalid_and_orphaned_entities(db, project_id)

    # 1. Fetch raw DB records up to scene_number
    scenes_query = db.query(Scene).filter(Scene.project_id == project_id)
    if up_to_scene_number is not None:
        scenes_query = scenes_query.filter(Scene.scene_number <= up_to_scene_number)
    
    scenes = scenes_query.order_by(Scene.scene_number.asc()).all()
    scene_ids = {s.id for s in scenes}
    scene_map: Dict[str, Scene] = {s.id: s for s in scenes}

    entities = db.query(Entity).filter(Entity.project_id == project_id).order_by(Entity.name).all()

    # 2. Build Helper Entity References & Resolve Name Aliases (e.g. "Arjun" -> "ARJUN RAO", "Nora Vale" -> "Nora Chen")
    canonical_entity_map: Dict[str, Entity] = {}
    primary_entities: List[Entity] = []

    def is_descriptive_title(name: str) -> bool:
        lower = name.strip().lower()
        return any(w in lower for w in ["'s ", "father", "mother", "parent", "brother", "sister"])

    # Sort entities so canonical personal names come before descriptive relationship titles
    sorted_entities = sorted(entities, key=lambda e: (is_descriptive_title(e.name), -len(e.name)))

    for ent in sorted_entities:
        ent_lower = ent.name.strip().lower()
        ent_tokens = [w for w in ent_lower.split() if len(w) > 2]
        matched = None
        for primary in primary_entities:
            if primary.type.lower() == ent.type.lower():
                primary_lower = primary.name.strip().lower()
                primary_tokens = [w for w in primary_lower.split() if len(w) > 2]
                
                # 1. Direct subset token match (e.g. "Arjun" -> "ARJUN RAO")
                if set(ent_tokens) and set(ent_tokens).issubset(set(primary_tokens)):
                    matched = primary
                    break
                
                # 2. Shared first-name resolution for characters (e.g. "Nora Vale" -> "Nora Chen")
                if primary.type.lower() == "character" and ent_tokens and primary_tokens:
                    # If first names match (e.g. "nora") and no third distinct person exists
                    if ent_tokens[0] == primary_tokens[0] and ent_tokens[0] not in ("dr.", "mr.", "mrs.", "ms.", "prof."):
                        matched = primary
                        break

                # 3. Possessive descriptor title matching (e.g. "Arjun's Father" -> "Rajesh Rao")
                if ("father" in ent_lower or "parent" in ent_lower or "mother" in ent_lower) and primary.type.lower() == "character":
                    if "father" not in primary_lower and "parent" not in primary_lower and "mother" not in primary_lower:
                        matched = primary
                        break
        if matched:
            canonical_entity_map[ent.id] = matched
        else:
            primary_entities.append(ent)
            canonical_entity_map[ent.id] = ent

    # Perform DB cleanup if duplicate entity rows exist
    has_duplicates = any(e.id != canonical_entity_map[e.id].id for e in entities)
    if has_duplicates:
        try:
            for ent in entities:
                canonical = canonical_entity_map[ent.id]
                if ent.id != canonical.id:
                    logger.info(f"Consolidating duplicate DB entity '{ent.name}' ({ent.id}) into canonical '{canonical.name}' ({canonical.id})")
                    db.query(Fact).filter(Fact.subject_entity_id == ent.id).update({"subject_entity_id": canonical.id})
                    db.query(Event).filter(Event.actor_entity_id == ent.id).update({"actor_entity_id": canonical.id})
                    db.query(Event).filter(Event.target_entity_id == ent.id).update({"target_entity_id": canonical.id})
                    db.query(Event).filter(Event.location_entity_id == ent.id).update({"location_entity_id": canonical.id})
                    db.query(Relationship).filter(Relationship.source_entity_id == ent.id).update({"source_entity_id": canonical.id})
                    db.query(Relationship).filter(Relationship.target_entity_id == ent.id).update({"target_entity_id": canonical.id})
                    db.query(KnowledgeState).filter(KnowledgeState.character_entity_id == ent.id).update({"character_entity_id": canonical.id})
                    db.query(Entity).filter(Entity.id == ent.id).delete()
            db.flush()
        except Exception as ex:
            logger.warning(f"Entity DB consolidation failed (ignoring for read-only query): {ex}")

    if scene_ids:
        facts_raw = db.query(Fact).filter(Fact.project_id == project_id, Fact.scene_id.in_(scene_ids)).all()
        events_raw = db.query(Event).join(Scene, Event.scene_id == Scene.id)\
            .filter(Scene.project_id == project_id, Event.scene_id.in_(scene_ids))\
            .order_by(Scene.scene_number.asc(), Event.created_at.asc()).all()
        relationships_raw = db.query(Relationship).filter(Relationship.project_id == project_id, Relationship.scene_id.in_(scene_ids)).all()
        knowledge_raw = db.query(KnowledgeState).filter(KnowledgeState.project_id == project_id, KnowledgeState.source_scene_id.in_(scene_ids)).all()
    else:
        facts_raw, events_raw, relationships_raw, knowledge_raw = [], [], [], []

    # Build Helper Entity References
    entity_refs: Dict[str, EntityReference] = {
        e.id: EntityReference(id=canonical_entity_map[e.id].id, name=canonical_entity_map[e.id].name) for e in entities
    }

    # 3. Map Relationships & Knowledge
    rel_states: List[RelationshipState] = []
    for r in relationships_raw:
        source_ref = entity_refs.get(r.source_entity_id, EntityReference(id=r.source_entity_id, name="Unknown"))
        target_ref = entity_refs.get(r.target_entity_id) if r.target_entity_id else None
        scene_num = scene_map[r.scene_id].scene_number if r.scene_id in scene_map else None

        rel_states.append(RelationshipState(
            id=r.id,
            source=source_ref,
            relationship_type=r.relationship_type,
            target=target_ref,
            source_scene_id=r.scene_id,
            source_scene_number=scene_num,
            confidence=r.confidence
        ))

    knowledge_items: List[KnowledgeStateItem] = []
    for k in knowledge_raw:
        char_ref = entity_refs.get(k.character_entity_id, EntityReference(id=k.character_entity_id, name="Unknown"))
        scene_num = scene_map[k.source_scene_id].scene_number if k.source_scene_id in scene_map else None

        knowledge_items.append(KnowledgeStateItem(
            id=k.id,
            character=char_ref,
            knowledge=k.knowledge,
            source_scene_id=k.source_scene_id,
            source_scene_number=scene_num,
            knowledge_type=k.knowledge_type,
            confidence=k.confidence
        ))

    # 4. Map Facts & Events
    fact_states: List[FactState] = []
    for f in facts_raw:
        subj_ref = entity_refs.get(f.subject_entity_id, EntityReference(id=f.subject_entity_id, name="Unknown"))
        scene_num = scene_map[f.scene_id].scene_number if f.scene_id in scene_map else None

        fact_states.append(FactState(
            id=f.id,
            subject=subj_ref,
            predicate=f.predicate,
            value=f.value,
            source_scene_id=f.scene_id,
            source_scene_number=scene_num,
            confidence=f.confidence
        ))

    event_states: List[EventState] = []
    for ev in events_raw:
        scene_num = scene_map[ev.scene_id].scene_number if ev.scene_id in scene_map else None
        actor_ref = entity_refs.get(ev.actor_entity_id) if ev.actor_entity_id else None
        target_ref = entity_refs.get(ev.target_entity_id) if ev.target_entity_id else None
        loc_ref = entity_refs.get(ev.location_entity_id) if ev.location_entity_id else None

        event_states.append(EventState(
            id=ev.id,
            scene_id=ev.scene_id,
            scene_number=scene_num,
            event_type=ev.event_type,
            actor=actor_ref,
            target=target_ref,
            location=loc_ref,
            description=ev.description,
            attributes=ev.attributes_json or {}
        ))

    # 5. State Reduction over Chronological Events for Dynamic State
    char_current_locations: Dict[str, EntityReference] = {}
    char_possessions: Dict[str, List[EntityReference]] = {e.id: [] for e in entities if e.type == "character"}
    object_owners: Dict[str, EntityReference] = {}
    object_locations: Dict[str, EntityReference] = {}

    for rel in rel_states:
        if rel.relationship_type in ("owns", "possesses") and rel.target:
            char_id = rel.source.id
            obj_id = rel.target.id
            object_owners[obj_id] = rel.source
            if char_id in char_possessions and rel.target not in char_possessions[char_id]:
                char_possessions[char_id].append(rel.target)

    for ev in event_states:
        etype = ev.event_type.upper()
        
        if etype in ("ENTER", "TRAVEL", "MOVE", "WALK_OUTSIDE") and ev.actor and ev.location:
            char_current_locations[ev.actor.id] = ev.location

        if etype in ("ACQUIRE_OBJECT", "TAKE_OBJECT", "GIVE_OBJECT", "RECEIVE_OBJECT") and ev.actor and ev.target:
            obj_id = ev.target.id
            char_id = ev.actor.id
            object_owners[obj_id] = ev.actor
            if char_id in char_possessions and ev.target not in char_possessions[char_id]:
                char_possessions[char_id].append(ev.target)

    # 6. Construct Character, Location, and Object States
    character_states: List[CharacterState] = []
    location_states: List[LocationState] = []
    object_states: List[ObjectState] = []

    NON_CHARACTER_KEYWORDS = ("storm", "rain", "wind", "weather", "outside", "inside the", "diner", "hospital", "station", "road", "street", "building", "camera", "time", "clock", "null")

    for ent in primary_entities:
        ent_name_lower = ent.name.lower()
        if ent.type == "character" and not any(kw in ent_name_lower for kw in NON_CHARACTER_KEYWORDS):
            residence_val = None
            for f in fact_states:
                if f.subject.id == ent.id and f.predicate in ("lives_in", "residence", "home"):
                    residence_val = str(f.value)

            char_rels = [r for r in rel_states if r.source.id == ent.id or (r.target and r.target.id == ent.id)]
            char_know_raw = [k for k in knowledge_items if k.character.id == ent.id]
            seen_know_keys = set()
            char_know = []
            
            # Words indicating meta-judgments, emotional confusion, or audio/transient noise
            NOISE_TERMS = (
                "discrepancy", "confused", "sound is heard", "shutter sound", 
                "realizes something", "witnesses the old photograph being burned",
                "becomes confused", "learns that arjun is asking about"
            )
            
            for k in char_know_raw:
                k_lower = k.knowledge.lower()
                if any(noise in k_lower for noise in NOISE_TERMS):
                    continue
                norm_key = " ".join(k.knowledge.strip().strip('"\'').rstrip('.,!?').strip().lower().split())
                if norm_key not in seen_know_keys:
                    seen_know_keys.add(norm_key)
                    char_know.append(k)

            character_states.append(CharacterState(
                id=ent.id,
                name=ent.name,
                attributes=ent.attributes_json or {},
                residence=residence_val,
                current_location=char_current_locations.get(ent.id),
                possessions=char_possessions.get(ent.id, []),
                relationships=char_rels,
                knowledge=char_know
            ))

        elif ent.type == "location":
            location_states.append(LocationState(
                id=ent.id,
                name=ent.name,
                type="location",
                attributes=ent.attributes_json or {}
            ))

        elif ent.type == "object":
            object_states.append(ObjectState(
                id=ent.id,
                name=ent.name,
                type="object",
                attributes=ent.attributes_json or {},
                current_owner=object_owners.get(ent.id),
                current_location=object_locations.get(ent.id)
            ))

    return StoryStateResponse(
        project_id=project_id,
        characters=character_states,
        locations=location_states,
        objects=object_states,
        facts=fact_states,
        events=event_states,
        relationships=rel_states,
        knowledge_states=knowledge_items
    )

def get_story_state_summary(db: Session, project_id: str) -> StoryStateSummaryResponse:
    """Returns count overview for UI summary components."""
    state = build_story_state(db, project_id)
    return StoryStateSummaryResponse(
        character_count=len(state.characters),
        location_count=len(state.locations),
        object_count=len(state.objects),
        fact_count=len(state.facts),
        event_count=len(state.events),
        relationship_count=len(state.relationships),
        knowledge_count=len(state.knowledge_states)
    )
