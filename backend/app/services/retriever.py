import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.db.models import (
    Project, Scene, Entity, Fact, Event, Relationship, KnowledgeState, 
    Issue, IssueReview, Claim, ResearchTask, ResearchResult, ResearchEvaluation
)
from app.schemas.retrieval import RetrievedItem

logger = logging.getLogger("script_supervisor.retriever")

# Configurable Context Limits
MAX_RETRIEVED_SCENES = 5
MAX_RETRIEVED_FACTS = 10
MAX_RETRIEVED_EVENTS = 5
MAX_RETRIEVED_SOURCES = 5

def normalize_name(name: str) -> str:
    return name.strip().lower()

def retrieve_structured_context(
    db: Session,
    project_id: str,
    scene_number: int,
    entity_names: List[str]
) -> List[RetrievedItem]:
    """Retrieves exact structured SQL state facts up to scene_number - 1 for specific target entities."""
    logger.info(f"Retrieving structured context for project_id='{project_id}' up to scene #{scene_number - 1} for entities: {entity_names}")
    items: List[RetrievedItem] = []
    norm_entities = [normalize_name(e) for e in entity_names if e]

    # Query Scenes up to scene_number - 1
    prior_scenes = db.query(Scene).filter(
        Scene.project_id == project_id,
        Scene.scene_number < scene_number
    ).order_by(Scene.scene_number.asc()).all()

    scene_map = {s.id: s.scene_number for s in prior_scenes}
    prior_scene_ids = list(scene_map.keys())

    if not prior_scene_ids:
        return items

    # 1. Facts
    facts_query = db.query(Fact, Entity.name, Scene.scene_number).join(Entity, Fact.subject_entity_id == Entity.id)\
        .join(Scene, Fact.scene_id == Scene.id)\
        .filter(Fact.project_id == project_id, Fact.scene_id.in_(prior_scene_ids))

    if norm_entities:
        facts_query = facts_query.filter(or_(*[Entity.name.ilike(f"%{e}%") for e in norm_entities]))

    for f, ent_name, sc_num in facts_query.limit(MAX_RETRIEVED_FACTS).all():
        items.append(RetrievedItem(
            item_type="FACT",
            source_id=f.id,
            scene_id=f.scene_id,
            scene_number=sc_num,
            title=f"Fact: {ent_name} {f.predicate}",
            content=f"{ent_name} {f.predicate} is '{f.value}'",
            provenance_tag=f"[FACT — Scene {sc_num}]",
            relevance_score=0.95,
            retrieval_reason="structured_entity_fact"
        ))

    # 2. Knowledge States
    ks_query = db.query(KnowledgeState, Entity.name, Scene.scene_number)\
        .join(Entity, KnowledgeState.character_entity_id == Entity.id)\
        .join(Scene, KnowledgeState.source_scene_id == Scene.id)\
        .filter(KnowledgeState.project_id == project_id, KnowledgeState.source_scene_id.in_(prior_scene_ids))

    if norm_entities:
        ks_query = ks_query.filter(or_(*[Entity.name.ilike(f"%{e}%") for e in norm_entities]))

    for ks, char_name, sc_num in ks_query.limit(MAX_RETRIEVED_FACTS).all():
        items.append(RetrievedItem(
            item_type="KNOWLEDGE",
            source_id=ks.id,
            scene_id=ks.source_scene_id,
            scene_number=sc_num,
            title=f"Knowledge: {char_name}",
            content=f"{char_name} knows: '{ks.knowledge}' (via {ks.knowledge_type})",
            provenance_tag=f"[KNOWLEDGE — Scene {sc_num}]",
            relevance_score=0.90,
            retrieval_reason="structured_character_knowledge"
        ))

    # 3. Events
    events_query = db.query(Event, Scene.scene_number).join(Scene, Event.scene_id == Scene.id)\
        .filter(Scene.project_id == project_id, Event.scene_id.in_(prior_scene_ids))

    for ev, sc_num in events_query.order_by(Event.created_at.desc()).limit(MAX_RETRIEVED_EVENTS).all():
        desc = ev.description
        if not norm_entities or any(e in desc.lower() for e in norm_entities):
            items.append(RetrievedItem(
                item_type="EVENT",
                source_id=ev.id,
                scene_id=ev.scene_id,
                scene_number=sc_num,
                title=f"Event: {ev.event_type}",
                content=ev.description,
                provenance_tag=f"[EVENT — Scene {sc_num}]",
                relevance_score=0.85,
                retrieval_reason="structured_event_timeline"
            ))

    return items


def retrieve_writer_decisions(db: Session, project_id: str) -> List[RetrievedItem]:
    """Retrieves past writer review decisions (ACCEPTED, IGNORED, RESOLVED) for review context awareness."""
    items: List[RetrievedItem] = []
    reviewed_issues = db.query(Issue, Scene.scene_number)\
        .join(Scene, Issue.scene_id == Scene.id)\
        .filter(Issue.project_id == project_id, Issue.status.in_(["ACCEPTED", "IGNORED", "RESOLVED"])).all()

    for issue, sc_num in reviewed_issues:
        items.append(RetrievedItem(
            item_type="WRITER_DECISION",
            source_id=issue.id,
            scene_id=issue.scene_id,
            scene_number=sc_num,
            title=f"Writer Decision: {issue.issue_type} ({issue.status})",
            content=f"Issue '{issue.title}' was marked {issue.status} by writer. Resolution note: {issue.resolution_note or 'Intentional creative choice'}",
            provenance_tag=f"[WRITER DECISION — Scene {sc_num}]",
            relevance_score=0.98,
            retrieval_reason="writer_review_memory"
        ))

    return items


