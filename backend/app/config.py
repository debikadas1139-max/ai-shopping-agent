"""Application settings, read from environment variables (and backend/.env)."""

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

# backend/ folder (parent of app/). Used so paths never depend on where you run Python from.
BACKEND_DIR = Path(__file__).resolve().parent.parent

# Loads backend/.env into os.environ. Real environment variables win over the file.
load_dotenv(BACKEND_DIR / ".env")

PLACEHOLDER_KEY = "your_groq_api_key_here"


def _sqlite_path(database_url: str) -> Path:
    """Turn 'sqlite:///./store.db' into an absolute Path."""
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        raise ValueError("DATABASE_URL must look like sqlite:///./store.db")
    raw = database_url[len(prefix):]
    path = Path(raw)
    if not path.is_absolute():
        path = BACKEND_DIR / path
    return path.resolve()


@dataclass(frozen=True)
class Settings:
    groq_api_key: str
    groq_model: str
    groq_vision_model: str
    database_path: Path
    frontend_origins: list
    upload_dir: Path
    max_image_bytes: int

    @property
    def ai_configured(self) -> bool:
        """True when a real-looking Groq key is present (the key itself is never exposed)."""
        return bool(self.groq_api_key) and self.groq_api_key != PLACEHOLDER_KEY


@lru_cache
def get_settings() -> Settings:
    origins = [o.strip() for o in os.getenv("FRONTEND_ORIGIN", "http://localhost:5173").split(",") if o.strip()]
    # Browsers treat localhost and 127.0.0.1 as different origins, so allow both.
    extra = []
    for origin in origins:
        if "localhost" in origin:
            extra.append(origin.replace("localhost", "127.0.0.1"))
    origins = list(dict.fromkeys(origins + extra))

    return Settings(
        groq_api_key=os.getenv("GROQ_API_KEY", "").strip(),
        groq_model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b").strip(),
        groq_vision_model=os.getenv("GROQ_VISION_MODEL", "qwen/qwen3.6-27b").strip(),
        database_path=_sqlite_path(os.getenv("DATABASE_URL", "sqlite:///./store.db").strip()),
        frontend_origins=origins,
        upload_dir=BACKEND_DIR / "uploads",
        # Groq limits base64 images to about 4 MB. Base64 adds ~33%, so keep files under 3 MB.
        max_image_bytes=3 * 1024 * 1024,
    )
