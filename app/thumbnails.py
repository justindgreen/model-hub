import hashlib
from pathlib import Path

import numpy as np
import trimesh

from app.config import THUMB_DIR


def _load(path: Path):
    mesh = trimesh.load(str(path), force="mesh")
    if isinstance(mesh, trimesh.Scene):
        mesh = mesh.dump(concatenate=True)
    return mesh


def mesh_stats(path: Path) -> dict:
    mesh = _load(path)
    verts = np.asarray(mesh.vertices)
    # geometry hash: stable under translation, robust-ish to minor float noise
    rounded = np.round(verts - verts.mean(axis=0), 3)
    geometry_hash = hashlib.sha256(rounded.tobytes()).hexdigest()
    bbox = mesh.bounding_box.extents.tolist() if len(verts) else [0, 0, 0]

    watertight = bool(getattr(mesh, "is_watertight", False))
    if watertight:
        volume_mm3 = abs(float(mesh.volume))
    else:
        # not a closed/manifold mesh -- trimesh's volume is meaningless there, so
        # fall back to the convex hull as a (larger, approximate) upper bound
        try:
            volume_mm3 = abs(float(mesh.convex_hull.volume))
        except Exception:
            volume_mm3 = None

    return {
        "geometry_hash": geometry_hash,
        "vertex_count": int(len(mesh.vertices)),
        "face_count": int(len(mesh.faces)) if hasattr(mesh, "faces") else 0,
        "bbox": tuple(bbox),
        "volume_mm3": volume_mm3,
        "is_watertight": watertight,
    }


def generate_thumbnail(path: Path, size: int = 512) -> str:
    """Render an isometric snapshot of the mesh to a PNG in THUMB_DIR.
    Returns the thumbnail filename (relative to THUMB_DIR), or None on failure.

    Uses matplotlib exclusively (not trimesh's pyglet/GL scene renderer) --
    that renderer needs a working X/EGL context, which is unreliable in a
    minimal headless container (xvfb-run's readiness check can hang with no
    clear error). matplotlib needs no display server at all.
    """
    mesh = _load(path)
    png = _matplotlib_fallback(mesh, size)

    if png is None:
        return None

    out_name = hashlib.sha1(str(path).encode()).hexdigest() + ".png"
    out_path = THUMB_DIR / out_name
    with open(out_path, "wb") as f:
        f.write(png)
    return out_name


def _matplotlib_fallback(mesh, size: int) -> bytes:
    import io
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    fig = plt.figure(figsize=(size / 100, size / 100), dpi=100)
    ax = fig.add_subplot(projection="3d")
    faces = mesh.vertices[mesh.faces]
    collection = Poly3DCollection(faces, facecolor="#4f8ef7", edgecolor="none", linewidths=0)
    ax.add_collection3d(collection)
    bounds = mesh.bounds
    ax.set_xlim(bounds[0][0], bounds[1][0])
    ax.set_ylim(bounds[0][1], bounds[1][1])
    ax.set_zlim(bounds[0][2], bounds[1][2])
    ax.set_box_aspect((1, 1, 1))
    ax.axis("off")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", transparent=True)
    plt.close(fig)
    return buf.getvalue()
