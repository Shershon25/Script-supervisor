"""
Seed script to populate initial demo data for local development.
"""
import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.db.database import SessionLocal, engine, Base
from app.db.models import Project
from app.services.scene_processor import process_scene

def seed():
    print("Ensuring database tables exist...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Check if project already exists
        existing = db.query(Project).filter(Project.title == "The Last Call").first()
        if existing:
            print(f"Demo project 'The Last Call' already exists (ID: {existing.id})")
            project_id = existing.id
        else:
            project = Project(title="The Last Call")
            db.add(project)
            db.commit()
            db.refresh(project)
            project_id = project.id
            print(f"Created demo project 'The Last Call' (ID: {project_id})")

        # Add Scene 1 if not exists
        try:
            print("Processing Scene 1 demo...")
            process_scene(
                db=db,
                project_id=project_id,
                scene_number=1,
                raw_text="INT. JOHN'S APARTMENT - NIGHT\n\nJohn enters the apartment.\n\nHe looks at a photograph of his father."
            )
            print("Scene 1 processed successfully.")
        except Exception as e:
            print(f"Scene 1 notice: {e}")

        print("Seeding complete.")

    finally:
        db.close()

if __name__ == "__main__":
    seed()
