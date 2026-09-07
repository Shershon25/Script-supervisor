import pytest
from app.db.models import Project, Scene, ProjectSettings
from app.services.project_settings import get_or_create_project_settings
from app.services.background_processor import run_previous_scene_analysis_background

def test_background_processor_disabled_setting(db_session):
    # 1. Create project & scene
    proj = Project(title="Background Test Project")
    db_session.add(proj)
    db_session.commit()

    s1 = Scene(project_id=proj.id, scene_number=1, raw_text="INT. ROOM - DAY\nJOHN sits.", is_analyzed=False)
    db_session.add(s1)
    db_session.commit()

    # 2. Disable auto background analysis
    settings = get_or_create_project_settings(db_session, proj.id)
    settings.auto_background_analysis_enabled = False
    db_session.commit()

    # 3. Run background processor
    run_previous_scene_analysis_background(proj.id, 1)

    # 4. Confirm scene 1 remains unanalyzed because setting was disabled
    db_session.refresh(s1)
    assert s1.is_analyzed is False

def test_scene_creation_endpoint_fast_response(client):
    # 1. Create project
    proj_res = client.post("/api/projects", json={"title": "Fast Scene Save Test"})
    assert proj_res.status_code == 201
    project_id = proj_res.json()["id"]

    # 2. Create Scene 1
    s1_res = client.post(f"/api/projects/{project_id}/scenes", json={"scene_number": 1, "raw_text": "INT. OFFICE - DAY\nJOHN is here."})
    assert s1_res.status_code == 201
    assert s1_res.json()["scene"]["scene_number"] == 1

    # 3. Create Scene 2 (triggers background analysis for Scene 1)
    s2_res = client.post(f"/api/projects/{project_id}/scenes", json={"scene_number": 2, "raw_text": "INT. HALLWAY - DAY\nJOHN walks."})
    assert s2_res.status_code == 201
    assert s2_res.json()["scene"]["scene_number"] == 2
