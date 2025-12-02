from __future__ import annotations

import json
import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable

import google.generativeai as genai

from .config import get_settings


@dataclass
class CheatSheetEntry:
    entry_id: str
    title: str
    summary: str
    guidance: str
    tags: list[str]

    @property
    def searchable_text(self) -> str:
        tag_blob = ", ".join(self.tags)
        return f"{self.title}. {self.summary}. Guidance: {self.guidance}. Tags: {tag_blob}."


@dataclass
class CheatMatch:
    entry: CheatSheetEntry
    score: float


def _load_entries(path: Path) -> list[CheatSheetEntry]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    return [
        CheatSheetEntry(
            entry_id=item.get("id", str(idx)),
            title=item["title"],
            summary=item["summary"],
            guidance=item["guidance"],
            tags=item.get("tags", []),
        )
        for idx, item in enumerate(raw)
    ]


def _embed(text: str) -> list[float]:
    settings = get_settings()
    genai.configure(api_key=settings.gemini_api_key)
    result = genai.embed_content(model=settings.embed_model_name, content=text)
    return result.get("embedding", [])


def _normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vec)) or 1.0
    return [value / norm for value in vec]


def _load_index() -> tuple[list[CheatSheetEntry], list[list[float]]]:
    settings = get_settings()
    path = settings.cheatsheet_path
    fingerprint = path.stat().st_mtime if path.exists() else 0.0
    return _load_index_cached(str(path), fingerprint)


@lru_cache(maxsize=4)
def _load_index_cached(path_str: str, fingerprint: float) -> tuple[list[CheatSheetEntry], list[list[float]]]:
    path = Path(path_str)
    entries = _load_entries(path)
    if not entries:
        return [], []
    embeddings = [_normalize(_embed(entry.searchable_text)) for entry in entries]
    return entries, embeddings


def _cosine(query_vec: list[float], doc_vec: list[float]) -> float:
    return sum(q * d for q, d in zip(query_vec, doc_vec))


def retrieve_matches(query: str, top_k: int = 3) -> list[CheatMatch]:
    entries, embeddings = _load_index()
    if not entries:
        return []
    query_vec = _normalize(_embed(query))
    scored = [CheatMatch(entry=entry, score=_cosine(query_vec, doc_vec)) for entry, doc_vec in zip(entries, embeddings)]
    scored.sort(key=lambda item: item.score, reverse=True)
    return scored[:top_k]


def format_cheat_context(matches: Iterable[CheatMatch]) -> str:
    matches = list(matches)
    if not matches:
        return ""
    lines = ["Cheat sheet insights for grounding:"]
    for match in matches:
        lines.append(
            f"- {match.entry.title}: {match.entry.guidance}"
        )
    return "\n".join(lines)


def build_cheat_context(conversation: str, caption: str | None, top_k: int = 3) -> tuple[str, list[CheatMatch]]:
    query = "\n".join(filter(None, [caption, conversation]))
    matches = retrieve_matches(query, top_k=top_k)
    return format_cheat_context(matches), matches
