from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Scene, Project
from app.schemas.scene import SceneCreate, SceneUpdate, SceneResponse
from app.services.scene_processor import process_scene

from app.services.background_processor import run_previous_scene_analysis_background
from fastapi import BackgroundTasks

router = APIRouter(prefix="/api/projects/{project_id}/scenes", tags=["Scenes"])

@router.post("", status_code=status.HTTP_201_CREATED)
def create_and_save_scene(
    project_id: str,
    payload: SceneCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Creates/saves scene N quickly and triggers background AI evaluation for previous scene (N-1).
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")

    existing_scene = db.query(Scene).filter(
        Scene.project_id == project_id,
        Scene.scene_number == payload.scene_number
    ).first()

    if existing_scene:
        scene = existing_scene
        scene.raw_text = payload.raw_text
    else:
        scene = Scene(
            project_id=project_id,
            scene_number=payload.scene_number,
            raw_text=payload.raw_text
        )
        db.add(scene)
    db.commit()
    db.refresh(scene)

    # Schedule background analysis for previous scene (N - 1)
    if payload.scene_number > 1:
        background_tasks.add_task(
            run_previous_scene_analysis_background,
            project_id=project_id,
            previous_scene_number=payload.scene_number - 1
        )

    return {
        "scene": {
            "id": scene.id,
            "project_id": scene.project_id,
            "scene_number": scene.scene_number,
            "raw_text": scene.raw_text,
            "is_analyzed": scene.is_analyzed,
            "created_at": scene.created_at.isoformat(),
        }
    }


@router.post("/{scene_id}/analyze")
def analyze_scene_manually(
    project_id: str,
    scene_id: str,
    db: Session = Depends(get_db)
):
    """
    Manually triggers immediate scene analysis using the rate-limited parallel processor flow.
    """
    scene = db.query(Scene).filter(Scene.id == scene_id, Scene.project_id == project_id).first()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found.")

    return process_scene(db, project_id, scene.scene_number, scene.raw_text)


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


@router.delete("/{scene_id}")
def delete_scene(project_id: str, scene_id: str, db: Session = Depends(get_db)):
    """
    Deletes a scene and all its derived data (facts, events, relationships,
    knowledge states, issues, claims, research tasks) via cascade.
    Returns whether the deleted scene was the latest in the project.
    """
    scene = db.query(Scene).filter(Scene.id == scene_id, Scene.project_id == project_id).first()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found.")

    deleted_scene_number = scene.scene_number

    # Determine if this is the latest scene before deleting
    from sqlalchemy import func
    max_scene_number = db.query(func.max(Scene.scene_number))\
        .filter(Scene.project_id == project_id)\
        .scalar()
    is_latest = (deleted_scene_number == max_scene_number)

    db.delete(scene)
    db.commit()

    return {
        "status": "deleted",
        "scene_number": deleted_scene_number,
        "is_latest": is_latest,
    }


@router.post("/renumber", response_model=List[SceneResponse])
def renumber_scenes(project_id: str, db: Session = Depends(get_db)):
    """
    Compacts scene numbers after a mid-script deletion so there are no gaps
    (e.g. [1, 2, 4, 5] → [1, 2, 3, 4]).
    Also resets is_analyzed=False on all scenes so a full batch re-analysis
    will reprocess everything from scratch with correct numbering.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    scenes = db.query(Scene)\
        .filter(Scene.project_id == project_id)\
        .order_by(Scene.scene_number.asc())\
        .all()

    for new_number, scene in enumerate(scenes, start=1):
        scene.scene_number = new_number
        scene.is_analyzed = False

    db.commit()
    for scene in scenes:
        db.refresh(scene)

    return scenes
