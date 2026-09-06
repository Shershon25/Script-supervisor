def test_scene_processing_and_story_memory(client):
    # 1. Create project
    proj_res = client.post("/api/projects", json={"title": "3-Scene Test Project"})
    assert proj_res.status_code == 201
    project_id = proj_res.json()["id"]

    # 2. Submit Scene 1
    scene1_text = "INT. JOHN'S APARTMENT - NIGHT\n\nJohn enters his apartment.\n\nHe looks at a photograph of his father."
    res1 = client.post(f"/api/projects/{project_id}/scenes", json={"scene_number": 1, "raw_text": scene1_text})
    assert res1.status_code == 201
    data1 = res1.json()
    assert "scene" in data1
    assert "analysis" in data1

    # Test duplicate scene #1
    res_dup = client.post(f"/api/projects/{project_id}/scenes", json={"scene_number": 1, "raw_text": "Duplicate"})
    assert res_dup.status_code == 409

    # 3. Submit Scene 2
    scene2_text = "EXT. CHENNAI STREET - DAY\n\nJohn walks outside.\n\nHe gets onto his motorcycle."
    res2 = client.post(f"/api/projects/{project_id}/scenes", json={"scene_number": 2, "raw_text": scene2_text})
    assert res2.status_code == 201

    # 4. Submit Scene 3
    scene3_text = "INT. CAFE - DAY\n\nJohn meets Sarah.\n\nSarah gives John a small envelope."
    res3 = client.post(f"/api/projects/{project_id}/scenes", json={"scene_number": 3, "raw_text": scene3_text})
    assert res3.status_code == 201

    # 5. Verify Story Data accumulation across all 3 scenes
    story_res = client.get(f"/api/projects/{project_id}/story-data")
    assert story_res.status_code == 200
    story_data = story_res.json()
    
    entity_names = [e["name"].lower() for e in story_data["entities"]]
    assert "john" in entity_names
    assert "sarah" in entity_names
    
    assert len(story_data["events"]) >= 3
