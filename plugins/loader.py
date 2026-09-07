from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_enabled_manifests(plugin_dir: Path) -> list[dict[str, Any]]:
    manifests = []
    for path in sorted(plugin_dir.glob("*.json")):
        item = json.loads(path.read_text(encoding="utf-8"))
        if item.get("enabled", False):
            manifests.append(item)
    return manifests
