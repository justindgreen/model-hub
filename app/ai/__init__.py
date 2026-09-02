from abc import ABC, abstractmethod
from typing import List, Optional


class AIProvider(ABC):
    @abstractmethod
    def tag_image(self, image_path: str) -> dict:
        """Return {'tags': [str, ...], 'description': str}"""

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Return an embedding vector for semantic search."""


def get_provider(session) -> Optional[AIProvider]:
    from app.settings_store import get_setting
    from app.ai.ollama_provider import OllamaProvider
    from app.ai.api_provider import APIProvider

    mode = get_setting(session, "ai_mode", "local")  # "local" | "api" | "off"
    if mode == "off":
        return None
    if mode == "api":
        api_key = get_setting(session, "ai_api_key", "")
        api_base = get_setting(session, "ai_api_base", "https://openrouter.ai/api/v1")
        model = get_setting(session, "ai_api_model", "openai/gpt-4o-mini")
        if not api_key:
            return None
        return APIProvider(api_key=api_key, api_base=api_base, model=model)

    host = get_setting(session, "ollama_host", None)
    vision_model = get_setting(session, "ollama_vision_model", None)
    embed_model = get_setting(session, "ollama_embed_model", None)
    return OllamaProvider(host=host, vision_model=vision_model, embed_model=embed_model)
