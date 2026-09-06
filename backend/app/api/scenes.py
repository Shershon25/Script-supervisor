from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Scene, Project
from app.schemas.scene import SceneCreate, SceneUpdate, SceneResponse
from app.services.scene_processor import process_scene

router = APIRouter(prefix="/api/projects/{project_id}/scenes", tags=["Scenes"])

@router.post("", status_code=status.HTTP_201_CREATED)
def analyze_and_create_scene(
    project_id: str,
    payload: SceneCreate,
    db: Session = Depends(get_db)
):
    """
    Submits a scene for AI analysis, validates structured output,
    persists Entities, Facts, and Events into CockroachDB/PostgreSQL,
    and returns the structured scene analysis result.
    """
    return process_scene(
        db=db,
        project_id=project_id,
        scene_number=payload.scene_number,
        raw_text=payload.raw_text
    )


@router.put("/{scene_id}", response_model=SceneResponse)
def update_scene_text(
    project_id: str,
    scene_id: str,
    payload: SceneUpdate,
    db: Session = Depends(get_db)
):
    """Updates raw text of a scene in database without re-running full AI analysis."""
    scene = db.query(Scene).filter(Scene.id == scene_id, Scene.project_id == project_id).first()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found.")

    scene.raw_text = payload.raw_text
    db.commit()
    db.refresh(scene)
    return scene


@router.get("", response_model=List[SceneResponse])
def list_scenes(project_id: str, db: Session = Depends(get_db)):
    """Lists all scenes in a project ordered by scene number."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    scenes = db.query(Scene)\
        .filter(Scene.project_id == project_id)\
        .order_by(Scene.scene_number.asc())\
        .all()

    # Dynamic fallback check for scenes analyzed in sample/demo projects
    from app.db.models import PlotEvent, SceneAnalysisRun
    analyzed_scene_numbers = set(
        pe[0] for pe in db.query(PlotEvent.scene_number).filter(PlotEvent.project_id == project_id).all()
    )
    analyzed_scene_ids = set(
        sar[0] for sar in db.query(SceneAnalysisRun.scene_id).filter(SceneAnalysisRun.project_id == project_id, SceneAnalysisRun.status == "COMPLETED").all()
    )

    for sc in scenes:
        if not sc.is_analyzed:
            if sc.scene_number in analyzed_scene_numbers or sc.id in analyzed_scene_ids:
                sc.is_analyzed = True

    return scenes
