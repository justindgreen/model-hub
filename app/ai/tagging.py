import struct
import logging
from typing import List

from sqlmodel import Session, select

from app.config import THUMB_DIR
from app.models import Model3D, Tag
from app.ai import get_provider

logger = logging.getLogger("modelhub.tagging")


def pack_embedding(vec: List[float]) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec)


def unpack_embedding(blob: bytes) -> List[float]:
    n = len(blob) // 4
    return list(struct.unpack(f"{n}f", blob))


def cosine_similarity(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def tag_model(session: Session, model: Model3D) -> dict:
    provider = get_provider(session)
    if provider is None:
        return {"status": "skipped", "reason": "AI disabled or not configured"}
    if not model.thumbnail_path:
        return {"status": "skipped", "reason": "no thumbnail"}

    thumb_full = THUMB_DIR / model.thumbnail_path
    result = provider.tag_image(str(thumb_full))

    for tag_name in result["tags"]:
        tag = session.exec(select(Tag).where(Tag.name == tag_name)).first()
        if not tag:
            tag = Tag(name=tag_name, ai_generated=True)
            session.add(tag)
            session.commit()
            session.refresh(tag)
        if tag not in model.tags:
            model.tags.append(tag)

    model.ai_description = result["description"]
    model.ai_tagged = True

    try:
        embed_text = f"{model.filename} {result['description']} {' '.join(result['tags'])}"
        vec = provider.embed_text(embed_text)
        if vec:
            model.embedding = pack_embedding(vec)
    except Exception as e:
        logger.warning("Embedding failed for %s: %s", model.filename, e)

    session.add(model)
    session.commit()
    return {"status": "ok", "tags": result["tags"], "description": result["description"]}


def semantic_search(session: Session, query: str, limit: int = 25) -> List[Model3D]:
    provider = get_provider(session)
    if provider is None:
        return []
    query_vec = provider.embed_text(query)
    if not query_vec:
        return []

    scored = []
    for model in session.exec(select(Model3D).where(Model3D.embedding.is_not(None))).all():
        vec = unpack_embedding(model.embedding)
        score = cosine_similarity(query_vec, vec)
        scored.append((score, model))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in scored[:limit]]
