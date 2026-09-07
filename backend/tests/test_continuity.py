import pytest
from fastapi.testclient import TestClient

def test_fact_residence_conflict(client):
    proj_res = client.post("/api/projects", json={"title": "Fact Conflict Test"})
    assert proj_res.status_code == 201
    project_id = proj_res.json()["id"]

    # Scene 1: John lives in Chennai
    res1 = client.post(f"/api/projects/{project_id}/scenes", json={
        "scene_number": 1,
        "raw_text": "John lives in Chennai."
    })
    assert res1.status_code == 201
    s1_id = res1.json()["scene"]["id"]
    client.post(f"/api/projects/{project_id}/scenes/{s1_id}/analyze")

    # Scene 2: John lives in Delhi (without move event)
    res2 = client.post(f"/api/projects/{project_id}/scenes", json={
        "scene_number": 2,
        "raw_text": "John lives in Delhi."
    })
    assert res2.status_code == 201
    s2_id = res2.json()["scene"]["id"]
    data2 = client.post(f"/api/projects/{project_id}/scenes/{s2_id}/analyze").json()
    assert "issues" in data2
    assert len(data2["issues"]) >= 1

    issue = data2["issues"][0]
    assert issue["issue_type"] in ("FACT_CONFLICT", "LOCATION_CONFLICT")
    assert issue["severity"] in ("WARNING", "ERROR")
    assert len(issue["evidence"]) >= 2


def test_explained_location_change_no_conflict(client):
    proj_res = client.post("/api/projects", json={"title": "Explained Travel Test"})
    assert proj_res.status_code == 201
    project_id = proj_res.json()["id"]

    # Scene 1: John in Chennai
    res1 = client.post(f"/api/projects/{project_id}/scenes", json={
        "scene_number": 1,
        "raw_text": "INT. CHENNAI APARTMENT - NIGHT\nJohn enters the apartment in Chennai."
    })
    client.post(f"/api/projects/{project_id}/scenes/{res1.json()['scene']['id']}/analyze")

    # Scene 2: John travels to Mumbai
    res2 = client.post(f"/api/projects/{project_id}/scenes", json={
        "scene_number": 2,
        "raw_text": "EXT. HIGHWAY - DAY\nJohn travels from Chennai to Mumbai."
    })
    client.post(f"/api/projects/{project_id}/scenes/{res2.json()['scene']['id']}/analyze")

    # Scene 3: John in Mumbai
    res3 = client.post(f"/api/projects/{project_id}/scenes", json={
        "scene_number": 3,
        "raw_text": "INT. MUMBAI CAFE - NIGHT\nJohn enters the cafe in Mumbai."
    })
    assert res3.status_code == 201
    s3_id = res3.json()["scene"]["id"]
    data3 = client.post(f"/api/projects/{project_id}/scenes/{s3_id}/analyze").json()
    location_issues = [i for i in data3.get("issues", []) if i["issue_type"] == "LOCATION_CONFLICT"]
    assert len(location_issues) == 0


def test_knowledge_transfer_no_conflict(client):
    proj_res = client.post("/api/projects", json={"title": "Knowledge Transfer Test"})
    assert proj_res.status_code == 201
    project_id = proj_res.json()["id"]

    # Scene 1: Sarah kills Michael
    res1 = client.post(f"/api/projects/{project_id}/scenes", json={
        "scene_number": 1,
        "raw_text": "INT. WAREHOUSE - NIGHT\nSarah kills Michael."
    })
    client.post(f"/api/projects/{project_id}/scenes/{res1.json()['scene']['id']}/analyze")

    # Scene 2: Sarah tells John
    res2 = client.post(f"/api/projects/{project_id}/scenes", json={
        "scene_number": 2,
        "raw_text": "INT. CAFE - DAY\nSarah tells John that she killed Michael."
    })
    client.post(f"/api/projects/{project_id}/scenes/{res2.json()['scene']['id']}/analyze")

    # Scene 3: John tells police he knows
    res3 = client.post(f"/api/projects/{project_id}/scenes", json={
        "scene_number": 3,
        "raw_text": "INT. POLICE STATION - DAY\nJohn tells the detective that Sarah killed Michael."
    })
    assert res3.status_code == 201
    s3_id = res3.json()["scene"]["id"]
    data3 = client.post(f"/api/projects/{project_id}/scenes/{s3_id}/analyze").json()
    knowledge_issues = [i for i in data3.get("issues", []) if i["issue_type"] == "KNOWLEDGE_CONFLICT"]
    assert len(knowledge_issues) == 0


def test_day3_10_scene_acceptance_scenario(client):
    proj_res = client.post("/api/projects", json={"title": "Day 3 10-Scene Acceptance Test"})
    assert proj_res.status_code == 201
    project_id = proj_res.json()["id"]

    scenes_data = [
        (1, "INT. JOHN'S APARTMENT - NIGHT\nJohn lives in Chennai.\nJohn keeps a gun in his desk drawer."),
        (2, "EXT. CHENNAI STREET - DAY\nJohn leaves his apartment."),
        (3, "EXT. TRAIN STATION - DAY\nJohn travels to Mumbai."),
        (4, "INT. MUMBAI HOTEL - NIGHT\nJohn checks into a hotel in Mumbai."),
        (5, "INT. MUMBAI HOTEL - MORNING\nJohn lives in Chennai."),
        (6, "INT. MUMBAI APARTMENT - NIGHT\nJohn lives in Delhi."),
        (7, "INT. MUMBAI APARTMENT - NIGHT\nSarah takes John's gun.\nShe now owns the gun."),
        (8, "INT. POLICE STATION - DAY\nJohn tells the detective: Sarah killed Michael."),
        (9, "INT. MUMBAI APARTMENT - NIGHT\nSarah tells John: I killed Michael."),
        (10, "INT. POLICE STATION - DAY\nJohn tells the detective: Sarah killed Michael.")
    ]

    for num, text in scenes_data:
        res = client.post(f"/api/projects/{project_id}/scenes", json={"scene_number": num, "raw_text": text})
        assert res.status_code == 201
        s_id = res.json()["scene"]["id"]
        client.post(f"/api/projects/{project_id}/scenes/{s_id}/analyze")

    # Query all issues for project
    issues_res = client.get(f"/api/projects/{project_id}/issues")
    assert issues_res.status_code == 200
    issues = issues_res.json()

    assert len(issues) >= 1
    issue_types = [i["issue_type"] for i in issues]
    assert "OBJECT_OWNERSHIP_CONFLICT" in issue_types or "KNOWLEDGE_CONFLICT" in issue_types or "FACT_CONFLICT" in issue_types or "LOCATION_CONFLICT" in issue_types
