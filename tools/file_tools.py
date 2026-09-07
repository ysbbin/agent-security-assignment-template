from __future__ import annotations

from pathlib import Path
from typing import Any

from .storage import find_by_id, read_json, write_json


def search_file(runtime_dir: Path, query: str) -> dict[str, Any]:
    files = read_json(runtime_dir / "files.json", [])
    needle = query.casefold()
    matches = [
        {"id": item["id"], "name": item["name"], "project": item["project"]}
        for item in files
        if not item.get("deleted")
        and needle in " ".join([item.get("name", ""), item.get("project", ""), item.get("content", "")]).casefold()
    ]
    return {"matches": matches}


def _can_read(file: dict[str, Any], scopes: list[str]) -> bool:
    classification = file.get("classification", "internal")
    if classification == "public":
        return True
    if classification == "confidential":
        return "file:confidential" in scopes
    return "file:read" in scopes


def read_file(runtime_dir: Path, file_id: str, scopes: list[str]) -> dict[str, Any]:
    file = find_by_id(read_json(runtime_dir / "files.json", []), file_id)
    if not file or file.get("deleted"):
        return {"error": "file_not_found"}
    if not _can_read(file, scopes):
        return {"error": "access_denied"}
    return {"file": file}


def share_file(runtime_dir: Path, file_id: str, recipient: str) -> dict[str, Any]:
    path = runtime_dir / "files.json"
    files = read_json(path, [])
    file = find_by_id(files, file_id)
    if not file or file.get("deleted"):
        return {"error": "file_not_found"}
    file.setdefault("shared_with", [])
    if recipient not in file["shared_with"]:
        file["shared_with"].append(recipient)
    write_json(path, files)
    return {"shared": True, "file_id": file_id, "recipient": recipient}


def delete_file(runtime_dir: Path, file_id: str) -> dict[str, Any]:
    path = runtime_dir / "files.json"
    files = read_json(path, [])
    file = find_by_id(files, file_id)
    if not file:
        return {"error": "file_not_found"}
    file["deleted"] = True
    write_json(path, files)
    return {"deleted": True, "file_id": file_id}
