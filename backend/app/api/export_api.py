import re
import urllib.parse
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from fastapi.responses import Response, JSONResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Project, Scene
from app.services.exporter import (
    generate_pdf_export,
    generate_docx_export,
    generate_fountain_export,
    parse_fountain_import
)

router = APIRouter(prefix="/api/projects", tags=["Script Export & Import Engine"])

@router.get("/{project_id}/export")
def export_screenplay(
    project_id: str,
    format: str = Query("pdf", description="Export format: 'pdf', 'docx', or 'fountain'"),
    font_family: str = Query("Courier", description="Font family: 'Courier', 'Helvetica', 'Times-Roman'"),
    font_size: int = Query(12, ge=8, le=18, description="Font size (8pt to 18pt)"),
    db: Session = Depends(get_db)
):
    """
    Exports the full project screenplay into PDF, DOCX, or Fountain plain text format.
    Includes industry standard formatting, customizable typography, and orphan header prevention.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found."
        )

    scenes = db.query(Scene).filter(Scene.project_id == project_id).order_by(Scene.scene_number).all()
    if not scenes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project has no scenes to export."
        )

    scenes_text = [s.raw_text for s in scenes]
    safe_title = re.sub(r'[^a-zA-Z0-9_\-]', '_', project.title) or "Screenplay"

    format_clean = format.lower().strip()

    if format_clean == "pdf":
        pdf_bytes = generate_pdf_export(
            scenes_text=scenes_text,
            font_family=font_family,
            font_size=font_size
        )
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{safe_title}.pdf"'
            }
        )

    elif format_clean in ("docx", "doc"):
        docx_bytes = generate_docx_export(
            scenes_text=scenes_text,
            font_family=font_family,
            font_size=font_size
        )
        return Response(
            content=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f'attachment; filename="{safe_title}.docx"'
            }
        )

    elif format_clean in ("fountain", "txt"):
        fountain_str = generate_fountain_export(scenes_text)
        return Response(
            content=fountain_str.encode("utf-8"),
            media_type="text/plain",
            headers={
                "Content-Disposition": f'attachment; filename="{safe_title}.fountain"'
            }
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported export format '{format}'. Supported formats: 'pdf', 'docx', 'fountain'."
        )


@router.post("/{project_id}/import-script")
async def import_screenplay_script(
    project_id: str,
    file: UploadFile = File(...),
    replace_existing: bool = Query(False, description="Whether to replace existing scenes in project"),
    db: Session = Depends(get_db)
):
    """
    Imports a Fountain (.fountain) or plain text screenplay file into scenes for a project.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found."
        )

    try:
        content_bytes = await file.read()
        content_text = content_bytes.decode("utf-8", errors="replace")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not read uploaded script file: {str(e)}"
        )

    parsed_scenes = parse_fountain_import(content_text)
    if not parsed_scenes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid screenplay scenes could be parsed from the file."
        )

    if replace_existing:
        db.query(Scene).filter(Scene.project_id == project_id).delete(synchronize_session=False)
        start_number = 1
    else:
        max_scene = db.query(Scene).filter(Scene.project_id == project_id).order_by(Scene.scene_number.desc()).first()
        start_number = (max_scene.scene_number + 1) if max_scene else 1

    created_count = 0
    for idx, sc_data in enumerate(parsed_scenes):
        scene_num = start_number + idx
        new_scene = Scene(
            project_id=project_id,
            scene_number=scene_num,
            raw_text=sc_data["raw_text"],
            source_type="FOUNTAIN_IMPORT"
        )
        db.add(new_scene)
        created_count += 1

    db.commit()

    return {
        "status": "success",
        "imported_scenes": created_count,
        "message": f"Successfully imported {created_count} scenes into '{project.title}'."
    }