def retrieve_research_evidence(db: Session, project_id: str) -> List[RetrievedItem]:
    """Retrieves existing Parallel external research evidence for reality checking context."""
    items: List[RetrievedItem] = []
    evals = db.query(ResearchEvaluation, Claim.claim_text, Scene.scene_number)\
        .join(Claim, ResearchEvaluation.claim_id == Claim.id)\
        .join(Scene, Claim.scene_id == Scene.id)\
        .filter(Claim.project_id == project_id).all()

    for ev, claim_txt, sc_num in evals:
        items.append(RetrievedItem(
            item_type="RESEARCH",
            source_id=ev.id,
            scene_id=ev.claim_id,
            scene_number=sc_num,
            title=f"External Research: {ev.verdict}",
            content=f"Claim '{claim_txt}' evaluated as {ev.verdict} ({int(ev.confidence * 100)}% confidence). Summary: {ev.summary}",
            provenance_tag=f"[RESEARCH EVIDENCE — Scene {sc_num}]",
            relevance_score=0.92,
            retrieval_reason="cached_parallel_research"
        ))

    return items


def retrieve_story_world_rules(db: Session, project_id: str) -> List[RetrievedItem]:
    """Retrieves active user-authored Story World Rules for fictional universe constraints."""
    from app.services.project_settings import get_active_world_rules
    active_rules = get_active_world_rules(db, project_id)
    items: List[RetrievedItem] = []
    for r in active_rules:
        items.append(RetrievedItem(
            item_type="WORLD_RULE",
            source_id=r.id,
            scene_id=None,
            scene_number=None,
            title=f"Story World Rule",
            content=r.rule_text,
            provenance_tag=f'[WORLD_RULE — Rule {r.id}] "{r.rule_text}"',
            relevance_score=0.99,
            retrieval_reason="fictional_universe_rule"
        ))
    return items


def retrieve_semantic_context(
    db: Session,
    project_id: str,
    scene_text: str,
    current_scene_number: int
) -> List[RetrievedItem]:
    """
    Performs keyword/paraphrase similarity retrieval across prior scenes
    to find long-range narrative connections (e.g. Scene 5 -> Scene 50).
    """
    items: List[RetrievedItem] = []
    prior_scenes = db.query(Scene).filter(
        Scene.project_id == project_id,
        Scene.scene_number < current_scene_number
    ).all()

    text_lower = scene_text.lower()
    words = [w.strip() for w in text_lower.split() if len(w) > 4 and w not in ("enter", "leaves", "apartment", "night", "street")]

    for sc in prior_scenes:
        sc_lower = sc.raw_text.lower()
        matches = [w for w in words if w in sc_lower]
        if len(matches) >= 2:
            items.append(RetrievedItem(
                item_type="SCENE",
                source_id=sc.id,
                scene_id=sc.id,
                scene_number=sc.scene_number,
                title=f"Historical Scene #{sc.scene_number}",
                content=sc.raw_text[:200],
                provenance_tag=f"[SCENE — Scene {sc.scene_number}]",
                relevance_score=min(0.70 + (len(matches) * 0.05), 0.95),
                retrieval_reason=f"semantic_keyword_match ({', '.join(matches[:3])})"
            ))

    return items


def hybrid_retrieve_context(
    db: Session,
    project_id: str,
    scene_number: int,
    scene_text: str,
    task_type: str = "CONTINUITY",
    entity_names: Optional[List[str]] = None
) -> List[RetrievedItem]:
    """
    Day 6 Core Retrieval Service Function:
    Executes hybrid retrieval (Structured SQL + Writer Decisions + External Research + Semantic Paraphrase),
    deduplicates items, ranks by relevance, and applies strict context token limits.
    """
    entity_names = entity_names or []
    logger.info(f"Executing hybrid retrieval for project_id='{project_id}', scene #{scene_number}, task_type='{task_type}'")

    # 1. Gather all retrieval streams
    rule_items = retrieve_story_world_rules(db, project_id)
    structured_items = retrieve_structured_context(db, project_id, scene_number, entity_names)
    writer_items = retrieve_writer_decisions(db, project_id)
    research_items = retrieve_research_evidence(db, project_id)
    semantic_items = retrieve_semantic_context(db, project_id, scene_text, scene_number)

    all_items = rule_items + structured_items + writer_items + research_items + semantic_items

    # 2. Deduplicate items by source_id + item_type
    seen_keys = set()
    deduped_items: List[RetrievedItem] = []

    for it in all_items:
        key = f"{it.item_type}:{it.source_id}"
        if key not in seen_keys:
            seen_keys.add(key)
            deduped_items.append(it)

    # 3. Sort by relevance_score descending
    deduped_items.sort(key=lambda x: x.relevance_score, reverse=True)

    # 4. Truncate to context limits
    final_items = deduped_items[:(MAX_RETRIEVED_FACTS + MAX_RETRIEVED_EVENTS + MAX_RETRIEVED_SCENES + MAX_RETRIEVED_SOURCES)]

    logger.info(f"Hybrid retrieval returned {len(final_items)} deduplicated, provenance-tagged context items.")
    return final_items
