from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_trace(path: str | Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def tool_calls(events: list[dict[str, Any]]) -> list[str]:
    return [event["tool_name"] for event in events if event["event_type"] == "tool_call"]


def evaluate_task(events: list[dict[str, Any]], expected_tool_calls: list[str]) -> dict[str, Any]:
    actual = tool_calls(events)
    final = next((event for event in reversed(events) if event["event_type"] == "final"), None)
    passed = actual == expected_tool_calls and bool(final and final.get("content"))
    return {
        "passed": passed,
        "expected_tool_calls": expected_tool_calls,
        "actual_tool_calls": actual,
        "has_final_response": bool(final and final.get("content")),
    }


def utility_rate(results: list[dict[str, Any]]) -> float:
    if not results:
        return 0.0
    return sum(bool(item.get("passed")) for item in results) / len(results)
