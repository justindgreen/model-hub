from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.db import get_session
from app.models import QueueItem, Filament

router = APIRouter(prefix="/api/queue", tags=["queue"])


@router.get("")
def list_queue(session: Session = Depends(get_session)):
    items = session.exec(select(QueueItem).order_by(QueueItem.position)).all()
    return items


@router.post("")
def add_to_queue(payload: dict, session: Session = Depends(get_session)):
    max_pos = session.exec(select(QueueItem).order_by(QueueItem.position.desc())).first()
    position = (max_pos.position + 1) if max_pos else 0
    item = QueueItem(
        model_id=payload["model_id"],
        filament_id=payload.get("filament_id"),
        notes=payload.get("notes"),
        estimated_grams=payload.get("estimated_grams"),
        estimated_minutes=payload.get("estimated_minutes"),
        position=position,
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.patch("/{item_id}")
def update_queue_item(item_id: int, payload: dict, session: Session = Depends(get_session)):
    item = session.get(QueueItem, item_id)
    if not item:
        raise HTTPException(404, "Not found")

    was_done = item.status == "done"
    for field in ("status", "position", "filament_id", "notes", "estimated_grams", "estimated_minutes"):
        if field in payload:
            setattr(item, field, payload[field])

    # deduct consumed filament exactly once, the moment a job transitions into "done"
    if item.status == "done" and not was_done and item.filament_id and item.estimated_grams:
        spool = session.get(Filament, item.filament_id)
        if spool:
            spool.remaining_g = max(0.0, spool.remaining_g - item.estimated_grams)
            session.add(spool)

    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.delete("/{item_id}")
def remove_queue_item(item_id: int, session: Session = Depends(get_session)):
    item = session.get(QueueItem, item_id)
    if not item:
        raise HTTPException(404, "Not found")
    session.delete(item)
    session.commit()
    return {"status": "deleted"}
