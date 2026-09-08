import json
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.db.database import get_db
from app.db.models import Project, Scene, ImportedDocument, SceneAnalysisRun
from app.schemas.document import (
    ImportPreviewResponse, ParsedSceneResponse, ConfirmImportRequest, ImportedDocumentResponse
)
from app.services.document_parser import (
    PdfDocumentParser, DocxDocumentParser, FountainDocumentParser, SceneBoundaryDetector, ParsedDocument
)

logger = logging.getLogger("script_supervisor.api_documents")

router = APIRouter(prefix="/api/projects/{project_id}/documents", tags=["Document Import"])

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".fountain"}

import os

def sanitize_filename(filename: str) -> str:
    """Strips path traversal indicators from uploaded filename."""
    if not filename:
        return "screenplay.fountain"
    # Take basename only
    base = os.path.basename(filename.replace("\\", "/")).strip()
    return base or "screenplay.fountain"

def validate_file_metadata(filename: str, file_size: int):
    """Validates filename extension and size limits."""
    clean_name = sanitize_filename(filename)
    dot_idx = clean_name.rfind(".")
    if dot_idx == -1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file has no extension. Supported formats are PDF (.pdf), DOCX (.docx), and Fountain (.fountain)."
        )

    ext = clean_name[dot_idx:].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Supported formats are PDF (.pdf), DOCX (.docx), and Fountain (.fountain)."
        )

    max_bytes = settings.MAX_IMPORT_FILE_SIZE_MB * 1024 * 1024
    if file_size > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed limit of {settings.MAX_IMPORT_FILE_SIZE_MB}MB."
        )

    return ext


