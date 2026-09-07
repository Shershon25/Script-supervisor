import pytest
from fastapi.testclient import TestClient

def test_hybrid_retrieval_and_provenance(client):
    proj_res = client.post("/api/projects", json={"title": "Day 6 Retrieval Test"})
    assert proj_res.status_code == 201
    project_id = proj_res.json()["id"]

    # Scene 1: John lives in Chennai
    res1 = client.post(f"/api/projects/{project_id}/scenes", json={
        "scene_number": 1,
        "raw_text": "INT. APARTMENT - NIGHT\nJohn lives in Chennai.\nJohn receives a camera from his father."
    })
    assert res1.status_code == 201
    s1_id = res1.json()["scene"]["id"]
    client.post(f"/api/projects/{project_id}/scenes/{s1_id}/analyze")

    # Scene 2: John travels to Mumbai
    res2 = client.post(f"/api/projects/{project_id}/scenes", json={
        "scene_number": 2,
        "raw_text": "INT. STATION - DAY\nJohn travels from Chennai to Mumbai."
    })
    assert res2.status_code == 201
    s2_id = res2.json()["scene"]["id"]

    # Test Context Retrieval endpoint for Scene 2
    ret_res = client.post(f"/api/projects/{project_id}/retrieve-context", json={
        "scene_id": s2_id,
        "task_type": "CONTINUITY",
        "entity_names": ["John", "Camera"]
    })
    assert ret_res.status_code == 200
    ret_data = ret_res.json()

    assert ret_data["project_id"] == project_id
    assert ret_data["scene_id"] == s2_id
    assert ret_data["total_retrieved"] >= 1

    tags = [item["provenance_tag"] for item in ret_data["items"]]
    assert any("[FACT" in t or "[EVENT" in t or "[SCENE" in t for t in tags)


def test_targeted_reasoning_endpoint(client):
    proj_res = client.post("/api/projects", json={"title": "Day 6 Reasoning Test"})
    assert proj_res.status_code == 201
    project_id = proj_res.json()["id"]

    res1 = client.post(f"/api/projects/{project_id}/scenes", json={
        "scene_number": 1,
        "raw_text": "INT. APARTMENT - NIGHT\nJohn lives in Chennai."
    })
    s1_id = res1.json()["scene"]["id"]

    reason_res = client.post(f"/api/projects/{project_id}/reason", json={
        "scene_id": s1_id,
        "task_type": "CONTINUITY",
        "target_entity_names": ["John"]
    })
    assert reason_res.status_code == 200
    r_data = reason_res.json()

    assert "task_type" in r_data
    assert "verdict" in r_data
    assert "reasoning_summary" in r_data


def test_project_isolation_in_retrieval(client):
    p1 = client.post("/api/projects", json={"title": "Project A"}).json()["id"]
    p2 = client.post("/api/projects", json={"title": "Project B"}).json()["id"]

    res1 = client.post(f"/api/projects/{p1}/scenes", json={
        "scene_number": 1,
        "raw_text": "INT. ROOM - NIGHT\nSecret code is 12345."
    })
    s1_id = res1.json()["scene"]["id"]

    res2 = client.post(f"/api/projects/{p2}/scenes", json={
        "scene_number": 1,
        "raw_text": "INT. OTHER ROOM - NIGHT\nNothing here."
    })
    s2_id = res2.json()["scene"]["id"]

    # Try retrieving context for Project B scene
    ret_b = client.post(f"/api/projects/{p2}/retrieve-context", json={
        "scene_id": s2_id,
        "task_type": "CONTINUITY"
    }).json()

    contents = [item["content"] for item in ret_b["items"]]
    assert not any("12345" in c for c in contents)
