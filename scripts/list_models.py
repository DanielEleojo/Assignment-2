"""Utility script to list Gemini models accessible to the configured API key."""
from __future__ import annotations

from dotenv import load_dotenv
import google.generativeai as genai
import os


def main() -> None:
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise SystemExit("GEMINI_API_KEY missing; populate .env first")
    genai.configure(api_key=api_key)
    models = [
        model
        for model in genai.list_models()
        if "generateContent" in getattr(model, "supported_generation_methods", [])
    ]
    print(f"Found {len(models)} models supporting generateContent:\n")
    for model in models:
        display = getattr(model, "display_name", "")
        dims = getattr(model, "input_token_limit", None)
        print(f"- {model.name} (display='{display}', tokens={dims})")


if __name__ == "__main__":
    main()
