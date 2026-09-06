"""
CLI script to reset database scenes, entities, facts, events, relationships, knowledge states, and issues
while preserving project definitions (or optionally resetting a specific project).
"""
import sys
import argparse
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.db.database import SessionLocal, engine
from app.db.models import Project, Scene, Entity, Fact, Event, Relationship, KnowledgeState, Issue

def reset_db(project_id: str = None, include_projects: bool = False):
    db = SessionLocal()
    try:
        if project_id:
            print(f"Resetting scenes & story data for project ID '{project_id}'...")
            db.query(Issue).filter(Issue.project_id == project_id).delete(synchronize_session=False)
            db.query(KnowledgeState).filter(KnowledgeState.project_id == project_id).delete(synchronize_session=False)
            db.query(Relationship).filter(Relationship.project_id == project_id).delete(synchronize_session=False)
            db.query(Fact).filter(Fact.project_id == project_id).delete(synchronize_session=False)

            scene_ids = [s.id for s in db.query(Scene.id).filter(Scene.project_id == project_id).all()]
            if scene_ids:
                db.query(Event).filter(Event.scene_id.in_(scene_ids)).delete(synchronize_session=False)

            db.query(Entity).filter(Entity.project_id == project_id).delete(synchronize_session=False)
            db.query(Scene).filter(Scene.project_id == project_id).delete(synchronize_session=False)

            if include_projects:
                db.query(Project).filter(Project.id == project_id).delete(synchronize_session=False)

            db.commit()
            print(f"Successfully reset project '{project_id}'.")
        else:
            print("Resetting all scenes and story data across all projects...")
            db.query(Issue).delete()
            db.query(KnowledgeState).delete()
            db.query(Relationship).delete()
            db.query(Fact).delete()
            db.query(Event).delete()
            db.query(Entity).delete()
            db.query(Scene).delete()

            if include_projects:
                db.query(Project).delete()
                print("Deleted all Project records.")
            else:
                print("Preserved Project records.")

            db.commit()
            print("Successfully reset database.")
    except Exception as e:
        db.rollback()
        print(f"Error resetting database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reset Script Supervisor database.")
    parser.add_argument("--project-id", type=str, default=None, help="Optional project ID to reset")
    parser.add_argument("--include-projects", action="store_true", help="Delete Project definitions as well")
    args = parser.parse_args()

    reset_db(project_id=args.project_id, include_projects=args.include_projects)
