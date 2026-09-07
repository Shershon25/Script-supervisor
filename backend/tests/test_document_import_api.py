import pytest
import io
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import Base, engine
from app.db.models import Project, Scene, ImportedDocument

client = TestClient(app)

SAMPLE_TXT_CONTENT = """INT. ARJUN'S APARTMENT - MORNING

Arjun studies an old photograph.

MAYA (V.O.)
You still have the photograph?

EXT. CHENNAI CENTRAL - DAY

Arjun meets Maya.

INT. POLICE ARCHIVE - NIGHT

Maya searches an old file."""

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    if "scenes" in inspector.get_table_names():
        columns = [c["name"] for c in inspector.get_columns("scenes")]
        with engine.begin() as conn:
            if "source_document_id" not in columns:
                conn.execute(text("ALTER TABLE scenes ADD COLUMN source_document_id VARCHAR(36)"))
            if "source_page_start" not in columns:
                conn.execute(text("ALTER TABLE scenes ADD COLUMN source_page_start INTEGER"))
            if "source_page_end" not in columns:
                conn.execute(text("ALTER TABLE scenes ADD COLUMN source_page_end INTEGER"))
            if "source_type" not in columns:
                conn.execute(text("ALTER TABLE scenes ADD COLUMN source_type VARCHAR(50) DEFAULT 'MANUAL'"))
    yield


def test_document_import_preview_api():
    """Test API: Upload Fountain document for preview, check scene count and READY_FOR_REVIEW status."""
    p_res = client.post("/api/projects", json={"title": "Import API Test Project"}).json()
    proj_id = p_res["id"]

    files = {"file": ("test_screenplay.fountain", io.BytesIO(SAMPLE_TXT_CONTENT.encode("utf-8")), "text/plain")}
    res = client.post(f"/api/projects/{proj_id}/documents/import", files=files)

    assert res.status_code == 200
    data = res.json()
    assert data["filename"] == "test_screenplay.fountain"
    assert data["file_type"] == "fountain"
    assert data["status"] == "READY_FOR_REVIEW"
    assert data["scene_count"] == 3
    assert len(data["scenes"]) == 3
    assert data["scenes"][0]["heading"] == "INT. ARJUN'S APARTMENT - MORNING"


def test_document_confirm_import_append():
    """Test API & Provenance: Confirm import creates Scene records with source_type=IMPORTED_DOCUMENT."""
    p_res = client.post("/api/projects", json={"title": "Confirm Import Project"}).json()
    proj_id = p_res["id"]

    files = {"file": ("screenplay.fountain", io.BytesIO(SAMPLE_TXT_CONTENT.encode("utf-8")), "text/plain")}
    preview_res = client.post(f"/api/projects/{proj_id}/documents/import", files=files).json()
    doc_id = preview_res["document_id"]

    # Confirm import
    confirm_res = client.post(f"/api/projects/{proj_id}/documents/{doc_id}/confirm-import", json={"mode": "append"})
    assert confirm_res.status_code == 200
    assert confirm_res.json()["scenes_imported"] == 3

    # Check created scenes
    scenes_res = client.get(f"/api/projects/{proj_id}/scenes")
    assert scenes_res.status_code == 200
    scenes = scenes_res.json()
    assert len(scenes) == 3
    assert scenes[0]["scene_number"] == 1
    assert scenes[0]["source_type"] == "IMPORTED_DOCUMENT"
    assert scenes[0]["source_document_id"] == doc_id


def test_document_confirm_import_replace():
    """Test API & Overwrite: Replace mode removes existing scenes before adding imported scenes."""
    p_res = client.post("/api/projects", json={"title": "Replace Mode Project"}).json()
    proj_id = p_res["id"]

    # Add existing manual scene
    sc1 = client.post(f"/api/projects/{proj_id}/scenes", json={"scene_number": 1, "raw_text": "INT. OLD SCENE - DAY\nOld text."}).json()

    # Upload document
    files = {"file": ("new_screenplay.fountain", io.BytesIO(SAMPLE_TXT_CONTENT.encode("utf-8")), "text/plain")}
    preview_res = client.post(f"/api/projects/{proj_id}/documents/import", files=files).json()
    doc_id = preview_res["document_id"]

    # Confirm import in replace mode
    confirm_res = client.post(f"/api/projects/{proj_id}/documents/{doc_id}/confirm-import", json={"mode": "replace"})
    assert confirm_res.status_code == 200

    scenes = client.get(f"/api/projects/{proj_id}/scenes").json()
    assert len(scenes) == 3
    assert "INT. ARJUN'S APARTMENT - MORNING" in scenes[0]["raw_text"]


def test_project_isolation_on_import():
    """Test 19 & 20: Project A cannot confirm import for Project B's document."""
    pA = client.post("/api/projects", json={"title": "Project Alpha"}).json()
    pB = client.post("/api/projects", json={"title": "Project Beta"}).json()

    files = {"file": ("screenplay.fountain", io.BytesIO(SAMPLE_TXT_CONTENT.encode("utf-8")), "text/plain")}
    preview_A = client.post(f"/api/projects/{pA['id']}/documents/import", files=files).json()
    doc_A_id = preview_A["document_id"]

    # Attempt to confirm Project A's doc from Project B -> 404
    bad_res = client.post(f"/api/projects/{pB['id']}/documents/{doc_A_id}/confirm-import", json={"mode": "append"})
    assert bad_res.status_code == 404


def test_duplicate_confirmation_idempotent():
    """Test 23: Duplicate confirmation calls return already imported message without duplicating scenes."""
    p = client.post("/api/projects", json={"title": "Idempotent Project"}).json()
    files = {"file": ("screenplay.fountain", io.BytesIO(SAMPLE_TXT_CONTENT.encode("utf-8")), "text/plain")}
    preview = client.post(f"/api/projects/{p['id']}/documents/import", files=files).json()
    doc_id = preview["document_id"]

    c1 = client.post(f"/api/projects/{p['id']}/documents/{doc_id}/confirm-import", json={"mode": "append"})
    assert c1.status_code == 200

    c2 = client.post(f"/api/projects/{p['id']}/documents/{doc_id}/confirm-import", json={"mode": "append"})
    assert c2.status_code == 200
    assert "already been imported" in c2.json()["message"]

    scenes = client.get(f"/api/projects/{p['id']}/scenes").json()
    assert len(scenes) == 3


def test_imported_scene_analyzed_by_existing_pipeline():
    """Test 24-29: Imported scene can be analyzed by existing unified scene analysis service."""
    p = client.post("/api/projects", json={"title": "Unified Analysis Integration Project"}).json()
    files = {"file": ("screenplay.fountain", io.BytesIO(SAMPLE_TXT_CONTENT.encode("utf-8")), "text/plain")}
    preview = client.post(f"/api/projects/{p['id']}/documents/import", files=files).json()
    doc_id = preview["document_id"]

    client.post(f"/api/projects/{p['id']}/documents/{doc_id}/confirm-import", json={"mode": "append"})
    scenes = client.get(f"/api/projects/{p['id']}/scenes").json()
    imported_scene_id = scenes[0]["id"]

    # Run unified analysis on imported scene
    analyze_res = client.post(f"/api/projects/{p['id']}/scenes/{imported_scene_id}/analyze")
    assert analyze_res.status_code == 200
    ana_data = analyze_res.json()
    assert ana_data["scene"]["id"] == imported_scene_id
    assert "analysis" in ana_data
