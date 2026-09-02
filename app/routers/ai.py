from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session, select
from app.db import get_session
from app.models import Model3D
from app.ai.tagging import tag_model
from app.ai import get_provider

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.get("/status")
def ai_status(session: Session = Depends(get_session)):
    provider = get_provider(session)
    return {"configured": provider is not None, "provider": type(provider).__name__ if provider else None}


@router.post("/tag/{model_id}")
def tag_single(model_id: int, session: Session = Depends(get_session)):
    model = session.get(Model3D, model_id)
    if not model:
        raise HTTPException(404, "Model not found")
    return tag_model(session, model)


_job_state = {"running": False, "done": 0, "total": 0, "cancel": False, "estimated_cost_usd": 0.0}


def _run_batch_tagging(model_ids: list[int]):
    from app.db import engine
    from sqlmodel import Session as _S
    from app.ai.api_provider import APIProvider
    from app.settings_store import get_setting

    _job_state.update(running=True, done=0, total=len(model_ids), cancel=False, estimated_cost_usd=0.0)
    with _S(engine) as session:
        provider = get_provider(session)
        cost_per_call = float(get_setting(session, "ai_api_cost_per_call_usd", "0.002"))
        is_paid = isinstance(provider, APIProvider)
        for mid in model_ids:
            if _job_state["cancel"]:
                break
            model = session.get(Model3D, mid)
            if model and not model.ai_tagged:
                try:
                    tag_model(session, model)
                    if is_paid:
                        _job_state["estimated_cost_usd"] += cost_per_call
                except Exception:
                    pass
            _job_state["done"] += 1
        from app.notify import notify
        notify(session, "Meshory: tagging finished",
               f"Tagged {_job_state['done']}/{_job_state['total']} model(s)." +
               (f" Est. cost: ${_job_state['estimated_cost_usd']:.3f}" if _job_state["estimated_cost_usd"] else ""))
    _job_state["running"] = False


@router.post("/tag-all")
def tag_all(background_tasks: BackgroundTasks, only_untagged: bool = True,
            session: Session = Depends(get_session)):
    if _job_state["running"]:
        raise HTTPException(409, "A tagging job is already running")
    stmt = select(Model3D)
    if only_untagged:
        stmt = stmt.where(Model3D.ai_tagged == False)  # noqa: E712
    ids = [m.id for m in session.exec(stmt).all()]
    background_tasks.add_task(_run_batch_tagging, ids)
    return {"status": "started", "count": len(ids)}


@router.post("/tag-all/pause")
def pause_tagging():
    _job_state["cancel"] = True
    return {"status": "pausing"}


@router.get("/tag-all/status")
def tag_all_status():
    return _job_state
