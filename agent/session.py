from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.storage import read_json, write_json


class SessionManager:
    def __init__(self, runtime_dir: Path):
        self.runtime_dir = runtime_dir
        self.path = runtime_dir / "session.json"

    def start(self, user_id: str) -> dict[str, Any]:
        users = read_json(self.runtime_dir / "users.json", [])
        user = next((item for item in users if item["user_id"] == user_id), None)
        if user is None:
            raise ValueError(f"Unknown user: {user_id}")

        current = read_json(self.path, {})
        if not current:
            current = {
                "active_user": user_id,
                "role": user["role"],
                "capability_scope": list(user["allowed_scopes"]),
            }
        else:
            current["active_user"] = user_id
            current["role"] = user["role"]
            current.setdefault("capability_scope", list(user["allowed_scopes"]))
        write_json(self.path, current)
        return current

    def read(self) -> dict[str, Any]:
        return read_json(self.path, {})
