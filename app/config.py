import os
from pathlib import Path

LIBRARY_PATH = Path(os.environ.get("LIBRARY_PATH", "/data"))
CONFIG_PATH = Path(os.environ.get("CONFIG_PATH", "/config"))
CONFIG_PATH.mkdir(parents=True, exist_ok=True)

DB_PATH = CONFIG_PATH / "meshory.db"
THUMB_DIR = CONFIG_PATH / "thumbnails"
THUMB_DIR.mkdir(parents=True, exist_ok=True)

SUPPORTED_EXTENSIONS = {
    ".stl", ".3mf", ".obj", ".step", ".stp", ".fbx",
    ".zip", ".rar", ".7z",
    ".txt", ".svg", ".3dm",
}
MESH_EXTENSIONS = {".stl", ".3mf", ".obj", ".fbx"}

# AI provider defaults, overridden at runtime via the Settings table
DEFAULT_OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://ollama:11434")
DEFAULT_OLLAMA_VISION_MODEL = os.environ.get("OLLAMA_VISION_MODEL", "llava")
DEFAULT_OLLAMA_EMBED_MODEL = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text")

SCAN_INTERVAL_SECONDS = int(os.environ.get("SCAN_INTERVAL_SECONDS", "300"))
