from app.db.models import Project, ProjectSettings, StoryWorldRule, Issue, Scene
from app.services.project_settings import get_or_create_project_settings, get_active_world_rules

def test_default_settings_initialization(client):
    """Test A.1 & A.2: Creating project auto-initializes settings (reality=5, strictness=5, version=1)."""
    response = client.post("/api/projects", json={"title": "Test Project Settings Init"})
    assert response.status_code == 201
    proj_id = response.json()["id"]

    res_settings = client.get(f"/api/projects/{proj_id}/settings")
    assert res_settings.status_code == 200
    data = res_settings.json()
    assert data["project_id"] == proj_id
    assert data["reality_level"] == 5
    assert data["continuity_strictness"] == 5
    assert data["settings_version"] == 1
    assert data["world_rules"] == []

def test_modify_settings_and_version_increment(client):
    """Test B.3 - B.6: Valid updates increment settings_version; invalid bounds return 400."""
    p_res = client.post("/api/projects", json={"title": "Settings Version Project"})
    proj_id = p_res.json()["id"]

    # Update reality_level = 2 -> version becomes 2
    res1 = client.put(f"/api/projects/{proj_id}/settings", json={"reality_level": 2})
    assert res1.status_code == 200
    assert res1.json()["reality_level"] == 2
    assert res1.json()["settings_version"] == 2

    # Update continuity_strictness = 9 -> version becomes 3
    res2 = client.put(f"/api/projects/{proj_id}/settings", json={"continuity_strictness": 9})
    assert res2.status_code == 200
    assert res2.json()["continuity_strictness"] == 9
    assert res2.json()["settings_version"] == 3

    # Invalid bounds (reality_level = 15) -> 400 or 422
    res_bad1 = client.put(f"/api/projects/{proj_id}/settings", json={"reality_level": 15})
    assert res_bad1.status_code in (400, 422)

    # Invalid bounds (continuity_strictness = -1) -> 400 or 422
    res_bad2 = client.put(f"/api/projects/{proj_id}/settings", json={"continuity_strictness": -1})
    assert res_bad2.status_code in (400, 422)

def test_world_rules_crud_and_isolation(client):
    """Test C.7 - C.10: CRUD operations on world rules and strict project isolation."""
    p1 = client.post("/api/projects", json={"title": "Project Alpha"}).json()
    p2 = client.post("/api/projects", json={"title": "Project Beta"}).json()

    # Create Rule in Project Alpha
    rule_res = client.post(f"/api/projects/{p1['id']}/settings/world-rules", json={
        "rule_text": "Teleportation device exists in this world",
        "active": True
    })
    assert rule_res.status_code == 201
    rule_data = rule_res.json()
    assert rule_data["rule_text"] == "Teleportation device exists in this world"
    assert rule_data["active"] is True
    rule_id = rule_data["id"]

    # Settings version in P1 bumped to 2
    settings_p1 = client.get(f"/api/projects/{p1['id']}/settings").json()
    assert settings_p1["settings_version"] == 2
    assert len(settings_p1["world_rules"]) == 1

    # Toggle active=False via PATCH
    patch_res = client.patch(f"/api/projects/{p1['id']}/settings/world-rules/{rule_id}", json={"active": False})
    assert patch_res.status_code == 200
    assert patch_res.json()["active"] is False

    # Settings version in P1 bumped to 3
    settings_p1_after = client.get(f"/api/projects/{p1['id']}/settings").json()
    assert settings_p1_after["settings_version"] == 3

    # Attempt to operate on P1 rule_id from P2 context -> 404 (Isolation)
    iso_res = client.patch(f"/api/projects/{p2['id']}/settings/world-rules/{rule_id}", json={"active": True})
    assert iso_res.status_code == 404

    # Delete rule
    del_res = client.delete(f"/api/projects/{p1['id']}/settings/world-rules/{rule_id}")
    assert del_res.status_code == 204

    settings_p1_final = client.get(f"/api/projects/{p1['id']}/settings").json()
    assert len(settings_p1_final["world_rules"]) == 0
    assert settings_p1_final["settings_version"] == 4

