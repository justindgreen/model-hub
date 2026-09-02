from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlmodel import Session, select
from typing import Optional

from app.db import get_session
from app.models import Model3D, Tag
from app.config import LIBRARY_PATH, THUMB_DIR
from app.scanner import scan_library, import_uploaded_file
from app.ai.tagging import semantic_search
from app.estimate import estimate_print

router = APIRouter(prefix="/api/library", tags=["library"])


@router.post("/scan")
def trigger_scan(session: Session = Depends(get_session)):
    return scan_library(session)


@router.get("/models")
def list_models(
    q: Optional[str] = None,
    tag: Optional[str] = None,
    extension: Optional[str] = None,
    duplicates_only: bool = False,
    limit: int = 200,
    offset: int = 0,
    session: Session = Depends(get_session),
):
    stmt = select(Model3D)
    if extension:
        stmt = stmt.where(Model3D.extension == extension)
    if duplicates_only:
        stmt = stmt.where(Model3D.is_duplicate_of.is_not(None))
    models = session.exec(stmt.offset(offset).limit(limit)).all()

    if q:
        ql = q.lower()
        models = [m for m in models if ql in m.filename.lower()
                  or (m.ai_description and ql in m.ai_description.lower())]
    if tag:
        models = [m for m in models if tag.lower() in [t.name for t in m.tags]]
    return models


@router.post("/import")
async def import_file(
    file: UploadFile = File(...),
    source_url: Optional[str] = Form(None),
    designer: Optional[str] = Form(None),
    license: Optional[str] = Form(None),
    session: Session = Depends(get_session),
):
    """Receives a model file pushed from the Model Hub browser extension
    (or any other client) and files it into the library."""
    content = await file.read()
    try:
        model = import_uploaded_file(
            session, file.filename, content,
            source_url=source_url, designer=designer, license=license,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    return model


@router.get("/search/semantic")
def search_semantic(q: str, limit: int = 25, session: Session = Depends(get_session)):
    results = semantic_search(session, q, limit)
    return results


@router.get("/models/{model_id}")
def get_model(model_id: int, session: Session = Depends(get_session)):
    model = session.get(Model3D, model_id)
    if not model:
        raise HTTPException(404, "Model not found")
    return model


@router.patch("/models/{model_id}")
def update_model(model_id: int, payload: dict, session: Session = Depends(get_session)):
    model = session.get(Model3D, model_id)
    if not model:
        raise HTTPException(404, "Model not found")
    for field in ("source_url", "designer", "license", "filename"):
        if field in payload:
            setattr(model, field, payload[field])
    session.add(model)
    session.commit()
    session.refresh(model)
    return model


@router.get("/models/{model_id}/file")
def download_model(model_id: int, session: Session = Depends(get_session)):
    model = session.get(Model3D, model_id)
    if not model:
        raise HTTPException(404, "Model not found")
    full_path = LIBRARY_PATH / model.path
    if not full_path.exists():
        raise HTTPException(404, "File missing on disk")
    return FileResponse(full_path, filename=model.filename)


@router.get("/models/{model_id}/estimate")
def estimate_model_print(
    model_id: int, material: str = "PLA", infill: float = 0.15,
    session: Session = Depends(get_session),
):
    model = session.get(Model3D, model_id)
    if not model:
        raise HTTPException(404, "Model not found")
    full_path = LIBRARY_PATH / model.path
    if not full_path.exists():
        raise HTTPException(404, "File missing on disk")
    return estimate_print(model, full_path, material=material, infill=infill)


@router.get("/thumbnails/{filename}")
def get_thumbnail(filename: str):
    path = THUMB_DIR / filename
    if not path.exists():
        raise HTTPException(404, "Thumbnail not found")
    return FileResponse(path)


@router.delete("/models/{model_id}")
def delete_model_record(model_id: int, session: Session = Depends(get_session)):
    """Removes the DB record only. Does not touch the file on disk."""
    model = session.get(Model3D, model_id)
    if not model:
        raise HTTPException(404, "Model not found")
    session.delete(model)
    session.commit()
    return {"status": "deleted"}
