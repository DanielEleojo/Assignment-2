# MemeSensei

MemeSensei is a helper app that explains memes. You can use it from the command line or through a simple web page.

## Detailed Setup

1. **Install Python 3.11+**
	- On Windows, download the official installer from python.org and enable "Add python.exe to PATH".
2. **Create and activate a virtual environment**
	- `python -m venv .venv`
	- PowerShell: `./.venv/Scripts/Activate.ps1`
3. **Install dependencies**
	- `pip install --upgrade pip`
	- `pip install -r requirements.txt`
4. **Prepare folders**
	- The repo's `.gitignore` leaves runtime artifacts (logs, chat history, uploads) untracked, so create the folders locally: `data/`, `logs/`, and `uploads/`.
	- If `data/chats.json` does not exist, create an empty file; the CLI will populate it on first use. Keep `data/cheatsheets.json` from the repo intact so retrieval works.
5. **Configure environment variables**
	- Copy `.env.example` to `.env` if provided, or create `.env` in the project root.
	- Set `GEMINI_API_KEY=<your-key>` and `FLASK_SECRET_KEY=<any-secret-value>`.
	- Optional overrides: `CHAT_STORE_PATH`, `CHEATSHEET_PATH`, and `UPLOADS_PATH` if you move data around.
6. **Verify the install**
	- Run `python -m app.main --help` to confirm the Typer CLI starts.
	- Run `flask --app app.web:create_app routes` to ensure Flask can import the app.
7. **Run the CLI workflow**
	- Create a chat: `python -m app.main chat new "Sprint Retro"`.
	- Add a meme description: `python -m app.main chat post --chat-id <id> --message "Describe meme here."`
	- Interpret the meme: `python -m app.main interpret --chat-id <id> --show-cheat-sheet`.
8. **Run the web UI**
	- `flask --app app.web:create_app run --debug`
	- Visit `http://127.0.0.1:5000` and upload a meme or type in a caption.
9. **Log telemetry (optional)**
	- Check `logs/telemetry.csv` after each run to confirm entries are appended.
10. **Run evaluations**
	 - `python scripts/run_eval.py` (hits the live Gemini API, so ensure your key has quota).

## Running the Project

| Mode | Command | Notes |
| --- | --- | --- |
| CLI chat flow | `python -m app.main chat new "My chat"` then `python -m app.main interpret --chat-id <id> --show-cheat-sheet` | Creates/reads `data/chats.json`; make sure the `.env` file is populated first. |
| CLI quick help | `python -m app.main --help` | Lists every available Typer command. |
| Web UI (dev) | `flask --app app.web:create_app run --debug` | Requires `FLASK_SECRET_KEY` in `.env`; uploads land in the ignored `uploads/` directory. |
| Evaluation suite | `python scripts/run_eval.py` | Exercises guardrails + Gemini for regression checks. |

If you clone the project fresh, the only required manual files are `.env` (for secrets) and an empty `data/chats.json`. Everything else is generated automatically at runtime and stays out of version control because of the `.gitignore` rules.

## What You Can Do

- Store meme discussions in simple chat threads.
- Pull helpful cheat-sheet hints before asking the AI.
- Ask Gemini to explain how a meme works.
- Keep a lightweight log of each interpretation.

## How It Works

1. You create or pick a chat.
2. The app checks the message to keep it clean and short.
3. It looks for related tips in the cheat-sheet file.
4. Those tips plus your message go to Gemini.
5. The answer and telemetry are saved for later.

## Common Commands

- `python -m app.main chat list` — show all chats.
- `python -m app.main interpret --chat-id <id>` — explain the latest meme in that thread.
- `flask --app app.web:create_app run` — launch the browser version.

