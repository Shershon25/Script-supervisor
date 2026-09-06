from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Project, Scene
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse

router = APIRouter(prefix="/api/projects", tags=["Projects"])

SAMPLE_SCENES = [
    (1, "INT. JOHN'S APARTMENT - NIGHT\n\nJohn enters his apartment.\n\nHe looks at a photograph of his father.\n\nJohn owns a red Mustang.\n\nJohn lives in Chennai."),
    (2, "EXT. CEMETERY - DAY\n\nJohn stands beside his father's grave.\n\nHis father died in 2015."),
    (3, "INT. DINER - NIGHT\n\nJohn meets Sarah.\n\nSarah gives John a water-damaged Polaroid 600 of Waterfront Pier 19."),
    (4, "EXT. CHENNAI HIGHWAY - DAY\n\nJohn travels from Chennai to Mumbai."),
    (5, "INT. MUMBAI CAFE - NIGHT\n\nSarah meets Mike.\n\nSarah discovers that Waterfront Pier 19 was sealed three weeks ago.\n\nTeleportation device exists in this world."),
    (6, "INT. MUMBAI APARTMENT - NIGHT\n\nJohn says: I live in Mumbai now."),
    (7, "INT. ALLEY - NIGHT\n\nJohn secretly obtains a duplicate key to the pier."),
    (8, "INT. WAREHOUSE - NIGHT\n\nSarah hides the photograph in a steel lockbox."),
    (9, "INT. OFFICE - DAY\n\nSarah tells Mike about the photograph."),
    (10, "INT. HOTEL - NIGHT\n\nSarah tells John that the meeting was cancelled."),
    (11, "INT. CAFE - DAY\n\nJohn receives a telegram."),
    (12, "INT. APARTMENT - NIGHT\n\nJohn looks at the Polaroid of Waterfront Pier 19."),
    (13, "EXT. DOCK - NIGHT\n\nMike investigates the waterfront warehouse."),
    (14, "INT. POLICE STATION - INTERROGATION ROOM - NIGHT\n\nJohn sits alone under the humming fluorescents. Metal table bolted to the concrete floor. The cold air smells of burnt coffee and damp dust.\n\nJOHN\nI didn't do it. You have nothing on me.\n\nSarah enters, shutting the heavy iron door with a deafening latch.\n\nSARAH\nThen explain this.\n\nShe pulls a water-damaged 4x6 print from an evidence envelope and slams it face-up between them.\n\nJohn freezes. His eyes dart across the faded Polaroid of the waterfront warehouse.\n\nJOHN\nWhere did you find this? The pier was sealed three weeks ago.\n\nSarah doesn't flinch. She leans over the table, hands planted flat."),
    (15, "EXT. HIGHWAY - NIGHT\n\nJohn drives his blue Mustang through the rain.")
]

from app.services.project_settings import get_or_create_project_settings

@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_new_project(project_in: ProjectCreate, db: Session = Depends(get_db)):
    """Creates a new screenplay project."""
    project = Project(title=project_in.title.strip())
    db.add(project)
    db.commit()
    db.refresh(project)
    get_or_create_project_settings(db, project.id)
    return project

@router.get("", response_model=List[ProjectResponse])
def get_all_projects(db: Session = Depends(get_db)):
    """Lists all active screenplay projects."""
    return db.query(Project).order_by(Project.created_at.desc()).all()

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project_by_id(project_id: str, db: Session = Depends(get_db)):
    """Gets details for a single project by ID."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found."
        )
    return project

@router.post("/seed-demo", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def seed_demo_project(db: Session = Depends(get_db)):
    """
    Seeds the official hackathon demo project 'The Last Signal' pre-populated with 15 sample scenes.
    """
    title = "The Last Signal (Official Demo)"
    
    # Check if existing sample project exists
    existing = db.query(Project).filter(Project.title == title).first()
    if existing:
        return existing

    project = Project(title=title)
    db.add(project)
    db.flush()

    for scene_num, raw_text in SAMPLE_SCENES:
        scene = Scene(
            project_id=project.id,
            scene_number=scene_num,
            raw_text=raw_text
        )
        db.add(scene)

    db.commit()
    db.refresh(project)
    get_or_create_project_settings(db, project.id)
    return project

@router.put("/{project_id}", response_model=ProjectResponse)
def rename_project(
    project_id: str,
    project_in: ProjectUpdate,
    db: Session = Depends(get_db)
):
    """Renames an existing screenplay project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found."
        )

    clean_title = project_in.title.strip()
    if not clean_title:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project title cannot be empty."
        )

    project.title = clean_title
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_200_OK)
def delete_project_by_id(project_id: str, db: Session = Depends(get_db)):
    """Deletes a project and all associated screenplay data."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found."
        )
    db.delete(project)
    db.commit()
    return {"status": "success", "message": f"Project '{project.title}' deleted successfully."}

