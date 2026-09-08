import logging
import uuid
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
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

# Keywords that indicate an object is PRESENT / available
_PRESENT_KEYWORDS = frozenset([
    "has", "hold", "holds", "inside", "contain", "contains", "grabs", "grab",
    "picks up", "pick up", "found", "finds", "acquires", "acquire", "returned",
    "returns", "restored", "reappears", "reappear", "back", "retrieved", "retrieve",
    "carries", "carry", "brought", "brings", "with him", "with her", "with them",
    "in his bag", "in her bag", "in the bag",
])

# Keywords that indicate an object is ABSENT / unavailable
_ABSENT_KEYWORDS = frozenset([
    "missing", "gone", "lost", "disappeared", "disappear", "left behind",
    "no longer", "without", "not have", "doesn't have", "does not have",
    "forgot", "taken", "stolen", "destroyed", "dropped", "not found",
    "can't find", "cannot find", "is gone", "was gone",
])


def _classify_object_state(text: str) -> Optional[str]:
    """Returns 'PRESENT', 'ABSENT', or None based on keyword scan of text."""
    t = text.lower()
    absent_score = sum(1 for kw in _ABSENT_KEYWORDS if kw in t)
    present_score = sum(1 for kw in _PRESENT_KEYWORDS if kw in t)
    if absent_score > 0 and absent_score >= present_score:
        return "ABSENT"
    if present_score > 0:
        return "PRESENT"
    return None





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

    # 3. Object Ownership & State Candidate Generation
    for rel in current_relationships:
        if rel.relationship_type in ("owns", "possesses", "uses", "has") and rel.target_entity:
            obj_name = rel.target_entity.name
            user_name = rel.source_entity.name
            
            obj_prior = next((o for o in prior_state.objects if o.name.lower() == obj_name.lower()), None)
            if obj_prior:
                # 3a. Possession change without transfer
                if obj_prior.current_owner and obj_prior.current_owner.name.lower() != user_name.lower():
                    transfer_event = any(ev.event_type.upper() in ("GIVE_OBJECT", "TAKE_OBJECT", "SELL_OBJECT", "RECOVER_OBJECT", "FIND_OBJECT") for ev in current_events)
                    if not transfer_event:
                        cand_id = f"cand_own_{rel.id}"
                        candidates.append(ContinuityCandidate(
                            id=cand_id,
                            issue_type="OBJECT_OWNERSHIP_CONFLICT",
                            entity_name=obj_name,
                            current_scene_id=scene.id,
                            current_scene_number=scene.scene_number,
                            current_text=f"{user_name} possesses/uses {obj_name}",
                            previous_scene_id=scene.id,
                            previous_scene_number=max(1, scene.scene_number - 1),
                            previous_text=f"{obj_prior.current_owner.name} previously held/owned {obj_name}",
                            reason=f"Possession of {obj_name} changed from {obj_prior.current_owner.name} to {user_name} without an explicit transfer event"
                        ))

                # 3b. Object state / availability conflict (e.g. Insulin left behind -> used again)
                obj_status = (obj_prior.attributes or {}).get("status") or getattr(obj_prior, "status", None)
                if obj_status and str(obj_status).lower() in ("unavailable", "left_behind", "lost", "missing", "destroyed", "left"):
                    recovery_event = any(ev.event_type.upper() in ("RECOVER_OBJECT", "FIND_OBJECT", "BUY_OBJECT", "RETRIEVE_OBJECT") for ev in current_events)
                    if not recovery_event:
                        cand_id = f"cand_objstate_{rel.id}"
                        candidates.append(ContinuityCandidate(
                            id=cand_id,
                            issue_type="OBJECT_STATE_CONFLICT",
                            entity_name=obj_name,
                            current_scene_id=scene.id,
                            current_scene_number=scene.scene_number,
                            current_text=f"{user_name} uses/possesses {obj_name} in Scene {scene.scene_number}",
                            previous_scene_id=scene.id,
                            previous_scene_number=max(1, scene.scene_number - 1),
                            previous_text=f"{obj_name} was previously established as unavailable/left behind (status: {obj_status})",
                            reason=f"{obj_name} was left behind or unavailable in earlier scenes, but is used again without an intervening recovery event"
                        ))

    # 4. Event / Implied Interaction Candidate Generation (e.g. Diner visit)
    for ev in current_events:
        ev_desc = (ev.description or "").lower()
        if any(w in ev_desc for w in ("visit", "diner", "meet", "again", "earlier", "remember", "back to")):
            cand_id = f"cand_event_{ev.id}"
            candidates.append(ContinuityCandidate(
                id=cand_id,
                issue_type="EVENT_CONFLICT",
                entity_name=getattr(ev, "event_type", "Event Inconsistency"),
                current_scene_id=scene.id,
                current_scene_number=scene.scene_number,
                current_text=f"Scene {scene.scene_number} event/dialogue implies prior visit or interaction: '{ev.event_type}: {ev.description}'",
                previous_scene_id=scene.id,
                previous_scene_number=max(1, scene.scene_number - 1),
                previous_text="No matching prior event or visit established in preceding timeline.",
                reason="Dialogue or interaction suggests a prior visit or relationship event not established in preceding scenes"
            ))

    # 5. Knowledge Candidate Generation
    for ck in current_knowledge:
        char_name = ck.character_entity.name if ck.character_entity else "Character"
        knowledge_text = ck.knowledge.lower()

        char_prior = next((c for c in prior_state.characters if c.name.lower() == char_name.lower()), None)
        prior_known_texts = [k.knowledge.lower() for k in char_prior.knowledge] if (char_prior and char_prior.knowledge) else []

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

    # 6. Cross-Scene Object State Candidate Generation
    # Pre-filter: query DB for object entities in the current scene that had a
    # prior ABSENT state. Package as ContinuityCandidate so Gemini can evaluate
    # with full context — handling synonyms, negation, and edge cases properly.
    curr_obj_entities = db.execute(text("""
        SELECT DISTINCT e.name, e.id
        FROM entities e
        WHERE e.project_id = :pid AND e.type = 'object'
    """), {"pid": project_id}).fetchall()

    if curr_obj_entities:
        # Build current scene text blob for object reference confirmation
        curr_fact_blob_rows = db.execute(text("""
            SELECT e.name as subject, f.predicate, f.value
            FROM facts f
            JOIN entities e ON f.subject_entity_id = e.id
            WHERE f.scene_id = :sid
        """), {"sid": scene.id}).fetchall()
        curr_event_blob_rows = db.execute(text("""
            SELECT description FROM events WHERE scene_id = :sid
        """), {"sid": scene.id}).fetchall()
        curr_blob = " ".join(
            [f"{r.subject} {r.predicate} {r.value}" for r in curr_fact_blob_rows] +
            [r.description or "" for r in curr_event_blob_rows]
        ).lower()

        for obj_row in curr_obj_entities:
            obj_name = obj_row.name
            obj_lower = obj_name.lower()

            if len(obj_lower) < 4 or obj_lower not in curr_blob:
                continue

            # Query prior facts mentioning this object
            p_facts = db.execute(text("""
                SELECT e.name as subject, f.predicate, f.value, s.scene_number, s.id as scene_id
                FROM facts f
                JOIN entities e ON f.subject_entity_id = e.id
                JOIN scenes s ON f.scene_id = s.id
                WHERE s.project_id = :pid
                  AND s.scene_number < :csn
                  AND (lower(e.name) LIKE :pat OR lower(f.value) LIKE :pat OR lower(f.predicate) LIKE :pat)
                ORDER BY s.scene_number ASC
            """), {"pid": project_id, "csn": scene.scene_number, "pat": f"%{obj_lower}%"}).fetchall()

            # Query prior events mentioning this object
            p_events = db.execute(text("""
                SELECT ev.description, ev.event_type, s.scene_number, s.id as scene_id
                FROM events ev
                JOIN scenes s ON ev.scene_id = s.id
                WHERE s.project_id = :pid
                  AND s.scene_number < :csn
                  AND lower(ev.description) LIKE :pat
                ORDER BY s.scene_number ASC
            """), {"pid": project_id, "csn": scene.scene_number, "pat": f"%{obj_lower}%"}).fetchall()

            if not p_facts and not p_events:
                continue

            # Build timeline of classified states
            timeline: List[Tuple[int, str, str, str]] = []
            for r in p_facts:
                txt = f"{r.subject} {r.predicate} {r.value}"
                st = _classify_object_state(txt)
                if st:
                    timeline.append((r.scene_number, r.scene_id, st, txt))
            for r in p_events:
                st = _classify_object_state(r.description or "")
                if st:
                    timeline.append((r.scene_number, r.scene_id, st, r.description or ""))

            timeline.sort(key=lambda x: x[0])
            if not timeline:
                continue

            # Walk timeline to find the last ABSENT → check if current scene is PRESENT
            last_state, last_snum, last_sid, last_txt = None, None, None, ""
            for (sn, sid, st, txt) in timeline:
                last_state = st
                last_snum = sn
                last_sid = sid
                last_txt = txt

            if last_state != "ABSENT":
                continue

            # Build a rich evidence summary for Gemini to evaluate
            # Include all state-bearing entries from the timeline so Gemini
            # can reason about the full arc: present → absent → present
            timeline_summary = "; ".join(
                f"Sc.{sn}: [{st}] \"{txt[:80]}\"" for (sn, sid, st, txt) in timeline[-4:]
            )

            cand_id = f"cand_objstate_cross_{obj_row.id}"
            candidates.append(ContinuityCandidate(
                id=cand_id,
                issue_type="OBJECT_STATE_CONFLICT",
                entity_name=obj_name,
                current_scene_id=scene.id,
                current_scene_number=scene.scene_number,
                current_text=(
                    f"'{obj_name}' is referenced as present/used in Scene {scene.scene_number}."
                ),
                previous_scene_id=last_sid,
                previous_scene_number=last_snum,
                previous_text=(
                    f"'{obj_name}' was last recorded as ABSENT in Scene {last_snum}: "
                    f"\"{last_txt[:120]}\". "
                    f"Full state arc: [{timeline_summary}]"
                ),
                reason=(
                    f"'{obj_name}' was established as missing/absent in Scene {last_snum} "
                    f"but reappears in Scene {scene.scene_number} without a recorded "
                    f"recovery, transfer, or acquisition event."
                )
            ))
    # 7. Timeline Inconsistency Candidate Generation
    # Scans current scene raw text, facts, and events for timestamps (e.g. 11:42 PM, 7:12 P.M., 6:55 P.M., 1954).
    # Compares against prior scenes' timestamps to detect regressions or incompatible event timing.
    import re
    TIME_PATTERN = re.compile(r'\b(?:1[0-2]|0?[1-9]):[0-5][0-9]\s*(?:a\.?m\.?|p\.?m\.?|AM|PM)?\b|\b(?:19|20)\d{2}\b', re.IGNORECASE)

    curr_facts_text = " ".join([f"{f.predicate} {f.value}" for f in current_facts])
    curr_events_text = " ".join([f"{ev.event_type} {ev.description}" for ev in current_events])
    curr_full_text = (scene.raw_text or "") + " " + curr_facts_text + " " + curr_events_text

    curr_time_matches = TIME_PATTERN.findall(curr_full_text)
    if curr_time_matches:
        prior_facts_events = db.execute(text("""
            SELECT s.scene_number, s.id as scene_id, f.value as text_content
            FROM facts f
            JOIN scenes s ON f.scene_id = s.id
            WHERE s.project_id = :pid AND s.scene_number < :csn
            UNION ALL
            SELECT s.scene_number, s.id as scene_id, ev.description as text_content
            FROM events ev
            JOIN scenes s ON ev.scene_id = s.id
            WHERE s.project_id = :pid AND s.scene_number < :csn
        """), {"pid": project_id, "csn": scene.scene_number}).fetchall()

        for p_row in prior_facts_events:
            p_text = p_row.text_content or ""
            p_time_matches = TIME_PATTERN.findall(p_text)
            if p_time_matches:
                cand_id = f"cand_timeline_sc{scene.scene_number}_{p_row.scene_number}"
                candidates.append(ContinuityCandidate(
                    id=cand_id,
                    issue_type="TIMELINE_CONFLICT",
                    entity_name="Timeline",
                    current_scene_id=scene.id,
                    current_scene_number=scene.scene_number,
                    current_text=f"Scene {scene.scene_number} timestamp/time reference: \"{(curr_facts_text or scene.raw_text)[:120]}\"",
                    previous_scene_id=p_row.scene_id,
                    previous_scene_number=p_row.scene_number,
                    previous_text=f"Scene {p_row.scene_number} established time reference: \"{p_text[:120]}\"",
                    reason=f"The established timing of the experiment or event in Scene {p_row.scene_number} conflicts with the timestamp or time reference given in Scene {scene.scene_number}."
                ))
                logger.info(f"[TIMELINE] Scene #{scene.scene_number}: Nominated TIMELINE_CONFLICT candidate against Scene #{p_row.scene_number}.")
                break

    return candidates




