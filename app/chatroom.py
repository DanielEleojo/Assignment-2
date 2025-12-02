from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .config import get_settings


@dataclass
class ChatMessage:
    author: str
    text: str
    timestamp: str

    def render(self) -> str:
        ts = self.timestamp
        return f"[{ts}] {self.author}: {self.text}"


@dataclass
class ChatThread:
    chat_id: int
    title: str
    description: str
    messages: list[ChatMessage]

    def pretty(self) -> str:
        header = f"Chat #{self.chat_id} — {self.title}"
        desc = f"{self.description}".strip()
        body = "\n".join(msg.render() for msg in self.messages) or "(no messages yet)"
        if desc:
            return f"{header}\n{desc}\n{body}"
        return f"{header}\n{body}"

    def as_prompt_context(self, last_n: int = 20) -> str:
        relevant = self.messages[-last_n:]
        lines = [msg.render() for msg in relevant]
        return f"Conversation from chat '{self.title}':\n" + "\n".join(lines)


class ChatStore:
    def __init__(self, path: Path | None = None) -> None:
        settings = get_settings()
        self.path = path or settings.chat_store_path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _default_state(self) -> dict:
        return {"next_id": 1, "threads": []}

    def _load_state(self) -> dict:
        if not self.path.exists():
            return self._default_state()
        with self.path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _save_state(self, state: dict) -> None:
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump(state, handle, indent=2)

    def _thread_from_dict(self, payload: dict) -> ChatThread:
        messages = [ChatMessage(**msg) for msg in payload.get("messages", [])]
        return ChatThread(
            chat_id=payload["chat_id"],
            title=payload.get("title", "Untitled chat"),
            description=payload.get("description", ""),
            messages=messages,
        )

    def list_threads(self) -> list[ChatThread]:
        state = self._load_state()
        return [self._thread_from_dict(item) for item in state.get("threads", [])]

    def get_thread(self, chat_id: int) -> ChatThread:
        state = self._load_state()
        for item in state.get("threads", []):
            if item["chat_id"] == chat_id:
                return self._thread_from_dict(item)
        raise ValueError(f"Chat #{chat_id} does not exist.")

    def create_thread(self, title: str, description: str = "") -> ChatThread:
        state = self._load_state()
        chat_id = state.get("next_id", 1)
        thread = {
            "chat_id": chat_id,
            "title": title,
            "description": description,
            "messages": [],
        }
        state.setdefault("threads", []).append(thread)
        state["next_id"] = chat_id + 1
        self._save_state(state)
        return self._thread_from_dict(thread)

    def add_message(self, chat_id: int, author: str, text: str) -> ChatMessage:
        if not text.strip():
            raise ValueError("Message text cannot be empty.")
        state = self._load_state()
        for item in state.get("threads", []):
            if item["chat_id"] == chat_id:
                timestamp = datetime.now(timezone.utc).isoformat()
                message = ChatMessage(author=author or "anon", text=text.strip(), timestamp=timestamp)
                item.setdefault("messages", []).append(message.__dict__)
                self._save_state(state)
                return message
        raise ValueError(f"Chat #{chat_id} does not exist.")

    def append_messages(self, chat_id: int, messages: Iterable[ChatMessage]) -> None:
        state = self._load_state()
        for item in state.get("threads", []):
            if item["chat_id"] == chat_id:
                item.setdefault("messages", []).extend(msg.__dict__ for msg in messages)
                self._save_state(state)
                return
        raise ValueError(f"Chat #{chat_id} does not exist.")