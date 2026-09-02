from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.db import get_session
from app.models import Filament

router = APIRouter(prefix="/api/filament", tags=["filament"])


@router.get("")
def list_filament(session: Session = Depends(get_session)):
    return session.exec(select(Filament)).all()


@router.post("")
def create_filament(payload: dict, session: Session = Depends(get_session)):
    f = Filament(**payload)
    session.add(f)
    session.commit()
    session.refresh(f)
    return f


@router.patch("/{filament_id}")
def update_filament(filament_id: int, payload: dict, session: Session = Depends(get_session)):
    f = session.get(Filament, filament_id)
    if not f:
        raise HTTPException(404, "Not found")
    for k, v in payload.items():
        if hasattr(f, k):
            setattr(f, k, v)
    session.add(f)
    session.commit()
    session.refresh(f)
    return f


@router.post("/{filament_id}/consume")
def consume_filament(filament_id: int, payload: dict, session: Session = Depends(get_session)):
    f = session.get(Filament, filament_id)
    if not f:
        raise HTTPException(404, "Not found")
    grams = float(payload.get("grams", 0))
    f.remaining_g = max(0.0, f.remaining_g - grams)
    session.add(f)
    session.commit()
    session.refresh(f)
    return f


@router.delete("/{filament_id}")
def delete_filament(filament_id: int, session: Session = Depends(get_session)):
    f = session.get(Filament, filament_id)
    if not f:
        raise HTTPException(404, "Not found")
    session.delete(f)
    session.commit()
    return {"status": "deleted"}
