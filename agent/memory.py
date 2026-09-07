from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.memory_tools import write_memory
from tools.storage import read_json


class MemoryStore:
    def __init__(self, runtime_dir: Path):
        self.runtime_dir = runtime_dir

    def entries(self) -> list[dict[str, Any]]:
        return read_json(self.runtime_dir / "memory.json", {"entries": []})["entries"]

    def update_from_records(
        self,
        entities: list[dict[str, Any]],
        source: str,
        source_id: str,
    ) -> list[dict[str, Any]]:
        writes = []
        for entity in entities:
            result = write_memory(
                self.runtime_dir,
                key=entity["key"],
                value=entity["value"],
                source=source,
                source_id=source_id,
                confidence=float(entity.get("confidence", 0.5)),
            )
            writes.append(result["entry"])
        return writes
