import logging
from typing import Dict, Any, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.db.models import Scene, Project, Issue, Claim, SceneAnalysisRun
from app.services.scene_processor import process_scene
from app.services.story_state import build_story_state
from app.services.retriever import hybrid_retrieve_context, retrieve_writer_decisions
from app.services.continuity import check_scene_continuity
from app.services.reasoning import execute_targeted_reasoning
from app.services.research_service import process_scene_claims, execute_research_for_claim
from app.schemas.unified import UnifiedAnalysisResponse, AnalysisRunSummary

logger = logging.getLogger("script_supervisor.unified_supervisor")

def process_scene_unified(db: Session, project_id: str, scene_id: str) -> UnifiedAnalysisResponse:
    """
    Application Service: Unified Script Supervisor Scene Ingestion & Analysis Pipeline.
    Orchestrates parsing, historical state boundary checking, hybrid retrieval, deterministic checks,
    AI story reasoning, gated external research, and issue deduplication.
    """
    scene = db.query(Scene).filter(Scene.id == scene_id, Scene.project_id == project_id).first()
    if not scene:
        raise ValueError(f"Scene '{scene_id}' not found in project '{project_id}'")

    started_at = datetime.now(timezone.utc)
    
    # 1. Create Analysis Run Record
    run = SceneAnalysisRun(
        project_id=project_id,
        scene_id=scene.id,
        status="ANALYZING",
        started_at=started_at,
        completed_at=started_at
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    analysis_status = "COMPLETED"
    error_msg = None
    research_reused = 0
    issues_created_count = 0
    research_tasks_count = 0
    entity_names: List[str] = []

    try:
        logger.info(f"[UNIFIED PIPELINE] Starting analysis for Scene #{scene.scene_number} (ID={scene.id})")
        # Step 1: Parse scene semantics & update persistent story state
        proc_res = process_scene(db, project_id, scene.scene_number, scene.raw_text)
        analysis_data = proc_res.get("analysis", {})
        entities = analysis_data.get("entities", [])
        facts = analysis_data.get("facts", [])
        events = analysis_data.get("events", [])

        entities_count = len(entities)
        facts_count = len(facts)
        events_count = len(events)
        entity_names = [e.get("name") if isinstance(e, dict) else getattr(e, "name", str(e)) for e in entities if e]
        logger.info(f"[UNIFIED PIPELINE] Step 1 complete for Scene #{scene.scene_number}: {entities_count} entities, {facts_count} facts, {events_count} events extracted.")

        # Step 2: Build historical Story State BEFORE current scene (up to scene_number - 1)
        prior_state = build_story_state(db, project_id, up_to_scene_number=max(0, scene.scene_number - 1))
        logger.info(f"[UNIFIED PIPELINE] Step 2 complete for Scene #{scene.scene_number}: Built prior state with {len(prior_state.facts)} facts, {len(prior_state.events)} events.")

        # Step 3: Contextual Hybrid Retrieval for active entities
        hybrid_retrieval = hybrid_retrieve_context(
            db, project_id, scene.scene_number, scene.raw_text, task_type="CONTINUITY", entity_names=entity_names
        )

        # Step 4: Deterministic Continuity & Knowledge Checks
        issues = check_scene_continuity(db, project_id, scene.id)
        issues_created_count = len(issues)
        logger.info(f"[UNIFIED PIPELINE] Step 4 complete for Scene #{scene.scene_number}: {issues_created_count} continuity issues created/returned.")

        # Step 5: Targeted AI Story Reasoning
        reasoning_res = execute_targeted_reasoning(
            db, project_id, scene.id, task_type="CONTINUITY", target_entity_names=entity_names
        )
        logger.info(f"[UNIFIED PIPELINE] Step 5 complete for Scene #{scene.scene_number}: Story reasoning completed.")

        # Step 6: Real-World Claim Extraction & Gated Parallel Research Reuse
        try:
            claims = process_scene_claims(db, project_id, scene)
            claims_count = len(claims)
            logger.info(f"[UNIFIED PIPELINE] Step 6 complete for Scene #{scene.scene_number}: {claims_count} claims processed.")

            for claim in claims:
                if claim.requires_research:
                    # Check if research was previously completed for identical claim fingerprint
                    if claim.status in ("VERIFIED", "LIKELY_TRUE", "CONTRADICTED", "INCONCLUSIVE"):
                        research_reused += 1
                    else:
                        execute_research_for_claim(db, project_id, claim.id, force_refresh=False)
                        research_tasks_count += 1
        except Exception as research_err:
            logger.warning(f"External research step encountered a partial failure: {research_err}")
            analysis_status = "PARTIAL"
            error_msg = f"Research step warning: {str(research_err)}"
            claims_count = 0

    except Exception as e:
        logger.error(f"Unified analysis failed for scene #{scene.scene_number}: {e}", exc_info=True)
        analysis_status = "FAILED"
        error_msg = str(e)
        entities_count = 0
        facts_count = 0
        events_count = 0
        claims_count = 0

    completed_at = datetime.now(timezone.utc)

    # Update Analysis Run Record
    run.status = analysis_status
    scene.is_analyzed = True
    run.entities_count = entities_count
    run.facts_count = facts_count
    run.events_count = events_count
    run.issues_count = issues_created_count
    run.claims_count = claims_count
    run.research_reused_count = research_reused
    run.error_message = error_msg
    run.completed_at = completed_at
    db.commit()

    return UnifiedAnalysisResponse(
        run_id=run.id,
        project_id=project_id,
        scene_id=scene.id,
        scene_number=scene.scene_number,
        status=analysis_status,
        summary=AnalysisRunSummary(
            entities_count=entities_count,
            facts_count=facts_count,
            events_count=events_count,
            issues_count=issues_created_count,
            claims_count=claims_count,
            research_reused_count=research_reused
        ),
        entities_detected=entity_names,
        issues_created=issues_created_count,
        research_tasks_created=research_tasks_count,
        error_message=error_msg,
        started_at=started_at,
        completed_at=completed_at
    )
