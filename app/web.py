from __future__ import annotations

from pathlib import Path
from typing import Optional
from uuid import uuid4

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from werkzeug.utils import secure_filename

from .chatroom import ChatStore
from .config import get_settings
from .guardrails import run_guardrails
from .llm_client import interpret_meme
from .rag import CheatMatch, build_cheat_context
from .telemetry import TelemetryRecord, log_record


def _ensure_dirs(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _validate_context(conversation: str, caption: Optional[str]) -> None:
    settings = get_settings()
    guard = run_guardrails(conversation, caption or "", max_chars=settings.max_input_chars)
    if not guard.allowed:
        raise ValueError(guard.reason or "Guardrails rejected the input.")


def create_app() -> Flask:
    settings = get_settings()
    template_dir = Path(__file__).resolve().parent.parent / "templates"
    app = Flask(__name__, template_folder=str(template_dir))
    app.config["SECRET_KEY"] = settings.flask_secret_key
    app.config["UPLOAD_FOLDER"] = str(settings.uploads_path)
    _ensure_dirs(settings.uploads_path)

    def _render_chat(
        chat_id: int,
        interpretation: Optional[str] = None,
        cheat_matches: Optional[list[CheatMatch]] = None,
    ):
        store = ChatStore()
        thread = store.get_thread(chat_id)
        return render_template(
            "chat.html",
            thread=thread,
            interpretation=interpretation,
            cheat_matches=cheat_matches or [],
        )

    @app.route("/")
    def index():
        store = ChatStore()
        threads = store.list_threads()
        return render_template("index.html", threads=threads)

    @app.post("/chat")
    def create_chat():
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        if not title:
            flash("Chat title is required.", "error")
            return redirect(url_for("index"))
        store = ChatStore()
        thread = store.create_thread(title=title, description=description)
        flash(f"Created chat #{thread.chat_id}", "success")
        return redirect(url_for("view_chat", chat_id=thread.chat_id))

    @app.get("/chat/<int:chat_id>")
    def view_chat(chat_id: int):
        return _render_chat(chat_id)

    @app.post("/chat/<int:chat_id>/message")
    def post_message(chat_id: int):
        author = request.form.get("author", "anon").strip() or "anon"
        text = request.form.get("text", "").strip()
        if not text:
            flash("Message text is required.", "error")
            return redirect(url_for("view_chat", chat_id=chat_id))
        store = ChatStore()
        try:
            store.add_message(chat_id, author, text)
        except ValueError as exc:
            flash(str(exc), "error")
            return redirect(url_for("index"))
        return redirect(url_for("view_chat", chat_id=chat_id))

    @app.post("/chat/<int:chat_id>/interpret")
    def interpret_chat(chat_id: int):
        store = ChatStore()
        try:
            thread = store.get_thread(chat_id)
        except ValueError as exc:
            flash(str(exc), "error")
            return redirect(url_for("index"))

        caption = request.form.get("caption", "").strip()
        conversation = thread.as_prompt_context()
        try:
            _validate_context(conversation, caption)
        except ValueError as exc:
            flash(str(exc), "error")
            return redirect(url_for("view_chat", chat_id=chat_id))

        cheat_context, matches = build_cheat_context(conversation, caption or None)

        image_path: Optional[Path] = None
        file = request.files.get("meme_image")
        if file and file.filename:
            filename = secure_filename(file.filename)
            unique_name = f"{uuid4().hex}_{filename}"
            dest = Path(app.config["UPLOAD_FOLDER"]) / unique_name
            file.save(dest)
            image_path = dest

        try:
            response = interpret_meme(conversation, cheat_context, caption or None, image_path)
        except Exception as exc:  # noqa: BLE001
            flash(f"LLM error: {exc}", "error")
            if image_path and image_path.exists():
                image_path.unlink(missing_ok=True)
            return redirect(url_for("view_chat", chat_id=chat_id))

        log_record(
            TelemetryRecord(
                pathway="rag" if cheat_context else "none",
                latency_ms=response.latency_ms,
                prompt_tokens=response.prompt_tokens,
                response_tokens=response.response_tokens,
                cost_usd=None,
            )
        )

        if image_path and image_path.exists():
            image_path.unlink(missing_ok=True)

        return _render_chat(chat_id, interpretation=response.text, cheat_matches=matches)

    return app


def main() -> None:
    app = create_app()
    settings = get_settings()
    app.run(debug=True, port=5000)


if __name__ == "__main__":
    main()
