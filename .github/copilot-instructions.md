# MemeSensei Agent Guide

- CLI entry point is `app/main.py` (Typer) and the web UI entry point is `app/web.py` (Flask). Flow: choose conversation source (chatroom or manual) ➜ guardrails ➜ cheat-sheet retrieval (`app/rag.py`) ➜ Gemini call ➜ telemetry append (`app/telemetry.py`).
- Configuration lives in `app/config.py`; it loads `.env` (needs `GEMINI_API_KEY`) and exposes limits plus `CHAT_STORE_PATH`, `CHEATSHEET_PATH`, upload path, and model names.
- Chatroom layer (`app/chatroom.py`) persists chats in `data/chats.json` and powers the Typer commands. Cheat-sheet layer (`app/rag.py`) embeds `data/cheatsheets.json` with `models/text-embedding-004` and returns the top matches.

## Expected patterns
- Always call `get_settings()` instead of re-reading env vars; it is memoized and keeps defaults aligned with README.
- Guardrails (`app/guardrails.py`) must run before LLM calls; reuse `run_guardrails(..., max_chars=settings.max_input_chars)` to enforce both length and injection checks.
- When forming prompts, follow `llm_client.interpret_meme`: conversation background, optional caption, retrieved cheat-sheet insights, then the short response rubric (single paragraph wording).
- Telemetry is append-only CSV; log via `telemetry.log_record` with the pathway string (now `"rag"` or `"none"`). If you add new metrics, extend `TelemetryRecord` rather than writing direct CSV rows.

## Workflows & commands
- Install dependencies: `pip install -r requirements.txt` (Python 3.11+ expected).
- Run the CLI: `python -m app.main chat new ...`, `chat post ...`, `chat show ...`, then `interpret --chat-id <local>` to explain a meme in that thread (use `--show-cheat-sheet` to print retrieved entries).
- Run the web UI: `flask --app app.web:create_app run` (requires `FLASK_SECRET_KEY` in `.env`).
- Offline evaluation (hits live Gemini): `python scripts/run_eval.py`; it loads `tests/tests.json` and reports pass rate + failing IDs.
- Cheat-sheet retrieval requires internet access for Gemini embeddings. Update `CHEATSHEET_PATH` if you maintain multiple corpora.

## Integration notes
- Gemini client (`google-generativeai`) is initialized once; reuse `_get_model()` to avoid re-auth overhead. Image support requires supplying a real file so `_read_image` can infer MIME.
- Flask server reuses chatroom + guardrail layers; upload handling relies on `settings.uploads_path`, so ensure the directory exists before saving files and clean up temp images after interpretation.
- `app/rag.py` currently embeds on startup and caches results. If you add dynamic editing endpoints, remember to bust `_load_index` cache by changing the JSON file's mtime or exposing an explicit invalidation hook.
- Tests and telemetry depend on the same settings file. If you need different limits for evaluation, inject overrides via env vars before importing modules.

## Gotchas
- Missing `GEMINI_API_KEY` raises immediately when calling `get_settings()`; ensure `.env` is in place before importing most modules.
- `scripts/run_eval.py` reuses guardrails; extremely long test inputs will fail fast rather than hitting the API.
- If cheat-sheet retrieval fails, fall back to an empty context but still log the error so telemetry stays accurate. Never drop chatroom messages silently—always persist through `ChatStore` helpers.
- The repo assumes ASCII filenames; keep new files UTF-8 but avoid exotic characters per project constraints.
