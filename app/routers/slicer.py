from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.db import get_session
from app.models import Model3D
from app.settings_store import get_setting

router = APIRouter(prefix="/api/slicer", tags=["slicer"])

# Slicers Meshory hands off to; here we just expose the same catalog so the
# frontend can offer "Open in <slicer>" -- since the app runs in a container,
# not on the user's desktop, "opening" means: give the slicer a path it can
# read (via the same share Unraid already exports) plus a direct download URL.
KNOWN_SLICERS = [
    "Bambu Studio", "Cura", "PrusaSlicer", "OrcaSlicer", "SuperSlicer",
    "Simplify3D", "Chitubox", "Lychee Slicer", "IdeaMaker", "Repetier-Host",
    "Slic3r", "KISSlicer", "Creality Print", "Snapmaker Luban", "FlashPrint",
]


@router.get("/list")
def list_slicers():
    return KNOWN_SLICERS


@router.get("/handoff/{model_id}")
def handoff(model_id: int, session: Session = Depends(get_session)):
    model = session.get(Model3D, model_id)
    if not model:
        raise HTTPException(404, "Model not found")

    share_prefix = get_setting(session, "unraid_share_path", "\\\\TOWER\\meshory-library")
    win_path = model.path.replace("/", "\\")
    network_path = share_prefix.rstrip("/\\") + "\\" + win_path
    return {
        "download_url": f"/api/library/models/{model_id}/file",
        "network_path": network_path,
        "filename": model.filename,
        "hint": (
            "Point your slicer's watched/import folder at the same share Unraid exports "
            "for this library, or download the file directly and open it manually -- the "
            "slicer itself always runs on your desktop, not inside this container."
        ),
    }
