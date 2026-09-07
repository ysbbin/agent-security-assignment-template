from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SENSITIVE_KEYS = {"api_key", "apikey", "gemini_api_key", "authorization", "token", "secret"}


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "[REDACTED]" if key.casefold() in SENSITIVE_KEYS else _redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


class TraceLogger:
    def __init__(self, trace_dir: Path, run_id: str, enabled: bool = True):
        self.enabled = enabled
        self.path = trace_dir / f"{run_id}.jsonl"
        if enabled:
            trace_dir.mkdir(parents=True, exist_ok=True)

    def log(self, event_type: str, **fields: Any) -> None:
        if not self.enabled:
            return
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            **fields,
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(_redact(record), ensure_ascii=False) + "\n")
