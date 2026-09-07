import logging
import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.db.models import Project, Scene, Entity, Fact, Event, Relationship, KnowledgeState, Issue, IssueReview
from app.services.story_state import build_story_state
from app.services.gemini import evaluate_continuity_candidates
from app.services.issue_review import compute_issue_fingerprint
from app.schemas.story_state import StoryStateResponse
from app.schemas.issue import (
    ContinuityCandidate, GeminiCandidateEvaluation, IssueEvidence, IssueResponse
)
from app.schemas.issue_review import IssueReviewResponse

logger = logging.getLogger("script_supervisor.continuity")

MIN_CONFIDENCE_THRESHOLD = 0.70

def generate_candidates_for_scene(
    db: Session, project_id: str, scene: Scene, prior_state: StoryStateResponse
) -> List[ContinuityCandidate]:
    """Stage 1: Generates candidate conflicts between new scene N and prior Story State (scenes 1..N-1)."""
    candidates: List[ContinuityCandidate] = []
    
    current_facts = db.query(Fact).filter(Fact.scene_id == scene.id).all()
    current_events = db.query(Event).filter(Event.scene_id == scene.id).all()
    current_relationships = db.query(Relationship).filter(Relationship.scene_id == scene.id).all()
    current_knowledge = db.query(KnowledgeState).filter(KnowledgeState.source_scene_id == scene.id).all()

    # Check prior writer review decisions to respect writer intent
    from app.services.retriever import retrieve_writer_decisions
    writer_items = retrieve_writer_decisions(db, project_id)
    ignored_entity_types = set()
    for wi in writer_items:
        # e.g. "Writer Decision: FACT_CONFLICT (IGNORED)"
        for itype in ("FACT_CONFLICT", "LOCATION_CONFLICT", "OBJECT_OWNERSHIP_CONFLICT", "KNOWLEDGE_CONFLICT"):
            if itype in wi.title and ("IGNORED" in wi.content or "ACCEPTED" in wi.content):
                ignored_entity_types.add(itype)

    # 1. Fact Candidate Generation
    if "FACT_CONFLICT" not in ignored_entity_types:
        for cf in current_facts:
            for pf in prior_state.facts:
                sub_match = (cf.subject_entity.name.lower() == pf.subject.name.lower())
                pred_norm_cf = cf.predicate.lower().replace("_", " ")
                pred_norm_pf = pf.predicate.lower().replace("_", " ")
                possession_set = {"owns", "possesses", "has", "drives", "vehicle", "car", "residence", "lives", "lives in", "lives_in", "resides", "location", "home", "city"}
                pred_match = (pred_norm_cf == pred_norm_pf) or (pred_norm_cf in possession_set and pred_norm_pf in possession_set)
                
                if sub_match and pred_match:
                    if str(cf.value).strip().lower() != str(pf.value).strip().lower():
                        cand_id = f"cand_fact_{cf.id}_{pf.id}"
                        candidates.append(ContinuityCandidate(
                            id=cand_id,
                            issue_type="FACT_CONFLICT",
                            entity_name=pf.subject.name,
                            current_scene_id=scene.id,
                            current_scene_number=scene.scene_number,
                            current_text=f"{cf.subject_entity.name} {cf.predicate} = {cf.value}",
                            previous_scene_id=pf.source_scene_id,
                            previous_scene_number=pf.source_scene_number or 1,
                            previous_text=f"{pf.subject.name} {pf.predicate} = {pf.value}",
                            reason=f"Fact value mismatch for {cf.predicate}"
                        ))

    # 2. Location Candidate Generation
    scene_travel_events = [ev for ev in current_events if ev.event_type.upper() in ("TRAVEL", "MOVE", "FLIGHT")]
    prior_travel_events = [
        ev for ev in prior_state.events 
        if ev.event_type.upper() in ("TRAVEL", "MOVE", "FLIGHT") and (ev.scene_number or 0) >= max(1, scene.scene_number - 2)
    ]
    
    for ev in current_events:
        if ev.actor_entity and ev.location_entity:
            actor_name = ev.actor_entity.name
            loc_name = ev.location_entity.name
            
            char_prior = next((c for c in prior_state.characters if c.name.lower() == actor_name.lower()), None)
            if char_prior and char_prior.current_location:
                prior_loc = char_prior.current_location.name
                
                # Check if prior travel event already accounts for this location transition
                has_prior_travel = False
                for pte in prior_travel_events:
                    pte_actor = pte.actor.name if pte.actor else ""
                    pte_desc = (pte.description or "").lower()
                    if pte_actor.lower() == actor_name.lower():
                        # e.g. Travel to Mumbai or travel to loc_name
                        if loc_name.lower() in pte_desc or (pte.location and pte.location.name.lower() in loc_name.lower()):
                            has_prior_travel = True
                            break
                        # Check city/region overlap (e.g. "mumbai" in "mumbai cafe")
                        loc_words = [w.lower() for w in loc_name.split() if len(w) > 3]
                        if any(w in pte_desc for w in loc_words):
                            has_prior_travel = True
                            break

                if prior_loc.lower() != loc_name.lower() and not scene_travel_events and not has_prior_travel:
                    # Avoid flagging if both location names share city name (e.g., "Mumbai Highway" -> "Mumbai Cafe")
                    shared_city = any(w.lower() in prior_loc.lower() for w in loc_name.split() if len(w) > 3 and w.lower() in ("mumbai", "chennai", "delhi", "pune", "london", "paris", "tokyo"))
                    if not shared_city:
                        cand_id = f"cand_loc_{ev.id}"
                        candidates.append(ContinuityCandidate(
                            id=cand_id,
                            issue_type="LOCATION_CONFLICT",
                            entity_name=actor_name,
                            current_scene_id=scene.id,
                            current_scene_number=scene.scene_number,
                            current_text=f"{actor_name} is located at {loc_name}",
                            previous_scene_id=scene.id,
                            previous_scene_number=max(1, scene.scene_number - 1),
                            previous_text=f"{actor_name} was previously located at {prior_loc}",
                            reason=f"Character location changed from {prior_loc} to {loc_name} without travel event"
                        ))

    # 3. Object Ownership Candidate Generation
    for rel in current_relationships:
        if rel.relationship_type in ("owns", "possesses") and rel.target_entity:
            obj_name = rel.target_entity.name
            new_owner = rel.source_entity.name
            
            obj_prior = next((o for o in prior_state.objects if o.name.lower() == obj_name.lower()), None)
            if obj_prior and obj_prior.current_owner:
                prior_owner = obj_prior.current_owner.name
                if prior_owner.lower() != new_owner.lower():
                    transfer_event = any(ev.event_type.upper() in ("GIVE_OBJECT", "TAKE_OBJECT", "SELL_OBJECT") for ev in current_events)
                    if not transfer_event:
                        cand_id = f"cand_own_{rel.id}"
                        candidates.append(ContinuityCandidate(
                            id=cand_id,
                            issue_type="OBJECT_OWNERSHIP_CONFLICT",
                            entity_name=obj_name,
                            current_scene_id=scene.id,
                            current_scene_number=scene.scene_number,
                            current_text=f"{new_owner} owns/possesses {obj_name}",
                            previous_scene_id=scene.id,
                            previous_scene_number=max(1, scene.scene_number - 1),
                            previous_text=f"{prior_owner} previously owned {obj_name}",
                            reason=f"Ownership of {obj_name} changed from {prior_owner} to {new_owner} without transfer"
                        ))

    # 4. Knowledge Candidate Generation
    for ck in current_knowledge:
        char_name = ck.character_entity.name
        knowledge_text = ck.knowledge.lower()
        
        char_prior = next((c for c in prior_state.characters if c.name.lower() == char_name.lower()), None)
        prior_known_texts = [k.knowledge.lower() for k in char_prior.knowledge] if char_prior else []
        
        if not any(knowledge_text in pk or pk in knowledge_text for pk in prior_known_texts):
            cand_id = f"cand_k_{ck.id}"
            candidates.append(ContinuityCandidate(
                id=cand_id,
                issue_type="KNOWLEDGE_CONFLICT",
                entity_name=char_name,
                current_scene_id=scene.id,
                current_scene_number=scene.scene_number,
                current_text=f"{char_name} claims/acts on knowledge: '{ck.knowledge}'",
                previous_scene_id=scene.id,
                previous_scene_number=max(1, scene.scene_number - 1),
                previous_text="No prior knowledge acquisition event found in preceding scenes.",
                reason=f"Character {char_name} acts on knowledge without prior transfer"
            ))

    return candidates


