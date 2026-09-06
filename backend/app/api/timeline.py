import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Project, Scene, PlotEvent
from app.schemas.timeline import PlotEventItem, TimelineViewResponse
from app.services.gemini import extract_plot_timeline

import re

logger = logging.getLogger("script_supervisor.api.timeline")

router = APIRouter(prefix="/api/projects/{project_id}/timeline", tags=["Timeline"])


@router.get("", response_model=TimelineViewResponse)
def get_timeline(project_id: str, db: Session = Depends(get_db)):
    """
    Returns the extracted plot timeline events and track names for a project.
    If no timeline events exist yet, automatically runs extraction on the project's scenes.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    events = db.query(PlotEvent)\
        .filter(PlotEvent.project_id == project_id)\
        .order_by(PlotEvent.scene_number.asc(), PlotEvent.created_at.asc())\
        .all()

    if not events:
        return TimelineViewResponse(
            project_id=project_id,
            events=[],
            tracks=[]
        )

    items = []
    for e in events:
        conn_event = e.connected_to_event if e.connected_to_event and str(e.connected_to_event).lower() not in ("null", "none", "") else None
        conn_type = e.connection_type if e.connection_type and str(e.connection_type).lower() not in ("null", "none", "") else None
        
        items.append(
            PlotEventItem(
                event_id=e.event_id,
                scene_number=e.scene_number,
                title=e.title,
                description=e.description,
                track_type=e.track_type,
                track_name=e.track_name,
                importance_score=e.importance_score,
                excerpt=e.excerpt,
                connected_to_event=conn_event,
                connection_type=conn_type
            )
        )

    tracks = list(dict.fromkeys([e.track_name for e in items if e.track_name]))

    return TimelineViewResponse(
        project_id=project_id,
        events=items,
        tracks=tracks
    )


@router.post("/extract", response_model=TimelineViewResponse)
def extract_project_timeline(project_id: str, db: Session = Depends(get_db)):
    """
    Runs structural plot & subplot event extraction across all screenplay scenes in the project.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    scenes = db.query(Scene)\
        .filter(Scene.project_id == project_id)\
        .order_by(Scene.scene_number.asc())\
        .all()

    if not scenes:
        return TimelineViewResponse(project_id=project_id, events=[], tracks=[])

    # Remove prior timeline events for fresh extraction run
    db.query(PlotEvent).filter(PlotEvent.project_id == project_id).delete()
    db.commit()

    all_extracted_items: List[PlotEventItem] = []
    previous_summary = ""

    for scene in scenes:
        extracted_resp = extract_plot_timeline(
            scene_number=scene.scene_number,
            scene_text=scene.raw_text,
            previous_events_summary=previous_summary
        )

        for item in extracted_resp.plot_events:
            conn_event = item.connected_to_event if item.connected_to_event and str(item.connected_to_event).lower() not in ("null", "none", "") else None
            conn_type = item.connection_type if item.connection_type and str(item.connection_type).lower() not in ("null", "none", "") else None

            db_event = PlotEvent(
                project_id=project_id,
                scene_id=scene.id,
                event_id=item.event_id,
                scene_number=item.scene_number,
                title=item.title,
                description=item.description,
                track_type=item.track_type,
                track_name=item.track_name,
                importance_score=item.importance_score,
                excerpt=item.excerpt,
                connected_to_event=conn_event,
                connection_type=conn_type
            )
            db.add(db_event)
            
            clean_item = PlotEventItem(
                event_id=item.event_id,
                scene_number=item.scene_number,
                title=item.title,
                description=item.description,
                track_type=item.track_type,
                track_name=item.track_name,
                importance_score=item.importance_score,
                excerpt=item.excerpt,
                connected_to_event=conn_event,
                connection_type=conn_type
            )
            all_extracted_items.append(clean_item)

            previous_summary += f"- [{item.event_id}] (Scene {item.scene_number}, Track: '{item.track_name}'): {item.title} — {item.description}\n"

    db.commit()

    tracks = list(dict.fromkeys([item.track_name for item in all_extracted_items if item.track_name]))

    return TimelineViewResponse(
        project_id=project_id,
        events=all_extracted_items,
        tracks=tracks
    )

