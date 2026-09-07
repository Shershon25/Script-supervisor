import pytest
from fastapi.testclient import TestClient

def test_issue_review_lifecycle_and_history(client):
    # 1. Create project & conflicting scenes
    proj_res = client.post("/api/projects", json={"title": "Issue Review Test"})
    assert proj_res.status_code == 201
    project_id = proj_res.json()["id"]

    res1 = client.post(f"/api/projects/{project_id}/scenes", json={
        "scene_number": 1,
        "raw_text": "John lives in Chennai."
    })
    s1_id = res1.json()["scene"]["id"]
    client.post(f"/api/projects/{project_id}/scenes/{s1_id}/analyze")

    res2 = client.post(f"/api/projects/{project_id}/scenes", json={
        "scene_number": 2,
        "raw_text": "John lives in Delhi."
    })
    assert res2.status_code == 201
    s2_id = res2.json()["scene"]["id"]
    analyze_res = client.post(f"/api/projects/{project_id}/scenes/{s2_id}/analyze")
    assert analyze_res.status_code == 200
    issues = analyze_res.json().get("issues", [])
    assert len(issues) >= 1
    target_issue = issues[0]
    issue_id = target_issue["id"]

    # 2. Accept Issue
    accept_res = client.post(f"/api/projects/{project_id}/issues/{issue_id}/review", json={
        "action": "ACCEPT",
        "note": "Confirmed real continuity issue."
    })
    assert accept_res.status_code == 200
    assert accept_res.json()["issue"]["status"] == "ACCEPTED"

    # 3. Resolve Issue
    resolve_res = client.post(f"/api/projects/{project_id}/issues/{issue_id}/review", json={
        "action": "RESOLVE",
        "resolution_type": "INTENTIONAL",
        "note": "John moved to Delhi between Scene 1 and Scene 2."
    })
    assert resolve_res.status_code == 200
    updated_issue = resolve_res.json()["issue"]
    assert updated_issue["status"] == "RESOLVED"
    assert updated_issue["resolution_type"] == "INTENTIONAL"
    assert updated_issue["resolution_note"] == "John moved to Delhi between Scene 1 and Scene 2."

    # 4. Fetch Audit History
    history_res = client.get(f"/api/projects/{project_id}/issues/{issue_id}/history")
    assert history_res.status_code == 200
    history = history_res.json()
    assert len(history) == 2
    assert history[0]["action"] == "ACCEPT"
    assert history[1]["action"] == "RESOLVE"

    # 5. Reopen Issue
    reopen_res = client.post(f"/api/projects/{project_id}/issues/{issue_id}/review", json={
        "action": "REOPEN",
        "note": "Reopening after screenplay revision."
    })
    assert reopen_res.status_code == 200
    assert reopen_res.json()["issue"]["status"] == "OPEN"


def test_invalid_review_transition(client):
    proj_res = client.post("/api/projects", json={"title": "Invalid Transition Test"})
    assert proj_res.status_code == 201
    project_id = proj_res.json()["id"]

    res1 = client.post(f"/api/projects/{project_id}/scenes", json={"scene_number": 1, "raw_text": "John lives in Chennai."})
    s1_id = res1.json()["scene"]["id"]
    client.post(f"/api/projects/{project_id}/scenes/{s1_id}/analyze")

    res2 = client.post(f"/api/projects/{project_id}/scenes", json={"scene_number": 2, "raw_text": "John lives in Delhi."})
    s2_id = res2.json()["scene"]["id"]
    analyze_res = client.post(f"/api/projects/{project_id}/scenes/{s2_id}/analyze")
    issue_id = analyze_res.json()["issues"][0]["id"]

    # Resolve issue first
    client.post(f"/api/projects/{project_id}/issues/{issue_id}/review", json={
        "action": "RESOLVE",
        "resolution_type": "FIXED",
        "note": "Fixed text."
    })

    # Attempt to ACCEPT directly from RESOLVED without REOPEN -> Should fail with 409
    bad_res = client.post(f"/api/projects/{project_id}/issues/{issue_id}/review", json={
        "action": "ACCEPT"
    })
    assert bad_res.status_code == 409


def test_issue_summary_counts(client):
    proj_res = client.post("/api/projects", json={"title": "Summary Counts Test"})
    assert proj_res.status_code == 201
    project_id = proj_res.json()["id"]

    res1 = client.post(f"/api/projects/{project_id}/scenes", json={"scene_number": 1, "raw_text": "John lives in Chennai."})
    s1_id = res1.json()["scene"]["id"]
    client.post(f"/api/projects/{project_id}/scenes/{s1_id}/analyze")

    res2 = client.post(f"/api/projects/{project_id}/scenes", json={"scene_number": 2, "raw_text": "John lives in Delhi."})
    s2_id = res2.json()["scene"]["id"]
    analyze_res = client.post(f"/api/projects/{project_id}/scenes/{s2_id}/analyze")
    issue_id = analyze_res.json()["issues"][0]["id"]

    # Ignore issue
    client.post(f"/api/projects/{project_id}/issues/{issue_id}/review", json={
        "action": "IGNORE",
        "resolution_type": "FALSE_POSITIVE",
        "note": "False positive."
    })

    summary_res = client.get(f"/api/projects/{project_id}/issues/summary")
    assert summary_res.status_code == 200
    summary = summary_res.json()
    assert summary["total"] >= 1
    assert summary["ignored"] >= 1


def test_cross_project_issue_isolation(client):
    projA = client.post("/api/projects", json={"title": "Project A"}).json()
    projB = client.post("/api/projects", json={"title": "Project B"}).json()

    res1A = client.post(f"/api/projects/{projA['id']}/scenes", json={"scene_number": 1, "raw_text": "John lives in Chennai."})
    s1A_id = res1A.json()["scene"]["id"]
    client.post(f"/api/projects/{projA['id']}/scenes/{s1A_id}/analyze")

    resA = client.post(f"/api/projects/{projA['id']}/scenes", json={"scene_number": 2, "raw_text": "John lives in Delhi."})
    sA_id = resA.json()["scene"]["id"]
    analyzeA = client.post(f"/api/projects/{projA['id']}/scenes/{sA_id}/analyze")
    issueA_id = analyzeA.json()["issues"][0]["id"]

    # Attempt to review Project A's issue using Project B's URL path -> Should fail with 404
    bad_cross = client.post(f"/api/projects/{projB['id']}/issues/{issueA_id}/review", json={
        "action": "IGNORE"
    })
    assert bad_cross.status_code == 404