@router.post("/import", response_model=ImportPreviewResponse, status_code=status.HTTP_200_OK)
async def import_document_preview(
    project_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Ingests a PDF, DOCX, or Fountain screenplay document, extracts text deterministically,
    detects scene boundaries, stores temporary preview state, and returns an import preview.
    """
    # 1. Validate project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    raw_filename = file.filename or "screenplay.fountain"
    filename = sanitize_filename(raw_filename)
    file_bytes = await file.read()
    file_size = len(file_bytes)

    # 2. Validate file metadata
    ext = validate_file_metadata(filename, file_size)

    # 3. Parse document according to file type
    file_type = ext.lstrip(".")
    try:
        if file_type == "pdf":
            parser = PdfDocumentParser()
        elif file_type == "docx":
            parser = DocxDocumentParser()
        else:
            parser = FountainDocumentParser()

        parsed_doc: ParsedDocument = parser.parse(file_bytes, filename)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Error parsing document {filename}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Document parsing failed: {str(e)}")

    if parsed_doc.character_count > settings.MAX_DOCUMENT_CHARACTERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Decompressed document character count ({parsed_doc.character_count}) exceeds maximum allowed limit of {settings.MAX_DOCUMENT_CHARACTERS} characters."
        )

    # 4. Detect scene boundaries deterministically
    detector = SceneBoundaryDetector()
    detected_scenes = detector.detect_scenes(parsed_doc)

    if len(detected_scenes) > settings.MAX_IMPORTED_SCENES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Screenplay contains {len(detected_scenes)} scenes, exceeding max allowed limit of {settings.MAX_IMPORTED_SCENES}."
        )

    # 5. Check existing scenes count
    existing_scenes_count = db.query(Scene).filter(Scene.project_id == project_id).count()

    # 6. Store temporary scenes preview payload on ImportedDocument
    scenes_payload = [
        {
            "temporary_id": s.temporary_id,
            "scene_number": s.scene_number,
            "heading": s.heading,
            "raw_text": s.raw_text,
            "source_page_start": s.source_page_start,
            "source_page_end": s.source_page_end,
            "confidence": s.confidence
        }
        for s in detected_scenes
    ]

    imported_doc = ImportedDocument(
        project_id=project_id,
        filename=filename,
        file_type=file_type,
        file_size=file_size,
        status="READY_FOR_REVIEW",
        parser_version="1.0.0",
        scene_detection_version="1.0.0",
        page_count=parsed_doc.page_count,
        character_count=parsed_doc.character_count,
        scene_count=len(detected_scenes),
        error_message=json.dumps(scenes_payload)  # Stored temp preview json
    )

    db.add(imported_doc)
    db.commit()
    db.refresh(imported_doc)

    parsed_responses = [
        ParsedSceneResponse(
            temporary_id=s.temporary_id,
            scene_number=s.scene_number,
            heading=s.heading,
            raw_text=s.raw_text,
            source_page_start=s.source_page_start,
            source_page_end=s.source_page_end,
            confidence=s.confidence
        )
        for s in detected_scenes
    ]

    return ImportPreviewResponse(
        document_id=imported_doc.id,
        filename=filename,
        file_type=file_type,
        file_size=file_size,
        status="READY_FOR_REVIEW",
        page_count=parsed_doc.page_count,
        character_count=parsed_doc.character_count,
        scene_count=len(detected_scenes),
        scenes=parsed_responses,
        warnings=parsed_doc.warnings,
        existing_scenes_count=existing_scenes_count
    )


@router.post("/{document_id}/confirm-import", status_code=status.HTTP_200_OK)
def confirm_document_import(
    project_id: str,
    document_id: str,
    payload: ConfirmImportRequest = ConfirmImportRequest(),
    db: Session = Depends(get_db)
):
    """
    Confirms document import and creates official Scene records with document provenance.
    If mode='replace', existing scenes of the project are deleted before creating new scenes.
    """
    imported_doc = db.query(ImportedDocument).filter(
        ImportedDocument.id == document_id,
        ImportedDocument.project_id == project_id
    ).first()

    if not imported_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Imported document not found.")

    # Idempotent duplicate confirmation protection
    if imported_doc.status == "IMPORTED":
        scenes_count = db.query(Scene).filter(
            Scene.project_id == project_id,
            Scene.source_document_id == document_id
        ).count()
        return {
            "message": "Document has already been imported.",
            "document_id": document_id,
            "scenes_imported": scenes_count
        }

    if not imported_doc.error_message:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No preview scene payload found for this document.")

    try:
        scenes_data = json.loads(imported_doc.error_message)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to read preview scene payload.")

    try:
        # If replace mode: delete existing scenes & clear stale analysis
        if payload.mode == "replace":
            from app.db.models import Fact, Event, Relationship, KnowledgeState, Issue, IssueReview, Claim, ResearchTask, PlotEvent, Entity

            entity_ids = [e[0] for e in db.query(Entity.id).filter(Entity.project_id == project_id).all()]

            db.query(IssueReview).filter(IssueReview.project_id == project_id).delete(synchronize_session=False)
            db.query(Issue).filter(Issue.project_id == project_id).delete(synchronize_session=False)
            db.query(ResearchTask).filter(ResearchTask.project_id == project_id).delete(synchronize_session=False)
            db.query(Claim).filter(Claim.project_id == project_id).delete(synchronize_session=False)
            db.query(Fact).filter(Fact.project_id == project_id).delete(synchronize_session=False)
            db.query(Relationship).filter(Relationship.project_id == project_id).delete(synchronize_session=False)
            db.query(KnowledgeState).filter(KnowledgeState.project_id == project_id).delete(synchronize_session=False)
            db.query(PlotEvent).filter(PlotEvent.project_id == project_id).delete(synchronize_session=False)
            db.query(SceneAnalysisRun).filter(SceneAnalysisRun.project_id == project_id).delete(synchronize_session=False)

            if entity_ids:
                db.query(Event).filter(Event.actor_entity_id.in_(entity_ids)).update({"actor_entity_id": None}, synchronize_session=False)
                db.query(Event).filter(Event.target_entity_id.in_(entity_ids)).update({"target_entity_id": None}, synchronize_session=False)
                db.query(Event).filter(Event.location_entity_id.in_(entity_ids)).update({"location_entity_id": None}, synchronize_session=False)

            db.query(Entity).filter(Entity.project_id == project_id).delete(synchronize_session=False)

            existing_scenes = db.query(Scene).filter(Scene.project_id == project_id).all()
            for s in existing_scenes:
                db.delete(s)
            db.flush()
            start_num = 1
        else:
            # Append mode: find max existing scene number
            max_scene = db.query(Scene).filter(Scene.project_id == project_id).order_by(Scene.scene_number.desc()).first()
            start_num = (max_scene.scene_number + 1) if max_scene else 1

        created_scenes = []
        for idx, s_data in enumerate(scenes_data):
            scene_num = start_num + idx
            scene_obj = Scene(
                project_id=project_id,
                scene_number=scene_num,
                raw_text=s_data["raw_text"],
                source_document_id=imported_doc.id,
                source_page_start=s_data.get("source_page_start"),
                source_page_end=s_data.get("source_page_end"),
                source_type="IMPORTED_DOCUMENT"
            )
            db.add(scene_obj)
            created_scenes.append(scene_obj)

        imported_doc.status = "IMPORTED"
        imported_doc.scene_count = len(created_scenes)
        imported_doc.error_message = None  # Clear preview JSON

        db.commit()

        logger.info(f"Successfully imported {len(created_scenes)} scenes for document {document_id} in project {project_id}.")

        return {
            "message": f"{len(created_scenes)} scenes imported successfully.",
            "document_id": document_id,
            "scenes_imported": len(created_scenes)
        }

    except Exception as e:
        db.rollback()
        imported_doc.status = "FAILED"
        imported_doc.error_message = str(e)
        db.commit()
        logger.error(f"Failed to confirm document import for {document_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Import failed. No scenes were added to the project: {str(e)}")


@router.get("", response_model=List[ImportedDocumentResponse])
def list_imported_documents(project_id: str, db: Session = Depends(get_db)):
    """Lists all imported documents for a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    return db.query(ImportedDocument)\
        .filter(ImportedDocument.project_id == project_id)\
        .order_by(ImportedDocument.created_at.desc())\
        .all()


@router.get("/{document_id}", response_model=ImportedDocumentResponse)
def get_imported_document(project_id: str, document_id: str, db: Session = Depends(get_db)):
    """Gets details for an imported document."""
    doc = db.query(ImportedDocument).filter(
        ImportedDocument.id == document_id,
        ImportedDocument.project_id == project_id
    ).first()

    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Imported document not found.")

    return doc


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_imported_document(project_id: str, document_id: str, db: Session = Depends(get_db)):
    """Deletes an imported document record."""
    doc = db.query(ImportedDocument).filter(
        ImportedDocument.id == document_id,
        ImportedDocument.project_id == project_id
    ).first()

    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Imported document not found.")

    db.delete(doc)
    db.commit()
