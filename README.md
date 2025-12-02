# MemeSensei

MemeSensei is a helper app that explains memes through a simple Flask-powered web interface.

## Web Setup & Run

1. **Install Python 3.11+**
	- On Windows, download the official installer from python.org and enable "Add python.exe to PATH".
2. **Create and activate a virtual environment**
	- `python -m venv .venv`
	- PowerShell: `./.venv/Scripts/Activate.ps1`
3. **Install dependencies**
	- `pip install --upgrade pip`
	- `pip install -r requirements.txt`
4. **Prepare folders**
	- The repo's `.gitignore` leaves runtime artifacts (logs, chat history, uploads) untracked, so create `data/`, `logs/`, and `uploads/` locally.
	- If `data/chats.json` is missing, create an empty file; the web app will append to it on first use. Leave `data/cheatsheets.json` untouched so retrieval works.
5. **Configure environment variables**
	- Create `.env` in the project root if it does not already exist.
	- Set at least `GEMINI_API_KEY=<your-key>` and `FLASK_SECRET_KEY=<any-secret-value>`.
	- Optional overrides: `CHAT_STORE_PATH`, `CHEATSHEET_PATH`, and `UPLOADS_PATH` when relocating assets.
6. **Start the Flask server**
	- Run `flask --app app.web:create_app run --debug` (omit `--debug` for production-like runs).
	- Flask will serve at `http://127.0.0.1:5000/` by default.

## Using the Web UI

1. Open `http://127.0.0.1:5000/` in your browser once the server is running.
2. Choose how to provide meme context:
	- **Chatroom**: pick an existing chat thread or create a new one to reuse previous conversation history.
	- **Manual**: type in a caption or upload an image without tying it to a chat.
3. Add optional notes or captions, then (if desired) upload an image file.
4. Submit the form. Guardrails check your input, the cheat-sheet retriever finds relevant hints, and Gemini generates a concise explanation.
5. Review the interpretation result plus any cheat-sheet snippets shown on the page.
6. Repeat the process for more memes; telemetry entries accumulate in `logs/telemetry.csv` for later analysis.

## What You Can Do

- Explain memes through a browser-friendly flow backed by Gemini.
- Pull helpful cheat-sheet hints before asking the AI.
- Keep a lightweight log of each interpretation.

## How It Works

1. You submit a meme or caption via the form.
2. The app checks the message to keep it clean and short.
3. It looks for related tips in the cheat-sheet file.
4. Those tips plus your message go to Gemini.
5. The answer and telemetry are saved for later.