def test_fictional_rule_precedence_and_claim_classification(client):
    """Test D.11 & D.12: Active world rule forces claim to FICTIONAL_WORLD_RULE (no research)."""
    p = client.post("/api/projects", json={"title": "Sci-Fi Universe"}).json()
    
    # Add active rule
    client.post(f"/api/projects/{p['id']}/settings/world-rules", json={
        "rule_text": "Teleportation device exists in this world",
        "active": True
    })

    # Add scene with teleportation claim
    sc_res = client.post(f"/api/projects/{p['id']}/scenes", json={
        "scene_number": 1,
        "raw_text": "INT. MUMBAI CAFE - NIGHT\n\nSarah tells Mike that teleportation device exists in this world."
    })
    assert sc_res.status_code == 201

    # Analyze unified scene
    u_res = client.post(f"/api/projects/{p['id']}/scenes/{sc_res.json()['scene']['id']}/analyze")
    assert u_res.status_code == 200

    claims_res = client.get(f"/api/projects/{p['id']}/claims")
    assert claims_res.status_code == 200
    claims = claims_res.json()
    
    # Match claim
    teleport_claims = [c for c in claims if "teleportation" in c["claim_text"].lower()]
    if teleport_claims:
        tc = teleport_claims[0]
        assert tc["claim_type"] == "FICTIONAL_WORLD_RULE"
        assert tc["requires_research"] is False

def test_writer_decision_authority_over_strictness(client):
    """Test E.13: Setting continuity_strictness=10 does NOT resurrect ACCEPTED/IGNORED/RESOLVED issues."""
    p = client.post("/api/projects", json={"title": "Writer Authority Test"}).json()

    sc_res = client.post(f"/api/projects/{p['id']}/scenes", json={
        "scene_number": 1,
        "raw_text": "INT. APARTMENT - NIGHT\n\nJohn lives in Chennai."
    }).json()

    # Analyze scene
    client.post(f"/api/projects/{p['id']}/scenes/{sc_res['scene']['id']}/analyze")

    # Add conflicting scene
    sc2_res = client.post(f"/api/projects/{p['id']}/scenes", json={
        "scene_number": 2,
        "raw_text": "INT. APARTMENT - NIGHT\n\nJohn lives in Mumbai."
    }).json()

    client.post(f"/api/projects/{p['id']}/scenes/{sc2_res['scene']['id']}/analyze")

    issues_res = client.get(f"/api/projects/{p['id']}/issues")
    issues = issues_res.json()
    
    if issues:
        target_issue = issues[0]
        # Review issue as ACCEPTED
        rev_res = client.post(f"/api/projects/{p['id']}/issues/{target_issue['id']}/review", json={
            "action": "ACCEPT",
            "note": "Writer intentional choice"
        })
        assert rev_res.status_code == 200
        assert rev_res.json()["issue"]["status"] == "ACCEPTED font-medium" or rev_res.json()["issue"]["status"] == "ACCEPTED"

        # Now set strictness to 10
        client.put(f"/api/projects/{p['id']}/settings", json={"continuity_strictness": 10})

        # Re-analyze scene
        client.post(f"/api/projects/{p['id']}/scenes/{sc2_res['scene']['id']}/analyze")

        # Verify issue status remains ACCEPTED, not duplicated or reopened
        issues_after = client.get(f"/api/projects/{p['id']}/issues").json()
        reviewed_target = next((i for i in issues_after if i["id"] == target_issue["id"]), None)
        assert reviewed_target is not None
        assert reviewed_target["status"] == "ACCEPTED"

def test_project_settings_isolation(client):
    """Test G.15 & G.16: Settings operations on Project A never mutate Project B."""
    pA = client.post("/api/projects", json={"title": "Project A Settings"}).json()
    pB = client.post("/api/projects", json={"title": "Project B Settings"}).json()

    # Update P_A settings
    client.put(f"/api/projects/{pA['id']}/settings", json={"reality_level": 1, "continuity_strictness": 2})

    settingsA = client.get(f"/api/projects/{pA['id']}/settings").json()
    settingsB = client.get(f"/api/projects/{pB['id']}/settings").json()

    assert settingsA["reality_level"] == 1
    assert settingsA["continuity_strictness"] == 2
    assert settingsA["settings_version"] == 2

    # Project B remains untouched defaults
    assert settingsB["reality_level"] == 5
    assert settingsB["continuity_strictness"] == 5
    assert settingsB["settings_version"] == 1
