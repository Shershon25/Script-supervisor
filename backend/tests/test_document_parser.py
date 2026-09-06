import pytest
import io
import docx
from pypdf import PdfWriter

from app.services.document_parser import (
    TxtDocumentParser, DocxDocumentParser, PdfDocumentParser, SceneBoundaryDetector, ParsedDocument
)

SAMPLE_SCREENPLAY_TEXT = """INT. ARJUN'S APARTMENT - MORNING

Arjun studies an old photograph.

His phone rings.

MAYA (V.O.)
You still have the photograph?

ARJUN
Yes.

CUT TO:

EXT. CHENNAI CENTRAL - DAY

Arjun meets Maya.

They walk toward the station.

CUT TO:

INT. POLICE ARCHIVE - NIGHT

Maya searches an old file."""


def create_sample_docx(text: str) -> bytes:
    doc = docx.Document()
    for paragraph in text.split("\n"):
        if paragraph.strip():
            doc.add_paragraph(paragraph.strip())
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()


def create_sample_pdf(text: str) -> bytes:
    # Build a simple valid text PDF using pypdf / ReportLab-free raw canvas or PyPDF writer
    # For testing, we can use a basic pypdf page creation or mock stream
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    # pypdf Writer blank page
    bio = io.BytesIO()
    writer.write(bio)
    return bio.getvalue()


def test_txt_parser_preserves_line_order():
    """Test 1 & 17: TXT parser preserves exact line order and page ranges are None."""
    parser = TxtDocumentParser()
    bytes_data = SAMPLE_SCREENPLAY_TEXT.encode("utf-8")
    parsed_doc = parser.parse(bytes_data, "screenplay.txt")

    assert parsed_doc.file_type == "txt"
    assert parsed_doc.page_count is None
    assert "INT. ARJUN'S APARTMENT - MORNING" in parsed_doc.raw_text
    assert "INT. POLICE ARCHIVE - NIGHT" in parsed_doc.raw_text


def test_docx_parser_preserves_paragraph_order():
    """Test 2: DOCX parser preserves paragraph order."""
    parser = DocxDocumentParser()
    docx_bytes = create_sample_docx(SAMPLE_SCREENPLAY_TEXT)
    parsed_doc = parser.parse(docx_bytes, "screenplay.docx")

    assert parsed_doc.file_type == "docx"
    assert parsed_doc.character_count > 0
    assert "INT. ARJUN'S APARTMENT - MORNING" in parsed_doc.raw_text
    assert "EXT. CHENNAI CENTRAL - DAY" in parsed_doc.raw_text


def test_empty_files_rejected():
    """Test 5: Empty files raise ValueError."""
    txt_parser = TxtDocumentParser()
    with pytest.raises(ValueError, match="empty"):
        txt_parser.parse(b"", "empty.txt")

    docx_parser = DocxDocumentParser()
    with pytest.raises(ValueError):
        docx_parser.parse(b"", "empty.docx")


def test_corrupt_files_fail_cleanly():
    """Test 6: Corrupt file bytes fail cleanly."""
    docx_parser = DocxDocumentParser()
    with pytest.raises(ValueError, match="corrupted"):
        docx_parser.parse(b"NOT_A_REAL_DOCX_STREAM", "corrupt.docx")

    pdf_parser = PdfDocumentParser()
    with pytest.raises(ValueError, match="corrupted"):
        pdf_parser.parse(b"NOT_A_REAL_PDF_STREAM", "corrupt.pdf")


def test_scene_detection_headings():
    """Test 7-12 & Sample Screenplay Fixture: INT, EXT, INT./EXT., time-of-day, deterministic scene numbering."""
    text_fixture = """INT. ARJUN'S APARTMENT - MORNING

Arjun studies an old photograph.

ext. chennai central - day

Arjun meets Maya.

INT./EXT. CAR - NIGHT

Maya drives into the alley."""

    parser = TxtDocumentParser()
    parsed_doc = parser.parse(text_fixture.encode("utf-8"), "test.txt")

    detector = SceneBoundaryDetector()
    scenes = detector.detect_scenes(parsed_doc)

    assert len(scenes) == 3

    # Scene 1
    assert scenes[0].scene_number == 1
    assert "INT. ARJUN'S APARTMENT - MORNING" in scenes[0].heading
    assert "studies an old photograph" in scenes[0].raw_text
    assert scenes[0].confidence >= 0.90

    # Scene 2 (case-insensitive ext.)
    assert scenes[1].scene_number == 2
    assert "ext. chennai central - day" in scenes[1].heading.lower()
    assert "Arjun meets Maya" in scenes[1].raw_text

    # Scene 3 (INT./EXT.)
    assert scenes[2].scene_number == 3
    assert "INT./EXT. CAR - NIGHT" in scenes[2].heading


