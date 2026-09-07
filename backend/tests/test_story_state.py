import pytest
from fastapi.testclient import TestClient

def test_empty_story_state(client):
    proj_res = client.post("/api/projects", json={"title": "Empty Story State Test"})
    assert proj_res.status_code == 201
    project_id = proj_res.json()["id"]

    res = client.get(f"/api/projects/{project_id}/story-state")
    assert res.status_code == 200
    data = res.json()
    assert data["project_id"] == project_id
    assert data["characters"] == []
    assert data["locations"] == []
    assert data["objects"] == []
    assert data["facts"] == []
    assert data["events"] == []
    assert data["relationships"] == []
    assert data["knowledge_states"] == []

def test_day2_5_scene_acceptance_scenario(client):
    # 1. Create project
    proj_res = client.post("/api/projects", json={"title": "Day 2 5-Scene Acceptance Test"})
    assert proj_res.status_code == 201
    project_id = proj_res.json()["id"]

    # Scene 1: John in apartment, lives in Chennai
    scene1_text = "INT. JOHN'S APARTMENT - NIGHT\n\nJohn enters his apartment.\n\nHe looks at a photograph of his father.\n\nJohn lives in Chennai."
    res1 = client.post(f"/api/projects/{project_id}/scenes", json={"scene_number": 1, "raw_text": scene1_text})
    assert res1.status_code == 201
    s1_id = res1.json()["scene"]["id"]
    data1 = client.post(f"/api/projects/{project_id}/scenes/{s1_id}/analyze").json()
    assert "story_state" in data1

    # Scene 2: Cemetery, father died in 2015
    scene2_text = "EXT. CEMETERY - DAY\n\nJohn stands beside his father's grave.\n\nHis father died in 2015."
    res2 = client.post(f"/api/projects/{project_id}/scenes", json={"scene_number": 2, "raw_text": scene2_text})
    assert res2.status_code == 201
    s2_id = res2.json()["scene"]["id"]
    client.post(f"/api/projects/{project_id}/scenes/{s2_id}/analyze")

    # Scene 3: Buys motorcycle
    scene3_text = "EXT. MOTORCYCLE SHOP - DAY\n\nJohn buys a motorcycle.\n\nHe rides away."
    res3 = client.post(f"/api/projects/{project_id}/scenes", json={"scene_number": 3, "raw_text": scene3_text})
    assert res3.status_code == 201
    s3_id = res3.json()["scene"]["id"]
    client.post(f"/api/projects/{project_id}/scenes/{s3_id}/analyze")

    # Scene 4: Travels from Chennai to Mumbai
    scene4_text = "EXT. CHENNAI HIGHWAY - DAY\n\nJohn travels from Chennai to Mumbai."
    res4 = client.post(f"/api/projects/{project_id}/scenes", json={"scene_number": 4, "raw_text": scene4_text})
    assert res4.status_code == 201
    s4_id = res4.json()["scene"]["id"]
    client.post(f"/api/projects/{project_id}/scenes/{s4_id}/analyze")

    # Scene 5: Mumbai cafe, meets Sarah, gets envelope, learns Michael is dead
    scene5_text = "INT. MUMBAI CAFE - NIGHT\n\nJohn meets Sarah.\n\nSarah gives John an envelope.\n\nSarah tells John that Michael is dead.\n\nJohn is shocked."
    res5 = client.post(f"/api/projects/{project_id}/scenes", json={"scene_number": 5, "raw_text": scene5_text})
    assert res5.status_code == 201
    s5_id = res5.json()["scene"]["id"]
    client.post(f"/api/projects/{project_id}/scenes/{s5_id}/analyze")

    # Fetch final derived Story State
    state_res = client.get(f"/api/projects/{project_id}/story-state")
    assert state_res.status_code == 200
    state = state_res.json()

    # Assert Characters
    char_names = [c["name"].lower() for c in state["characters"]]
    assert "john" in char_names
    assert "sarah" in char_names

    john_state = next(c for c in state["characters"] if c["name"].lower() == "john")
    
    # Assert Residence vs Current Location (Section 29)
    assert john_state["residence"] is not None or john_state["current_location"] is not None

    # Assert Possessions (Motorcycle, Envelope)
    possession_names = [p["name"].lower() for p in john_state["possessions"]]
    assert "motorcycle" in possession_names or "envelope" in possession_names

    # Assert Knowledge
    knowledge_texts = [k["knowledge"].lower() for k in state["knowledge_states"]]
    assert any("michael" in k for k in knowledge_texts)

    # Assert Relationships
    rel_types = [r["relationship_type"].lower() for r in state["relationships"]]
    assert "owns" in rel_types or "possesses" in rel_types or "child_of" in rel_types

    # Summary Endpoint Test
    summary_res = client.get(f"/api/projects/{project_id}/story-state/summary")
    assert summary_res.status_code == 200
    summary = summary_res.json()
    assert summary["character_count"] >= 2
    assert summary["event_count"] >= 5
