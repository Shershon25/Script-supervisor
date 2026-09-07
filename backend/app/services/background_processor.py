import logging
from app.db.database import SessionLocal
from app.db.models import Scene, ProjectSettings
from app.services.scene_processor import process_scene

logger = logging.getLogger("script_supervisor.background_processor")

def run_previous_scene_analysis_background(project_id: str, previous_scene_number: int):
    """
    Background Task triggered when a new scene N is added.
    Analyzes previous scene (N-1) in the background if auto_background_analysis_enabled is True.
    """
    logger.info(f"Background task triggered for previous scene #{previous_scene_number} in project '{project_id}'")

    with SessionLocal() as db:
        settings = db.query(ProjectSettings).filter(ProjectSettings.project_id == project_id).first()
        if settings and not settings.auto_background_analysis_enabled:
            logger.info(f"Auto background analysis disabled for project '{project_id}'. Skipping background evaluation.")
            return

        prev_scene = db.query(Scene).filter(
            Scene.project_id == project_id,
            Scene.scene_number == previous_scene_number
        ).first()

        if not prev_scene:
            logger.warning(f"Previous scene #{previous_scene_number} not found in project '{project_id}'. Skipping background analysis.")
            return

        if prev_scene.is_analyzed:
            logger.info(f"Previous scene #{previous_scene_number} is already analyzed. Skipping background re-analysis.")
            return

        try:
            logger.info(f"Starting background AI analysis for previous scene #{previous_scene_number}...")
            process_scene(db, project_id, prev_scene.scene_number, prev_scene.raw_text)
            logger.info(f"Background AI analysis completed successfully for previous scene #{previous_scene_number}.")
        except Exception as e:
            logger.error(f"Background AI analysis failed for previous scene #{previous_scene_number}: {e}", exc_info=True)