def check_scene_continuity(db: Session, project_id: str, scene_id: str) -> List[IssueResponse]:
    """
    Main Continuity Service Function:
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
    
    # Candidate list is passed to Gemini evaluation along with active World Rules retrieved via hybrid context
    cand_summary = {}
    for c in candidates:
        cand_summary[c.issue_type] = cand_summary.get(c.issue_type, 0) + 1
    logger.info(f"[CONTINUITY] Scene #{scene.scene_number}: Generated {len(candidates)} candidates -> {cand_summary} (Strictness={strictness})")

    if not candidates:
        logger.info(f"[CONTINUITY] Scene #{scene.scene_number}: 0 candidates generated. Returning empty issues list.")
        return []

    # 4. Stage 2: Gemini Evaluation using Hybrid Context
    retrieved_items = hybrid_retrieve_context(db, project_id, scene.scene_number, scene.raw_text, task_type="CONTINUITY")
    context_lines = [f"{item.provenance_tag}: {item.content}" for item in retrieved_items]
    context_str = "\n".join(context_lines) if context_lines else f"Prior Scenes: 1 to {prior_scene_number}"

    gemini_eval_res = evaluate_continuity_candidates(candidates, scene.raw_text, context_str, continuity_strictness=strictness)
    logger.info(f"[CONTINUITY] Scene #{scene.scene_number}: Gemini returned {len(gemini_eval_res.evaluations)} evaluations.")

    # Modulate confidence threshold based on strictness (0=0.85, 5=0.70, 10=0.55)
    effective_confidence_threshold = max(0.50, 0.85 - (strictness * 0.03))

    # 5. Stage 3 & 4: Grounding, Fingerprint Suppression & Persistence
    persisted_issues: List[IssueResponse] = []
    cand_map = {c.id: c for c in candidates}

    for ev in gemini_eval_res.evaluations:
        eval_class = ev.classification.upper()
        logger.info(f"[CONTINUITY EVAL] Scene #{scene.scene_number} Candidate '{ev.candidate_id}' -> Class: {eval_class}, Conf: {ev.confidence:.2f} (Threshold: {effective_confidence_threshold:.2f}), Title: '{ev.title}'")
        
        if eval_class not in ("CONFLICT", "AMBIGUOUS") or ev.confidence < (effective_confidence_threshold - 0.15):
            logger.info(f"[CONTINUITY EVAL] Skipping candidate '{ev.candidate_id}' (Class={eval_class}, Conf={ev.confidence:.2f})")
            continue

        cand = cand_map.get(ev.candidate_id)
        if not cand:
            continue

        # Compute deterministic issue fingerprint
        scene_nums = [cand.previous_scene_number, cand.current_scene_number]
        fingerprint = compute_issue_fingerprint(project_id, cand.issue_type, cand.entity_name, scene_nums)

        # Map severity (AMBIGUOUS maps to WARNING or INFO)
        computed_severity = ev.severity.upper() if eval_class == "CONFLICT" else "WARNING"

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
            severity=computed_severity,
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

    try:
        db.commit()
    except Exception as commit_err:
        logger.warning(f"Initial commit warning for scene #{scene.scene_number}: {commit_err}")
        db.rollback()
        try:
            db.commit()
        except Exception as retry_err:
            logger.error(f"Commit retry failed for scene #{scene.scene_number}: {retry_err}")

    logger.info(f"Persisted {len(persisted_issues)} continuity issues for scene #{scene.scene_number}.")
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
