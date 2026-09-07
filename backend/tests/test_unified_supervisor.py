import pytest

def test_unified_scene_analysis_pipeline(client):
    proj_res = client.post("/api/projects", json={"title": "Day 7 Unified Test"})
    assert proj_res.status_code == 201
    project_id = proj_res.json()["id"]

    # Scene 1: John lives in Chennai
    sc1_res = client.post(f"/api/projects/{project_id}/scenes", json={
        "scene_number": 1,
        "raw_text": "INT. APARTMENT - NIGHT\nJohn lives in Chennai."
    })
    assert sc1_res.status_code == 201
    sc1_id = sc1_res.json()["scene"]["id"]

    # Trigger Unified Analysis for Scene 1
    u1_res = client.post(f"/api/projects/{project_id}/scenes/{sc1_id}/analyze")
    assert u1_res.status_code == 200
    u1_data = u1_res.json()

    assert u1_data["scene"]["project_id"] == project_id
    assert u1_data["scene"]["id"] == sc1_id
    assert u1_data["scene"]["scene_number"] == 1
    assert "analysis" in u1_data
    assert "story_state" in u1_data


def test_unified_analysis_idempotency(client):
    proj_res = client.post("/api/projects", json={"title": "Day 7 Idempotency Test"})
    project_id = proj_res.json()["id"]

    sc1_res = client.post(f"/api/projects/{project_id}/scenes", json={
        "scene_number": 1,
        "raw_text": "INT. ROOM - DAY\nJohn has a red car."
    })
    sc1_id = sc1_res.json()["scene"]["id"]

    # Process twice
    r1 = client.post(f"/api/projects/{project_id}/scenes/{sc1_id}/analyze").json()
    r2 = client.post(f"/api/projects/{project_id}/scenes/{sc1_id}/analyze").json()

    assert "scene" in r1
    assert "scene" in r2
    assert r1["scene"]["id"] == r2["scene"]["id"]


def test_historical_boundary_preservation(client):
    proj_res = client.post("/api/projects", json={"title": "Day 7 Boundary Test"})
    project_id = proj_res.json()["id"]

    # Scene 1: John in Chennai
    sc1 = client.post(f"/api/projects/{project_id}/scenes", json={
        "scene_number": 1,
        "raw_text": "John lives in Chennai."
    }).json()["scene"]
    client.post(f"/api/projects/{project_id}/scenes/{sc1['id']}/analyze")

    # Scene 2: John in Delhi
    sc2 = client.post(f"/api/projects/{project_id}/scenes", json={
        "scene_number": 2,
        "raw_text": "John lives in Delhi."
    }).json()["scene"]

    u2_res = client.post(f"/api/projects/{project_id}/scenes/{sc2['id']}/analyze")
    assert u2_res.status_code == 200
    u2_data = u2_res.json()

    assert len(u2_data["issues"]) >= 1
