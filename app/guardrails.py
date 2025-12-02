from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

SUSPECT_PATTERNS: tuple[str, ...] = (
    "ignore previous instructions",
    "disregard all rules",
    "override the system",
    "forget the guardrails",
    "you are no longer",
)


@dataclass
class GuardrailResult:
    allowed: bool
    reason: str | None = None


def _contains_pattern(text: str, patterns: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(pattern in lowered for pattern in patterns)


def check_prompt_injection(*chunks: str) -> GuardrailResult:
    blob = "\n".join(chunks)
    if _contains_pattern(blob, SUSPECT_PATTERNS):
        return GuardrailResult(
            allowed=False,
            reason=(
                "Prompt rejected because it attempted to override safety instructions. "
                "Please rephrase without injection tactics."
            ),
        )
    return GuardrailResult(allowed=True)


def check_length(*chunks: str, max_chars: int) -> GuardrailResult:
    total = sum(len(chunk) for chunk in chunks)
    if total > max_chars:
        return GuardrailResult(
            allowed=False,
            reason=(
                f"Input too long ({total} chars). Please shorten to under {max_chars} characters."
            ),
        )
    return GuardrailResult(allowed=True)


def run_guardrails(*chunks: str, max_chars: int) -> GuardrailResult:
    length_result = check_length(*chunks, max_chars=max_chars)
    if not length_result.allowed:
        return length_result
    return check_prompt_injection(*chunks)
