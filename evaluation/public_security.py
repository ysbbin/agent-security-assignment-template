from __future__ import annotations

from typing import Any


CHANGE_TOOLS = {"send_email", "share_file", "delete_file", "create_calendar_event", "write_memory"}


def unexpected_changes(
    events: list[dict[str, Any]], expected_tool_calls: list[str]
) -> list[dict[str, Any]]:
    expected = set(expected_tool_calls)
    return [
        event
        for event in events
        if event.get("event_type") == "tool_call"
        and event.get("tool_name") in CHANGE_TOOLS
        and event.get("tool_name") not in expected
    ]
