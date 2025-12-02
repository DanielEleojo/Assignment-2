from __future__ import annotations

import base64
import mimetypes
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

from .config import get_settings


def _detect_mime(path: Path) -> str:
    mime, _ = mimetypes.guess_type(path)
    if not mime:
        raise ValueError(f"Could not detect MIME type for {path}")
    return mime


def _read_image(path: Path) -> dict[str, str]:
    mime_type = _detect_mime(path)
    raw = path.read_bytes()
    b64 = base64.b64encode(raw).decode("utf-8")
    return {"mime_type": mime_type, "data": b64}


@dataclass
class LLMResponse:
    text: str
    latency_ms: float
    prompt_tokens: int | None
    response_tokens: int | None


def _init_model():
    settings = get_settings()
    genai.configure(api_key=settings.gemini_api_key)
    return genai.GenerativeModel(
        model_name=settings.model_name,
        system_instruction=settings.system_prompt,
    )


_model = None


def _get_model():
    global _model
    if _model is None:
        _model = _init_model()
    return _model


def interpret_meme(
    conversation: str,
    cheat_context: str,
    caption: str | None,
    image_path: Path | None,
) -> LLMResponse:
    settings = get_settings()
    model = _get_model()
    parts: list[Any] = []
    parts.append(
        (
            "You are interpreting a meme for a user. Conversation background:\n"
            f"{conversation}\n"
        )
    )
    if caption:
        parts.append(f"User-provided meme caption or textual description:\n{caption}\n")
    if cheat_context:
        parts.append("Reference insights from the cheat sheet:\n" + cheat_context + "\n")
    parts.append(
        "Respond with one concise paragraph (<=80 words) that summarizes what this meme conveys in this conversation,"
        " focusing on the sender's intent and how the recipients likely interpret it."
        " Skip numbered lists or extra sections—just explain the meaning in plain language."
    )

    if image_path:
        parts.insert(1, _read_image(image_path))

    start = time.perf_counter()
    try:
        response = model.generate_content(parts)
    except google_exceptions.NotFound as exc:  # provide actionable hint
        raise RuntimeError(
            f"Gemini model '{settings.model_name}' is unavailable for this API key. "
            "Set GEMINI_MODEL=gemini-2.5-flash or pick another model from ListModels."
        ) from exc
    latency_ms = (time.perf_counter() - start) * 1000

    text = response.text or ""
    usage = getattr(response, "usage_metadata", None)
    prompt_tokens = getattr(usage, "prompt_token_count", None) if usage else None
    response_tokens = getattr(usage, "candidates_token_count", None) if usage else None
    return LLMResponse(
        text=text.strip(),
        latency_ms=latency_ms,
        prompt_tokens=prompt_tokens,
        response_tokens=response_tokens,
    )
