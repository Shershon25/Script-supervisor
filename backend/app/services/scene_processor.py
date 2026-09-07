import logging
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.db.models import Project, Scene, Entity, Fact, Event, Relationship, KnowledgeState
from app.services.gemini import analyze_scene
from app.services.story_state import build_story_state
from app.services.continuity import check_scene_continuity
from app.schemas.analysis import SceneAnalysisResponse

logger = logging.getLogger("script_supervisor.scene_processor")

def normalize_name(name: str) -> str:
    """Returns normalized name string for entity matching."""
    return name.strip().lower()

def resolve_or_create_entity(
    db: Session,
    project_id: str,
    entity_type: str,
    raw_name: str,
    entity_name_map: Dict[str, Entity]
) -> Optional[Entity]:
    """Resolves an extracted entity name to an existing database Entity (matching full name / first name / canonical aliases) or creates a new Entity."""
    if not raw_name or not raw_name.strip():
        return None

    clean_name = raw_name.strip().strip("'\".").strip()
    norm_input = clean_name.lower()

    # 1. Direct exact match
    if norm_input in entity_name_map:
        return entity_name_map[norm_input]

    input_tokens = set(norm_input.split())
    if not input_tokens:
        return None

    # 2. Token / Name subset matching against existing entities of same type
    best_match: Optional[Entity] = None
    for norm_existing, ent in list(entity_name_map.items()):
        if ent.type.lower() != entity_type.lower():
            continue

        existing_tokens = set(norm_existing.split())
        
        # Input is first/last name subset of existing full name (e.g. input="Arjun", existing="ARJUN RAO")
        if input_tokens.issubset(existing_tokens):
            best_match = ent
            break

        # Existing is first/last name subset of input full name (e.g. existing="Arjun", input="ARJUN RAO")
        if existing_tokens.issubset(input_tokens):
            logger.info(f"Upgrading entity {ent.id} name from '{ent.name}' to full name '{clean_name}'")
            ent.name = clean_name
            db.flush()
            best_match = ent
            break

    if best_match:
        entity_name_map[norm_input] = best_match
        entity_name_map[best_match.name.lower()] = best_match
        return best_match

    # 3. Create new entity if no match found
    entity_obj = Entity(
        project_id=project_id,
        type=entity_type.lower(),
        name=clean_name,
        attributes_json={}
    )
    db.add(entity_obj)
    db.flush()
    entity_name_map[norm_input] = entity_obj
    entity_name_map[clean_name.lower()] = entity_obj
    return entity_obj