def test_sample_three_scene_fixture():
    """Test 32: Sample screenplay fixture produces exactly 3 scenes."""
    parser = TxtDocumentParser()
    parsed_doc = parser.parse(SAMPLE_SCREENPLAY_TEXT.encode("utf-8"), "sample.txt")

    detector = SceneBoundaryDetector()
    scenes = detector.detect_scenes(parsed_doc)

    assert len(scenes) == 3
    assert scenes[0].heading == "INT. ARJUN'S APARTMENT - MORNING"
    assert scenes[1].heading == "EXT. CHENNAI CENTRAL - DAY"
    assert scenes[2].heading == "INT. POLICE ARCHIVE - NIGHT"


def test_micro_actions_not_treated_as_scenes():
    """Test 14: Micro-actions like 'CUT TO:' or 'He walks inside.' are not scene headings."""
    text = """INT. LIVING ROOM - DAY

John walks inside. He checks his watch.

CUT TO:

EXT. PARK - NIGHT

Sarah waits by the bench."""

    parser = TxtDocumentParser()
    parsed_doc = parser.parse(text.encode("utf-8"), "script.txt")

    detector = SceneBoundaryDetector()
    scenes = detector.detect_scenes(parsed_doc)

    assert len(scenes) == 2
    assert scenes[0].heading == "INT. LIVING ROOM - DAY"
    assert scenes[1].heading == "EXT. PARK - NIGHT"


def test_custom_location_heading_without_int_ext():
    """Test custom location headings without INT. or EXT. prefixes (e.g. INTERROGATION ROOM)."""
    text = """INTERROGATION ROOM

(A BOY, SWEATING WITH A STOIC EXPRESSION, IS LOOKING DIRECTLY AT THE CAMERA)

O.S.
Do you know anyone named Maddie Anderson?

BOY
Yes.

INT. CLASSROOM - DAY

Teacher writes on the blackboard."""

    parser = TxtDocumentParser()
    parsed_doc = parser.parse(text.encode("utf-8"), "script.txt")

    detector = SceneBoundaryDetector()
    scenes = detector.detect_scenes(parsed_doc)

    assert len(scenes) == 2
    assert scenes[0].scene_number == 1
    assert scenes[0].heading == "INTERROGATION ROOM"
    assert "(A BOY, SWEATING" in scenes[0].raw_text
    assert "BOY\nYes." in scenes[0].raw_text

    assert scenes[1].scene_number == 2
    assert scenes[1].heading == "INT. CLASSROOM - DAY"
    assert "Teacher writes" in scenes[1].raw_text


def test_cover_page_is_stripped_not_treated_as_scene():
    """Test that screenplay title/cover pages with 'Written by' are stripped and not created as scenes."""
    text = """OUAC

Written by

Melissa Vivian Holicek

INTERROGATION ROOM

(A BOY, SWEATING WITH A STOIC EXPRESSION, IS LOOKING DIRECTLY AT THE CAMERA)

O.S.
Do you know anyone named Maddie Anderson?

BOY
Yes."""

    parser = TxtDocumentParser()
    parsed_doc = parser.parse(text.encode("utf-8"), "ouac.txt")

    detector = SceneBoundaryDetector()
    scenes = detector.detect_scenes(parsed_doc)

    assert len(scenes) == 1
    assert scenes[0].scene_number == 1
    assert scenes[0].heading == "INTERROGATION ROOM"
    assert "Written by" not in scenes[0].raw_text
    assert "Melissa Vivian Holicek" not in scenes[0].raw_text
    assert "(A BOY, SWEATING" in scenes[0].raw_text


def test_concatenated_pdf_title_page_stripped():
    """Test single-line PDF streams where title page metadata is space-joined before scene heading."""
    text = "OUAC Written by Melissa Vivian Holicek INTERROGATION ROOM (A BOY, SWEATING WITH A STOIC EXPRESSION, IS LOOKING DIRECTLY AT THE CAMERA) O.S. Do you know anyone named Maddie Anderson? BOY Yes."

    parser = TxtDocumentParser()
    parsed_doc = parser.parse(text.encode("utf-8"), "concatenated_pdf.txt")

    detector = SceneBoundaryDetector()
    scenes = detector.detect_scenes(parsed_doc)

    assert len(scenes) == 1
    assert scenes[0].scene_number == 1
    assert scenes[0].heading == "INTERROGATION ROOM"
    assert "OUAC" not in scenes[0].heading
    assert "Written by" not in scenes[0].raw_text
    assert "Melissa Vivian Holicek" not in scenes[0].raw_text
    assert "(A BOY, SWEATING" in scenes[0].raw_text



