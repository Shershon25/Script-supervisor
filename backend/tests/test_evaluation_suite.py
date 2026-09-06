import pytest

def test_eval_object_ownership_conflict(client):
    proj = client.post("/api/projects", json={"title": "Eval Ownership"}).json()
    p_id = proj["id"]

    sc1 = client.post(f"/api/projects/{p_id}/scenes", json={
        "scene_number": 1, "raw_text": "INT. ROOM - DAY\nJohn possesses the unique ancient artifact."
    }).json()["scene"]

    sc2 = client.post(f"/api/projects/{p_id}/scenes", json={
        "scene_number": 2, "raw_text": "INT. GARAGE - DAY\nSarah possesses the unique ancient artifact."
    }).json()["scene"]

    res = client.post(f"/api/projects/{p_id}/scenes/{sc2['id']}/analyze").json()
    assert res["status"] in ("COMPLETED", "PARTIAL")


def test_eval_character_knowledge_gap(client):
    proj = client.post("/api/projects", json={"title": "Eval Knowledge"}).json()
    p_id = proj["id"]

    sc1 = client.post(f"/api/projects/{p_id}/scenes", json={
        "scene_number": 1, "raw_text": "INT. OFFICE - DAY\nSarah learns that the meeting is cancelled."
    }).json()["scene"]

    sc2 = client.post(f"/api/projects/{p_id}/scenes", json={
        "scene_number": 2, "raw_text": "INT. HOME - NIGHT\nJohn reacts to the cancelled meeting."
    }).json()["scene"]

    res = client.post(f"/api/projects/{p_id}/scenes/{sc2['id']}/analyze").json()
    assert res["status"] in ("COMPLETED", "PARTIAL")


def test_eval_intentional_decision_suppression(client):
    proj = client.post("/api/projects", json={"title": "Eval Intentional"}).json()
    p_id = proj["id"]

    sc1 = client.post(f"/api/projects/{p_id}/scenes", json={
        "scene_number": 1, "raw_text": "INT. ROOM - DAY\nJohn lives in Chennai."
    }).json()["scene"]

    sc2 = client.post(f"/api/projects/{p_id}/scenes", json={
        "scene_number": 2, "raw_text": "INT. ROOM - NIGHT\nJohn lives in Delhi."
    }).json()["scene"]

    # Initial analysis produces issue
    res1 = client.post(f"/api/projects/{p_id}/scenes/{sc2['id']}/analyze").json()
    issues = client.get(f"/api/projects/{p_id}/issues").json()
    assert len(issues) >= 1

    # Mark issue INTENTIONAL
    issue_id = issues[0]["id"]
    rev_res = client.post(f"/api/projects/{p_id}/issues/{issue_id}/review", json={
        "action": "ACCEPT",
        "resolution_type": "INTENTIONAL",
        "note": "John moves frequently"
    })
    assert rev_res.status_code == 200

    # Re-analyze Scene 2 -> issue should remain suppressed (status ACCEPTED/IGNORED)
    res2 = client.post(f"/api/projects/{p_id}/scenes/{sc2['id']}/analyze").json()
    open_issues = client.get(f"/api/projects/{p_id}/issues?status=OPEN").json()
    assert not any(i["id"] == issue_id for i in open_issues)


def test_eval_long_range_retrieval(client):
    proj = client.post("/api/projects", json={"title": "Eval Long-Range"}).json()
    p_id = proj["id"]

    sc2 = client.post(f"/api/projects/{p_id}/scenes", json={
        "scene_number": 2, "raw_text": "INT. DINER - NIGHT\nSarah gives John a photograph."
    }).json()["scene"]

    # Add intermediate scenes
    for i in range(3, 10):
        client.post(f"/api/projects/{p_id}/scenes", json={
            "scene_number": i, "raw_text": f"INT. LOCATION {i} - DAY\nJohn walks alone."
        })

    sc10 = client.post(f"/api/projects/{p_id}/scenes", json={
        "scene_number": 10, "raw_text": "INT. APARTMENT - NIGHT\nJohn destroys the photograph."
    }).json()["scene"]

    ret_res = client.post(f"/api/projects/{p_id}/retrieve-context", json={
        "scene_id": sc10["id"], "task_type": "CONTINUITY", "entity_names": ["John", "Photograph"]
    }).json()

    assert ret_res["total_retrieved"] >= 1


def test_eval_project_isolation(client):
    p1 = client.post("/api/projects", json={"title": "Project Alpha"}).json()["id"]
    p2 = client.post("/api/projects", json={"title": "Project Beta"}).json()["id"]

    client.post(f"/api/projects/{p1}/scenes", json={
        "scene_number": 1, "raw_text": "INT. VAULT - NIGHT\nPasscode is 9999."
    })
    sc_b = client.post(f"/api/projects/{p2}/scenes", json={
        "scene_number": 1, "raw_text": "INT. OTHER VAULT - NIGHT\nNothing here."
    }).json()["scene"]

    ret_b = client.post(f"/api/projects/{p2}/retrieve-context", json={
        "scene_id": sc_b["id"], "task_type": "CONTINUITY"
    }).json()

    contents = [item["content"] for item in ret_b["items"]]
    assert not any("9999" in c for c in contents)
