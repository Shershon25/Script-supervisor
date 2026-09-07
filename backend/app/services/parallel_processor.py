import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db.models import Scene, PlotEvent
from app.services.continuity import check_scene_continuity
from app.services.research_service import process_scene_claims
from app.services.gemini import extract_plot_timeline, PlotTimelineResponse

logger = logging.getLogger("script_supervisor.parallel_processor")

def execute_scene_downstream_tasks_parallel(db: Session, project_id: str, scene: Scene) -> Dict[str, Any]:
    """
    Executes the 3 downstream AI tasks concurrently using a ThreadPoolExecutor capped at max_workers=3:
    1. Worker 1: Continuity Check (check_scene_continuity)
    2. Worker 2: Real-World Claim Extraction & Web Search (process_scene_claims)
    3. Worker 3: Plot Timeline Extraction (extract_plot_timeline)

    Strictly limits parallel API calls to at most 3 concurrent calls.
    """
    logger.info(f"Running parallel downstream analysis for scene #{scene.scene_number} (max_workers=3)")

    def task_continuity() -> List[Any]:
        with SessionLocal() as worker_db:
            try:
                return check_scene_continuity(worker_db, project_id, scene.id)
            except Exception as e:
                logger.error(f"Continuity check failed for scene #{scene.scene_number}: {e}", exc_info=True)
                return []

    def task_claims():
        with SessionLocal() as worker_db:
            try:
                worker_scene = worker_db.query(Scene).filter(Scene.id == scene.id).first()
                if worker_scene:
                    process_scene_claims(worker_db, project_id, worker_scene)
            except Exception as e:
                logger.warning(f"Notice on claim processing for scene #{scene.scene_number}: {e}")

    def task_timeline():
        with SessionLocal() as worker_db:
            try:
                prev_events = worker_db.query(PlotEvent).filter(
                    PlotEvent.project_id == project_id,
                    PlotEvent.scene_number < scene.scene_number
                ).order_by(PlotEvent.scene_number.asc()).all()
                
                prev_summary = "\n".join([f"Scene {pe.scene_number} ({pe.event_id}): {pe.title} - {pe.description}" for pe in prev_events])
                res: PlotTimelineResponse = extract_plot_timeline(scene.scene_number, scene.raw_text, prev_summary)
                
                for pe in res.plot_events:
                    existing_pe = worker_db.query(PlotEvent).filter(
                        PlotEvent.project_id == project_id,
                        PlotEvent.event_id == pe.event_id
                    ).first()
                    if not existing_pe:
                        pe_obj = PlotEvent(
                            project_id=project_id,
                            scene_id=scene.id,
                            event_id=pe.event_id,
                            scene_number=pe.scene_number,
                            title=pe.title,
                            description=pe.description,
                            track_type=pe.track_type,
                            track_name=pe.track_name,
                            importance_score=pe.importance_score,
                            excerpt=pe.excerpt,
                            connected_to_event=pe.connected_to_event,
                            connection_type=pe.connection_type
                        )
                        worker_db.add(pe_obj)
                worker_db.commit()
            except Exception as e:
                logger.warning(f"Notice on plot timeline extraction for scene #{scene.scene_number}: {e}")

    with ThreadPoolExecutor(max_workers=3) as executor:
        future_cont = executor.submit(task_continuity)
        future_claims = executor.submit(task_claims)
        future_timeline = executor.submit(task_timeline)

        detected_issues = future_cont.result()
        future_claims.result()
        future_timeline.result()

    return {"issues": detected_issues}
