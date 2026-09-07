from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        if default is not None:
            return default
        raise FileNotFoundError(f"State file not found: {path}. Run reset.py --all first.")
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def find_by_id(records: list[dict[str, Any]], record_id: str) -> dict[str, Any] | None:
    return next((record for record in records if record.get("id") == record_id), None)
