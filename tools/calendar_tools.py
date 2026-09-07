from __future__ import annotations

from pathlib import Path
from typing import Any

from .storage import read_json, write_json


def search_calendar(runtime_dir: Path, query: str) -> dict[str, Any]:
    events = read_json(runtime_dir / "calendar.json", [])
    needle = query.casefold()
    matches = [
        item
        for item in events
        if needle in " ".join([item.get("title", ""), item.get("description", "")]).casefold()
    ]
    return {"matches": matches}


def create_calendar_event(
    runtime_dir: Path,
    title: str,
    start_time: str,
    participants: list[str],
    description: str = "",
) -> dict[str, Any]:
    path = runtime_dir / "calendar.json"
    events = read_json(path, [])
    item = {
        "id": f"cal-{len(events) + 1:03d}",
        "title": title,
        "owner": "current_user",
        "participants": participants,
        "description": description,
        "start_time": start_time,
    }
    events.append(item)
    write_json(path, events)
    return {"created": True, "event_id": item["id"]}
