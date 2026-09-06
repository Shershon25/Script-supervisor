import pytest
from fastapi.testclient import TestClient

def test_claim_classification_types(client):
    proj_res = client.post("/api/projects", json={"title": "Day 5 Claim Test"})
    assert proj_res.status_code == 201
    project_id = proj_res.json()["id"]

    # Scene 1: Real world claim & fictional rule
    res1 = client.post(f"/api/projects/{project_id}/scenes", json={
        "scene_number": 1,
        "raw_text": "INT. LAB - NIGHT\nIn 2040, teleportation is legal.\nThe police introduced facial recognition in 2014."
    })
    assert res1.status_code == 201

    claims_res = client.get(f"/api/projects/{project_id}/claims")
    assert claims_res.status_code == 200
    claims = claims_res.json()
    assert len(claims) >= 1

    claim_types = [c["claim_type"] for c in claims]
    assert "REAL_WORLD_CLAIM" in claim_types or "FICTIONAL_WORLD_RULE" in claim_types


def test_research_execution_and_deduplication(client):
    proj_res = client.post("/api/projects", json={"title": "Research Exec Test"})
    assert proj_res.status_code == 201
    project_id = proj_res.json()["id"]

    # Scene with real world claim
    res1 = client.post(f"/api/projects/{project_id}/scenes", json={
        "scene_number": 1,
        "raw_text": "INT. APARTMENT - NIGHT\nJohn drove from Pune to Mumbai in twenty minutes."
    })
    assert res1.status_code == 201

    claims_res = client.get(f"/api/projects/{project_id}/claims?claim_type=REAL_WORLD_CLAIM")
    assert claims_res.status_code == 200
    claims = claims_res.json()
    assert len(claims) >= 1
    claim = claims[0]

    # Trigger Research Task
    r_res1 = client.post(f"/api/projects/{project_id}/claims/{claim['id']}/research")
    assert r_res1.status_code == 200
    task1 = r_res1.json()
    assert task1["status"] == "ok"
    assert "task_id" in task1
    assert task1["verdict"] in ("CONTRADICTED", "LIKELY_TRUE", "VERIFIED")

    # Trigger again (without force refresh) -> Should reuse task
    r_res2 = client.post(f"/api/projects/{project_id}/claims/{claim['id']}/research")
    assert r_res2.status_code == 200
    assert r_res2.json()["task_id"] == task1["task_id"]


def test_get_research_task_detail(client):
    proj_res = client.post("/api/projects", json={"title": "Task Detail Test"})
    assert proj_res.status_code == 201
    project_id = proj_res.json()["id"]

    client.post(f"/api/projects/{project_id}/scenes", json={
        "scene_number": 1,
        "raw_text": "INT. STATION - NIGHT\nMumbai Central was operational in 2018."
    })

    claims = client.get(f"/api/projects/{project_id}/claims").json()
    claim_id = claims[0]["id"]

    task_res = client.post(f"/api/projects/{project_id}/claims/{claim_id}/research").json()
    task_id = task_res["task_id"]

    detail_res = client.get(f"/api/projects/{project_id}/research/{task_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["id"] == task_id
    assert detail["status"] == "COMPLETED"
    assert len(detail["sources"]) >= 1
    assert detail["evaluation"]["verdict"] in ("VERIFIED", "LIKELY_TRUE", "CONTRADICTED")
