import base64
import json
from typing import List

import httpx

from app.config import DEFAULT_OLLAMA_HOST, DEFAULT_OLLAMA_VISION_MODEL, DEFAULT_OLLAMA_EMBED_MODEL
from app.ai import AIProvider


class OllamaProvider(AIProvider):
    """Runs entirely against a local (or LAN) Ollama instance. No data leaves the network."""

    def __init__(self, host: str = None, vision_model: str = None, embed_model: str = None):
        self.host = (host or DEFAULT_OLLAMA_HOST).rstrip("/")
        self.vision_model = vision_model or DEFAULT_OLLAMA_VISION_MODEL
        self.embed_model = embed_model or DEFAULT_OLLAMA_EMBED_MODEL

    def tag_image(self, image_path: str) -> dict:
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()

        prompt = (
            "Look at this 3D printable model render. Reply ONLY with JSON: "
            '{"tags": ["...", "..."], "description": "one sentence"}. '
            "Tags should be short, lowercase, e.g. object type, category, use-case."
        )
        resp = httpx.post(
            f"{self.host}/api/generate",
            json={
                "model": self.vision_model,
                "prompt": prompt,
                "images": [b64],
                "stream": False,
                "format": "json",
            },
            timeout=120,
        )
        resp.raise_for_status()
        raw = resp.json().get("response", "{}")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {"tags": [], "description": raw.strip()[:200]}
        return {
            "tags": [t.lower().strip() for t in data.get("tags", []) if t],
            "description": data.get("description", ""),
        }

    def embed_text(self, text: str) -> List[float]:
        resp = httpx.post(
            f"{self.host}/api/embeddings",
            json={"model": self.embed_model, "prompt": text},
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json().get("embedding", [])