def process_scene(db: Session, project_id: str, scene_number: int, raw_text: str):
    """
    Core scene processing service:
    1. Validates project
    2. Persists scene
    3. Analyzes screenplay with Gemini
    4. Resolves & deduplicates entities
    5. Persists facts & events
    6. Persists relationships & knowledge states
    7. Builds Story State
    8. Runs non-blocking Continuity Detection Engine
    9. Returns scene, analysis, story_state, and issues.
    """
    logger.info(f"Processing scene #{scene_number} for project_id={project_id}")

    # 1. Validate project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found."
        )

    # 2. Handle existing scene vs new scene
    existing_scene = db.query(Scene).filter(
        Scene.project_id == project_id,
        Scene.scene_number == scene_number
    ).first()

    try:
        if existing_scene:
            scene = existing_scene
            scene.raw_text = raw_text
        else:
            scene = Scene(
                project_id=project_id,
                scene_number=scene_number,
                raw_text=raw_text
            )
            db.add(scene)
        db.flush()

        # 3. Analyze scene with Gemini
        logger.info(f"Sending scene #{scene_number} to Gemini service...")
        analysis: SceneAnalysisResponse = analyze_scene(raw_text)

        # 4. Entity Resolution & Persistence
        entity_name_map = {}
        existing_entities = db.query(Entity).filter(Entity.project_id == project_id).all()
        for ent in existing_entities:
            entity_name_map[normalize_name(ent.name)] = ent

        persisted_entities = []
        for extracted_ent in analysis.entities:
            entity_obj = resolve_or_create_entity(db, project_id, extracted_ent.type, extracted_ent.name, entity_name_map)
            if entity_obj and entity_obj not in persisted_entities:
                persisted_entities.append(entity_obj)

        # 5. Fact Persistence
        persisted_facts = []
        for extracted_fact in analysis.facts:
            # Infer entity type rather than hardcoding "character"
            norm_subj = normalize_name(extracted_fact.subject)
            inferred_type = "character"
            if norm_subj in entity_name_map:
                inferred_type = entity_name_map[norm_subj].type
            else:
                matched_ent = next((e for e in analysis.entities if normalize_name(e.name) == norm_subj), None)
                if matched_ent:
                    inferred_type = matched_ent.type
                elif any(w in norm_subj for w in ("diner", "room", "hospital", "station", "road", "street", "house", "building", "outside", "inside", "pier", "hallway", "car", "vehicle")):
                    inferred_type = "location"
                elif any(w in norm_subj for w in ("storm", "rain", "wind", "weather", "snow", "fog", "thunder")):
                    inferred_type = "environment"
                elif any(w in norm_subj for w in ("bag", "key", "camera", "insulin", "bottle", "label", "phone", "photo", "picture", "clock", "poster")):
                    inferred_type = "object"

            subj_entity = resolve_or_create_entity(db, project_id, inferred_type, extracted_fact.subject, entity_name_map)
            if not subj_entity:
                continue

            existing_fact = db.query(Fact).filter(
                Fact.project_id == project_id,
                Fact.subject_entity_id == subj_entity.id,
                Fact.predicate == extracted_fact.predicate,
                Fact.value == extracted_fact.value
            ).first()

            if not existing_fact:
                fact_obj = Fact(
                    project_id=project_id,
                    subject_entity_id=subj_entity.id,
                    predicate=extracted_fact.predicate,
                    value=extracted_fact.value,
                    scene_id=scene.id,
                    confidence=extracted_fact.confidence,
                    source_type="SCREENPLAY"
                )
                db.add(fact_obj)
                db.flush()
                persisted_facts.append(fact_obj)
            else:
                persisted_facts.append(existing_fact)

        # 6. Event Persistence
        persisted_events = []
        for extracted_event in analysis.events:
            actor_ent = resolve_or_create_entity(db, project_id, "character", extracted_event.actor, entity_name_map) if extracted_event.actor else None
            target_ent = resolve_or_create_entity(db, project_id, "object", extracted_event.target, entity_name_map) if extracted_event.target else None
            loc_ent = resolve_or_create_entity(db, project_id, "location", extracted_event.location, entity_name_map) if extracted_event.location else None

            event_obj = Event(
                scene_id=scene.id,
                event_type=extracted_event.event_type.upper(),
                actor_entity_id=actor_ent.id if actor_ent else None,
                target_entity_id=target_ent.id if target_ent else None,
                location_entity_id=loc_ent.id if loc_ent else None,
                description=extracted_event.description,
                attributes_json={}
            )
            db.add(event_obj)
            db.flush()
            persisted_events.append(event_obj)

        # 7. Relationship Persistence
        persisted_relationships = []
        for extracted_rel in analysis.relationships:
            src_ent = resolve_or_create_entity(db, project_id, "character", extracted_rel.source, entity_name_map)
            tgt_ent = resolve_or_create_entity(db, project_id, "character", extracted_rel.target, entity_name_map) if extracted_rel.target else None
            if not src_ent:
                continue

            rel_obj = Relationship(
                project_id=project_id,
                source_entity_id=src_ent.id,
                relationship_type=extracted_rel.relationship_type.lower(),
                target_entity_id=tgt_ent.id if tgt_ent else None,
                scene_id=scene.id,
                confidence=extracted_rel.confidence,
                source_type="SCREENPLAY"
            )
            db.add(rel_obj)
            db.flush()
            persisted_relationships.append(rel_obj)

        # 8. Knowledge State Persistence
        persisted_knowledge = []
        for extracted_k in analysis.knowledge_changes:
            char_ent = resolve_or_create_entity(db, project_id, "character", extracted_k.character, entity_name_map)
            if not char_ent:
                continue

            # Clean & normalize knowledge text for fuzzy/punctuation-agnostic deduplication
            raw_k_text = extracted_k.knowledge.strip().strip('"\'').rstrip('.,!?').strip()
            norm_k_key = " ".join(raw_k_text.lower().split())

            existing_k_list = db.query(KnowledgeState).filter(
                KnowledgeState.project_id == project_id,
                KnowledgeState.character_entity_id == char_ent.id
            ).all()

            existing_k = next((
                k for k in existing_k_list 
                if " ".join(k.knowledge.strip().strip('"\'').rstrip('.,!?').strip().lower().split()) == norm_k_key
            ), None)

            if not existing_k:
                k_obj = KnowledgeState(
                    project_id=project_id,
                    character_entity_id=char_ent.id,
                    knowledge=extracted_k.knowledge.strip().strip('"\''),
                    source_scene_id=scene.id,
                    knowledge_type=extracted_k.knowledge_type,
                    confidence=extracted_k.confidence
                )
                db.add(k_obj)
                db.flush()
                persisted_knowledge.append(k_obj)
            else:
                persisted_knowledge.append(existing_k)

        db.commit()
        db.refresh(scene)

        # 9. Build updated Story State
        updated_story_state = build_story_state(db, project_id)

        # 10. Run downstream AI tasks in parallel (Continuity, Claims & Research, Plot Timeline) capped at max_workers=3
        from app.services.parallel_processor import execute_scene_downstream_tasks_parallel
        parallel_results = execute_scene_downstream_tasks_parallel(db, project_id, scene)
        detected_issues = parallel_results.get("issues", [])

        logger.info(f"Scene #{scene_number} processed successfully.")
        scene.is_analyzed = True
        db.commit()

        return {
            "scene": {
                "id": scene.id,
                "project_id": scene.project_id,
                "scene_number": scene.scene_number,
                "raw_text": scene.raw_text,
                "created_at": scene.created_at.isoformat(),
            },
            "analysis": analysis.model_dump(),
            "story_state": updated_story_state.model_dump(),
            "issues": [i.model_dump() for i in detected_issues]
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing scene #{scene_number}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process scene: {str(e)}"
        )
