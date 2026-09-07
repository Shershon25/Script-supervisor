import pytest
from app.services.exporter import (
    classify_screenplay_lines,
    generate_pdf_export,
    generate_docx_export,
    generate_fountain_export,
    parse_fountain_import
)

SAMPLE_SCENE_1 = """INT. COFFEE SHOP - DAY

JOHN sits at a small table, sipping espresso.

JOHN
(nervous)
I wasn't sure if you'd show up.

MARY enters, shaking rain off her umbrella.

MARY
Traffic was terrible.

CUT TO:"""

SAMPLE_SCENE_2 = """EXT. PARK - DAY

John and Mary walk along the tree-lined path.

JOHN
So what's the plan?
"""


def test_classify_screenplay_lines():
    classified = classify_screenplay_lines(SAMPLE_SCENE_1)
    types = [item[0] for item in classified if item[0] != "BLANK"]
    
    assert "SCENE_HEADING" in types
    assert "CHARACTER" in types
    assert "PARENTHETICAL" in types
    assert "DIALOGUE" in types
    assert "TRANSITION" in types
    assert "ACTION" in types

def test_location_heading_detection_without_prefix():
    interrogation_scene = "INTERROGATION ROOM\n\n(A BOY, SWEATING WITH A STOIC EXPRESSION)\n\nO.S.\nDo you know anyone named Maddie?"
    classified = classify_screenplay_lines(interrogation_scene)
    
    # INTERROGATION ROOM must be classified as SCENE_HEADING, NOT a character
    first_item = classified[0]
    assert first_item[0] == "SCENE_HEADING"
    assert first_item[1] == "INTERROGATION ROOM"

    # O.S. must be classified as CHARACTER
    char_items = [item for item in classified if item[0] == "CHARACTER"]
    assert len(char_items) >= 1
    assert char_items[0][1] == "O.S."


def test_dialogue_line_merging_into_single_paragraph():
    multi_line_dialogue = "BOY\nAt school, I was in a terrible\nplace. I always pretended that I\nwas cool, and everything in my\nlife\nwas perfect, but in reality... it\nwasn't."
    pdf_bytes = generate_pdf_export([multi_line_dialogue])
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")

    docx_bytes = generate_docx_export([multi_line_dialogue])
    assert isinstance(docx_bytes, bytes)
    assert docx_bytes.startswith(b"PK")


def test_parenthetical_action_after_dialogue_classification():
    script_text = "MADDIE\n(Sadly)\nOkay. I'll let you sleep.\n(Lilly groans, lies down, and there is a silent pause.)\n\nLILLY\n(Sarcastically)\nThanks a lot."
    classified = classify_screenplay_lines(script_text)
    
    # (Lilly groans...) following DIALOGUE must be classified as ACTION, not PARENTHETICAL
    action_items = [item for item in classified if item[0] == "ACTION"]
    assert len(action_items) == 1
    assert "Lilly groans" in action_items[0][1]


def test_generate_pdf_export():
    pdf_bytes = generate_pdf_export(
        scenes_text=[SAMPLE_SCENE_1, SAMPLE_SCENE_2],
        font_family="Courier",
        font_size=12
    )
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 500
    assert pdf_bytes.startswith(b"%PDF")


def test_generate_docx_export():
    docx_bytes = generate_docx_export(
        scenes_text=[SAMPLE_SCENE_1, SAMPLE_SCENE_2],
        font_family="Courier New",
        font_size=12
    )
    assert isinstance(docx_bytes, bytes)
    assert len(docx_bytes) > 500
    # DOCX is a zip file starting with PK header
    assert docx_bytes.startswith(b"PK")


def test_generate_fountain_export():
    fountain_text = generate_fountain_export([SAMPLE_SCENE_1, SAMPLE_SCENE_2])
    assert "INT. COFFEE SHOP - DAY" in fountain_text
    assert "EXT. PARK - DAY" in fountain_text
    assert "JOHN" in fountain_text
    assert "MARY" in fountain_text


def test_parse_fountain_import():
    fountain_input = f"{SAMPLE_SCENE_1}\n\n{SAMPLE_SCENE_2}"
    parsed_scenes = parse_fountain_import(fountain_input)
    
    assert len(parsed_scenes) == 2
    assert parsed_scenes[0]["scene_number"] == 1
    assert "INT. COFFEE SHOP - DAY" in parsed_scenes[0]["raw_text"]
    assert parsed_scenes[1]["scene_number"] == 2
    assert "EXT. PARK - DAY" in parsed_scenes[1]["raw_text"]


def test_export_api_endpoints(client):
    # 1. Create a project
    proj_res = client.post("/api/projects", json={"title": "Export Test Project"})
    assert proj_res.status_code == 201
    project_id = proj_res.json()["id"]

    # 2. Add a scene
    scene_res = client.post(f"/api/projects/{project_id}/scenes", json={
        "scene_number": 1,
        "raw_text": SAMPLE_SCENE_1
    })
    assert scene_res.status_code == 201

    # 3. Test PDF export endpoint
    pdf_res = client.get(f"/api/projects/{project_id}/export?format=pdf&font_family=Courier&font_size=12")
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert pdf_res.content.startswith(b"%PDF")

    # 4. Test DOCX export endpoint
    docx_res = client.get(f"/api/projects/{project_id}/export?format=docx")
    assert docx_res.status_code == 200
    assert "wordprocessingml" in docx_res.headers["content-type"]
    assert docx_res.content.startswith(b"PK")

    # 5. Test Fountain export endpoint
    fountain_res = client.get(f"/api/projects/{project_id}/export?format=fountain")
    assert fountain_res.status_code == 200
    assert "text/plain" in fountain_res.headers["content-type"]
    assert b"INT. COFFEE SHOP - DAY" in fountain_res.content
