from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from plugins.loader import load_enabled_manifests
from tools.storage import find_by_id, read_json

from .memory import MemoryStore


@dataclass
class ContextResult:
    text: str
    source_ids: list[str] = field(default_factory=list)
    memory_writes: list[dict[str, Any]] = field(default_factory=list)


class ContextBuilder:
    def __init__(self, runtime_dir: Path, plugin_dir: Path):
        self.runtime_dir = runtime_dir
        self.plugin_dir = plugin_dir
        self.memory = MemoryStore(runtime_dir)

    def build(
        self,
        user_task: str,
        session: dict[str, Any],
        context_sources: dict[str, list[str]] | None = None,
    ) -> ContextResult:
        sources = context_sources or {}
        blocks = [
            f"Active user: {session.get('active_user')}",
            f"Role: {session.get('role')}",
            f"User request: {user_task}",
        ]
        source_ids: list[str] = []
        memory_writes: list[dict[str, Any]] = []

        emails = read_json(self.runtime_dir / "emails.json", [])
        for email_id in sources.get("emails", []):
            item = find_by_id(emails, email_id)
            if item:
                source_ids.append(email_id)
                blocks.append(
                    "Email record\n"
                    f"From: {item['sender']}\nSubject: {item['subject']}\n{item['body']}"
                )
                memory_writes.extend(
                    self.memory.update_from_records(
                        item.get("entities", []), "email", item["id"]
                    )
                )

        files = read_json(self.runtime_dir / "files.json", [])
        for file_id in sources.get("files", []):
            item = find_by_id(files, file_id)
            if item and not item.get("deleted"):
                source_ids.append(file_id)
                blocks.append(f"Document record\nName: {item['name']}\n{item['content']}")
                memory_writes.extend(
                    self.memory.update_from_records(
                        item.get("entities", []), "file", item["id"]
                    )
                )

        memory_entries = self.memory.entries()
        if memory_entries:
            blocks.append(
                "Saved workspace facts\n"
                + "\n".join(f"{entry['key']}: {entry['value']}" for entry in memory_entries)
            )

        manifests = load_enabled_manifests(self.plugin_dir)
        if manifests:
            blocks.append(
                "Available connectors\n"
                + "\n".join(
                    f"{item['name']} {item['version']}: {item['description']}"
                    for item in manifests
                )
            )

        return ContextResult(
            text="\n\n".join(blocks),
            source_ids=source_ids,
            memory_writes=memory_writes,
        )
