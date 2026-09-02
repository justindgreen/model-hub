from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.db import get_session
from app.models import Tag, Model3D

router = APIRouter(prefix="/api/tags", tags=["tags"])


@router.get("")
def list_tags(session: Session = Depends(get_session)):
    return session.exec(select(Tag)).all()


@router.post("/models/{model_id}")
def add_tag(model_id: int, payload: dict, session: Session = Depends(get_session)):
    model = session.get(Model3D, model_id)
    if not model:
        raise HTTPException(404, "Model not found")
    name = payload["name"].strip().lower()
    tag = session.exec(select(Tag).where(Tag.name == name)).first()
    if not tag:
        tag = Tag(name=name, ai_generated=False)
        session.add(tag)
        session.commit()
        session.refresh(tag)
    if tag not in model.tags:
        model.tags.append(tag)
        session.add(model)
        session.commit()
    return model


@router.delete("/models/{model_id}/{tag_name}")
def remove_tag(model_id: int, tag_name: str, session: Session = Depends(get_session)):
    model = session.get(Model3D, model_id)
    if not model:
        raise HTTPException(404, "Model not found")
    model.tags = [t for t in model.tags if t.name != tag_name.lower()]
    session.add(model)
    session.commit()
    return model
