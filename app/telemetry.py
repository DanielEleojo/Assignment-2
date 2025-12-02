from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .config import get_settings


@dataclass
class TelemetryRecord:
    pathway: str
    latency_ms: float
    prompt_tokens: int | None = None
    response_tokens: int | None = None
    cost_usd: float | None = None


def log_record(record: TelemetryRecord) -> None:
    settings = get_settings()
    log_path = settings.telemetry_path
    log_path.parent.mkdir(parents=True, exist_ok=True)
    is_new_file = not log_path.exists()

    with log_path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        if is_new_file:
            writer.writerow(
                [
                    "timestamp",
                    "pathway",
                    "latency_ms",
                    "prompt_tokens",
                    "response_tokens",
                    "cost_usd",
                ]
            )
        writer.writerow(
            [
                datetime.now(timezone.utc).isoformat(),
                record.pathway,
                f"{record.latency_ms:.2f}",
                record.prompt_tokens or "",
                record.response_tokens or "",
                record.cost_usd or "",
            ]
        )