def check_scene_continuity(db: Session, project_id: str, scene_id: str) -> List[IssueResponse]:
    """
    Main Day 3 & Day 4 Service Function:
    Checks scene_id for continuity conflicts against prior Story State.
    Uses issue fingerprinting, active Story World Rules, Continuity Strictness, and writer decision suppression.
    """
    logger.info(f"Checking continuity for scene_id={scene_id} in project_id={project_id}")

    scene = db.query(Scene).filter(Scene.id == scene_id, Scene.project_id == project_id).first()
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scene '{scene_id}' not found."
        )

    # 1. Fetch Project Settings & Active World Rules
    from app.services.project_settings import get_or_create_project_settings, get_active_world_rules
    from app.services.retriever import hybrid_retrieve_context
    
    settings_obj = get_or_create_project_settings(db, project_id)
    strictness = settings_obj.continuity_strictness # 0 to 10
    active_world_rules = get_active_world_rules(db, project_id)

    # 2. Reconstruct prior Story State (up to scene N-1)
    prior_scene_number = max(0, scene.scene_number - 1)
    prior_story_state = build_story_state(db, project_id, up_to_scene_number=prior_scene_number)

    # 3. Stage 1: Candidate Generation
    candidates = generate_candidates_for_scene(db, project_id, scene, prior_story_state)
    
    # Filter candidates if they match active world rules
    filtered_candidates = []
    for cand in candidates:
        matched_rule = False
        for rule in active_world_rules:
            # If candidate text or entity matches active world rule, candidate is permitted by fictional physics
            rule_words = [w.lower() for w in rule.rule_text.split() if len(w) > 3]
            cand_words = (cand.current_text + " " + cand.reason).lower()
            if len(rule_words) > 0 and sum(1 for w in rule_words if w in cand_words) >= max(1, len(rule_words) // 2):
                matched_rule = True
                logger.info(f"Candidate {cand.id} permitted by Story World Rule: '{rule.rule_text}'")
                break
        if not matched_rule:
            filtered_candidates.append(cand)

    candidates = filtered_candidates
    logger.info(f"Generated {len(candidates)} continuity candidates for scene #{scene.scene_number} (Strictness={strictness})")

    if not candidates:
        return []

    # 4. Stage 2: Gemini Evaluation using Hybrid Context
    retrieved_items = hybrid_retrieve_context(db, project_id, scene.scene_number, scene.raw_text, task_type="CONTINUITY")
    context_lines = [f"{item.provenance_tag}: {item.content}" for item in retrieved_items]
    context_str = "\n".join(context_lines) if context_lines else f"Prior Scenes: 1 to {prior_scene_number}"

    gemini_eval_res = evaluate_continuity_candidates(candidates, scene.raw_text, context_str, continuity_strictness=strictness)

    # Modulate confidence threshold based on strictness (0=0.85, 5=0.70, 10=0.55)
    effective_confidence_threshold = max(0.50, 0.85 - (strictness * 0.03))

    # 5. Stage 3 & 4: Grounding, Fingerprint Suppression & Persistence
    persisted_issues: List[IssueResponse] = []
    cand_map = {c.id: c for c in candidates}

    for ev in gemini_eval_res.evaluations:
        if ev.classification.upper() != "CONFLICT" or ev.confidence < effective_confidence_threshold:
            continue

        cand = cand_map.get(ev.candidate_id)
        if not cand:
            continue

        # Compute deterministic issue fingerprint
        scene_nums = [cand.previous_scene_number, cand.current_scene_number]
        fingerprint = compute_issue_fingerprint(project_id, cand.issue_type, cand.entity_name, scene_nums)

        # Check existing reviewed or open issues with same fingerprint
        existing_issue = db.query(Issue).filter(
            Issue.project_id == project_id,
            Issue.issue_fingerprint == fingerprint
        ).first()

        # Build evidence objects
        evidence_list = [
            IssueEvidence(
                scene_id=cand.previous_scene_id,
                scene_number=cand.previous_scene_number,
                type="ESTABLISHED_FACT" if cand.issue_type == "FACT_CONFLICT" else "HISTORICAL_STATE",
                text=cand.previous_text
            ),
            IssueEvidence(
                scene_id=cand.current_scene_id,
                scene_number=cand.current_scene_number,
                type="CONFLICTING_FACT" if cand.issue_type == "FACT_CONFLICT" else "NEW_SCENE_STATE",
                text=cand.current_text
            )
        ]

        if existing_issue:
            # If already reviewed by writer (ACCEPTED, IGNORED, RESOLVED), suppress re-creation!
            reviews = db.query(IssueReview).filter(IssueReview.issue_id == existing_issue.id).order_by(IssueReview.created_at.asc()).all()
            review_responses = [IssueReviewResponse.model_validate(r) for r in reviews]

            persisted_issues.append(IssueResponse(
                id=existing_issue.id,
                project_id=existing_issue.project_id,
                scene_id=existing_issue.scene_id,
                scene_number=scene.scene_number,
                issue_type=existing_issue.issue_type,
                severity=existing_issue.severity,
                title=existing_issue.title,
                description=existing_issue.description,
                confidence=existing_issue.confidence,
                status=existing_issue.status,
                evidence=[IssueEvidence(**e) for e in (existing_issue.evidence_json or [])],
                reviewed_at=existing_issue.reviewed_at,
                reviewed_by=existing_issue.reviewed_by,
                resolution_type=existing_issue.resolution_type,
                resolution_note=existing_issue.resolution_note,
                issue_fingerprint=existing_issue.issue_fingerprint,
                reviews=review_responses,
                created_at=existing_issue.created_at
            ))
            continue

        # Create new Issue record
        issue_obj = Issue(
            project_id=project_id,
            scene_id=scene.id,
            issue_type=cand.issue_type,
            severity=ev.severity.upper(),
            title=ev.title,
            description=ev.description,
            confidence=ev.confidence,
            status="OPEN",
            evidence_json=[e.model_dump() for e in evidence_list],
            issue_fingerprint=fingerprint
        )
        db.add(issue_obj)
        db.flush()

        persisted_issues.append(IssueResponse(
            id=issue_obj.id,
            project_id=issue_obj.project_id,
            scene_id=issue_obj.scene_id,
            scene_number=scene.scene_number,
            issue_type=issue_obj.issue_type,
            severity=issue_obj.severity,
            title=issue_obj.title,
            description=issue_obj.description,
            confidence=issue_obj.confidence,
            status=issue_obj.status,
            evidence=evidence_list,
            reviewed_at=issue_obj.reviewed_at,
            reviewed_by=issue_obj.reviewed_by,
            resolution_type=issue_obj.resolution_type,
            resolution_note=issue_obj.resolution_note,
            issue_fingerprint=issue_obj.issue_fingerprint,
            reviews=[],
            created_at=issue_obj.created_at
        ))

    db.commit()
    logger.info(f"Persisted {len(persisted_issues)} continuity issues for scene #{scene.scene_number}")
    return persisted_issues


def get_project_issues(
    db: Session, project_id: str, status_filter: Optional[str] = None, severity_filter: Optional[str] = None
) -> List[IssueResponse]:
    """Fetches all continuity issues for a project with scene_number join, history reviews, and filtering."""
    query = db.query(Issue, Scene.scene_number).join(Scene, Issue.scene_id == Scene.id)\
        .filter(Issue.project_id == project_id)

    if status_filter:
        query = query.filter(Issue.status == status_filter.upper())
    if severity_filter:
        query = query.filter(Issue.severity == severity_filter.upper())

    results = query.order_by(Scene.scene_number.asc(), Issue.created_at.desc()).all()

    issue_responses = []
    for issue_obj, scene_num in results:
        evidence_items = [IssueEvidence(**e) for e in (issue_obj.evidence_json or [])]
        reviews = db.query(IssueReview).filter(IssueReview.issue_id == issue_obj.id).order_by(IssueReview.created_at.asc()).all()
        review_responses = [IssueReviewResponse.model_validate(r) for r in reviews]

        issue_responses.append(IssueResponse(
            id=issue_obj.id,
            project_id=issue_obj.project_id,
            scene_id=issue_obj.scene_id,
            scene_number=scene_num,
            issue_type=issue_obj.issue_type,
            severity=issue_obj.severity,
            title=issue_obj.title,
            description=issue_obj.description,
            confidence=issue_obj.confidence,
            status=issue_obj.status,
            evidence=evidence_items,
            reviewed_at=issue_obj.reviewed_at,
            reviewed_by=issue_obj.reviewed_by,
            resolution_type=issue_obj.resolution_type,
            resolution_note=issue_obj.resolution_note,
            issue_fingerprint=issue_obj.issue_fingerprint,
            reviews=review_responses,
            created_at=issue_obj.created_at
        ))

    return issue_responses
