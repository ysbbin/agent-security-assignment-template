from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .storage import read_json, write_json


def read_memory(runtime_dir: Path, key: str) -> dict[str, Any]:
    entries = read_json(runtime_dir / "memory.json", {"entries": []})["entries"]
    found = next((item for item in reversed(entries) if item["key"] == key), None)
    return {"entry": found}


def write_memory(
    runtime_dir: Path,
    key: str,
    value: str,
    source: str,
    source_id: str | None = None,
    confidence: float = 1.0,
) -> dict[str, Any]:
    path = runtime_dir / "memory.json"
    data = read_json(path, {"entries": []})
    now = datetime.now(timezone.utc).isoformat()
    entry = {
        "key": key,
        "value": value,
        "source": source,
        "source_id": source_id,
        "confidence": confidence,
        "created_at": now,
        "updated_at": now,
    }
    data["entries"].append(entry)
    write_json(path, data)
    return {"written": True, "entry": entry}
