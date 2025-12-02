from __future__ import annotations

import json
from pathlib import Path
import time

from app.config import get_settings
from app.guardrails import run_guardrails
from app.llm_client import interpret_meme
from app.rag import build_cheat_context

TEST_PATH = Path("tests/tests.json")


def _load_tests() -> list[dict]:
    with TEST_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _evaluate_case(case: dict, max_chars: int) -> tuple[bool, str]:
    conversation = case["conversation"]
    caption = case.get("caption", "")
    expectations = [token.lower() for token in case.get("expectations", [])]

    guard = run_guardrails(conversation, caption, max_chars=max_chars)
    if not guard.allowed:
        return False, f"Guardrail rejection: {guard.reason}"

    cheat_context, _matches = build_cheat_context(conversation, caption)
    response = interpret_meme(conversation, cheat_context, caption, image_path=None)

    text = response.text.lower()
    success = all(keyword in text for keyword in expectations)
    if success:
        return True, "ok"
    missing = [kw for kw in expectations if kw not in text]
    return False, f"Missing keywords: {', '.join(missing)}"


def main() -> None:
    cases = _load_tests()
    settings = get_settings()
    passed = 0
    failures: list[tuple[str, str]] = []

    for case in cases:
        success, detail = _evaluate_case(case, settings.max_input_chars)
        if success:
            passed += 1
        else:
            failures.append((case["id"], detail))
        time.sleep(2)

    total = len(cases)
    rate = (passed / total) * 100 if total else 0
    print(f"Pass rate: {passed}/{total} ({rate:.1f}%)")
    if failures:
        print("\nFailed cases:")
        for case_id, detail in failures:
            print(f" - {case_id}: {detail}")


if __name__ == "__main__":
    main()
