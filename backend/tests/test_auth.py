import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_auth_register_and_login():
    client_unauth = TestClient(app)
    
    # 1. Register User
    reg_res = client_unauth.post("/api/auth/register", json={
        "username": "newuser",
        "password": "secretpassword"
    })
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    assert "access_token" in reg_data
    assert reg_data["user"]["username"] == "newuser"

    # 2. Duplicate Username Registration -> 400
    dup_res = client_unauth.post("/api/auth/register", json={
        "username": "newuser",
        "password": "anotherpassword"
    })
    assert dup_res.status_code == 400

    # 3. Login User
    login_res = client_unauth.post("/api/auth/login", json={
        "username": "newuser",
        "password": "secretpassword"
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]

    # 4. Access /api/auth/me with Token
    me_res = client_unauth.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_res.status_code == 200
    assert me_res.json()["username"] == "newuser"

def test_unauthenticated_request_rejected(client):
    client_unauth = TestClient(app)
    
    # Unauthenticated request to /api/projects -> 401
    res = client_unauth.get("/api/projects")
    assert res.status_code == 401

def test_user_project_isolation():
    client_unauth = TestClient(app)
    
    # User 1
    u1_reg = client_unauth.post("/api/auth/register", json={"username": "user1", "password": "password1"}).json()
    t1 = u1_reg["access_token"]
    
    # User 2
    u2_reg = client_unauth.post("/api/auth/register", json={"username": "user2", "password": "password2"}).json()
    t2 = u2_reg["access_token"]
    
    # User 1 creates project
    p1 = client_unauth.post(
        "/api/projects",
        json={"title": "User 1 Secret Project"},
        headers={"Authorization": f"Bearer {t1}"}
    ).json()

    # User 2 lists projects -> should not see User 1's project
    p2_list = client_unauth.get(
        "/api/projects",
        headers={"Authorization": f"Bearer {t2}"}
    ).json()
    assert not any(p["id"] == p1["id"] for p in p2_list)

    # User 2 attempts to get User 1's project directly -> 404
    bad_get = client_unauth.get(
        f"/api/projects/{p1['id']}",
        headers={"Authorization": f"Bearer {t2}"}
    )
    assert bad_get.status_code == 404
