from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


DEFAULT_MODEL_NAME = "gemini-2.5-flash"
DEFAULT_MAX_INPUT_CHARS = 4000
DEFAULT_SYSTEM_PROMPT = (
    "You are MemeSensei, a cultural analyst that explains internet memes. "
    "Always connect the meme to the user's conversation context, call out "
    "hidden assumptions, and offer respectful guidance. Refuse harmful, "
    "hateful, or policy-violating requests."
)
DEFAULT_UPLOADS_PATH = Path("uploads")
DEFAULT_FLASK_SECRET = "dev-secret"
DEFAULT_CHEATSHEET_PATH = Path("data/cheatsheets.json")
DEFAULT_EMBED_MODEL = "models/text-embedding-004"


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str
    model_name: str = DEFAULT_MODEL_NAME
    max_input_chars: int = DEFAULT_MAX_INPUT_CHARS
    telemetry_path: Path = Path("logs/telemetry.csv")
    chat_store_path: Path = Path("data/chats.json")
    uploads_path: Path = DEFAULT_UPLOADS_PATH
    system_prompt: str = DEFAULT_SYSTEM_PROMPT
    flask_secret_key: str = DEFAULT_FLASK_SECRET
    cheatsheet_path: Path = DEFAULT_CHEATSHEET_PATH
    embed_model_name: str = DEFAULT_EMBED_MODEL


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing. Populate .env or environment variables.")
    return Settings(
        gemini_api_key=api_key,
        model_name=os.getenv("GEMINI_MODEL", DEFAULT_MODEL_NAME),
        max_input_chars=int(os.getenv("MAX_INPUT_CHARS", DEFAULT_MAX_INPUT_CHARS)),
        system_prompt=os.getenv("SYSTEM_PROMPT", DEFAULT_SYSTEM_PROMPT),
        chat_store_path=Path(os.getenv("CHAT_STORE_PATH", "data/chats.json")),
        uploads_path=Path(os.getenv("UPLOADS_PATH", str(DEFAULT_UPLOADS_PATH))),
        flask_secret_key=os.getenv("FLASK_SECRET_KEY", DEFAULT_FLASK_SECRET),
        cheatsheet_path=Path(os.getenv("CHEATSHEET_PATH", str(DEFAULT_CHEATSHEET_PATH))),
        embed_model_name=os.getenv("EMBED_MODEL_NAME", DEFAULT_EMBED_MODEL),
    )
