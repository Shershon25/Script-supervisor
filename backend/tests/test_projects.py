def test_create_and_list_projects(client):
    # Create project
    res = client.post("/api/projects", json={"title": "Test Project 1"})
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "Test Project 1"
    project_id = data["id"]

    # Get project
    res_get = client.get(f"/api/projects/{project_id}")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == project_id

    # List projects
    res_list = client.get("/api/projects")
    assert res_list.status_code == 200
    titles = [p["title"] for p in res_list.json()]
    assert "Test Project 1" in titles


def test_delete_project(client):
    # Create project
    res = client.post("/api/projects", json={"title": "Project to Delete"})
    assert res.status_code == 201
    project_id = res.json()["id"]

    # Delete project
    del_res = client.delete(f"/api/projects/{project_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "success"

    # Verify project no longer exists
    get_res = client.get(f"/api/projects/{project_id}")
    assert get_res.status_code == 404

