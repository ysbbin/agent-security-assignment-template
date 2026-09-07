from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .calendar_tools import create_calendar_event, search_calendar
from .email_tools import read_email, search_email, send_email
from .file_tools import delete_file, read_file, search_file, share_file
from .memory_tools import read_memory, write_memory


Handler = Callable[..., dict[str, Any]]


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: Handler
    changes_state: bool = False

    def declaration(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


class ToolRegistry:
    def __init__(self, runtime_dir: Path, session: dict[str, Any]):
        scopes = list(session.get("capability_scope", []))
        obj = lambda properties, required=None: {
            "type": "object",
            "properties": properties,
            "required": required or [],
        }
        string = lambda description: {"type": "string", "description": description}

        self._tools = {
            "search_email": ToolSpec(
                "search_email", "Search mock email messages.",
                obj({"query": string("Search phrase")}, ["query"]),
                lambda **args: search_email(runtime_dir, **args),
            ),
            "read_email": ToolSpec(
                "read_email", "Read one mock email by id.",
                obj({"email_id": string("Email id")}, ["email_id"]),
                lambda **args: read_email(runtime_dir, **args),
            ),
            "send_email": ToolSpec(
                "send_email", "Send a message to the mock outbox.",
                obj({
                    "to": string("Recipient address"),
                    "subject": string("Message subject"),
                    "body": string("Message body"),
                }, ["to", "subject", "body"]),
                lambda **args: send_email(runtime_dir, **args), True,
            ),
            "search_file": ToolSpec(
                "search_file", "Search mock drive files.",
                obj({"query": string("Search phrase")}, ["query"]),
                lambda **args: search_file(runtime_dir, **args),
            ),
            "read_file": ToolSpec(
                "read_file", "Read a mock drive file by id.",
                obj({"file_id": string("File id")}, ["file_id"]),
                lambda **args: read_file(runtime_dir, scopes=scopes, **args),
            ),
            "share_file": ToolSpec(
                "share_file", "Share a mock drive file with a recipient.",
                obj({
                    "file_id": string("File id"),
                    "recipient": string("Recipient address"),
                }, ["file_id", "recipient"]),
                lambda **args: share_file(runtime_dir, **args), True,
            ),
            "delete_file": ToolSpec(
                "delete_file", "Mark a mock drive file as deleted.",
                obj({"file_id": string("File id")}, ["file_id"]),
                lambda **args: delete_file(runtime_dir, **args), True,
            ),
            "search_calendar": ToolSpec(
                "search_calendar", "Search mock calendar events.",
                obj({"query": string("Search phrase")}, ["query"]),
                lambda **args: search_calendar(runtime_dir, **args),
            ),
            "create_calendar_event": ToolSpec(
                "create_calendar_event", "Create an event in the mock calendar.",
                obj({
                    "title": string("Event title"),
                    "start_time": string("ISO date and time"),
                    "participants": {"type": "array", "items": {"type": "string"}},
                    "description": string("Event description"),
                }, ["title", "start_time", "participants"]),
                lambda **args: create_calendar_event(runtime_dir, **args), True,
            ),
            "read_memory": ToolSpec(
                "read_memory", "Read one saved workspace fact.",
                obj({"key": string("Fact key")}, ["key"]),
                lambda **args: read_memory(runtime_dir, **args),
            ),
            "write_memory": ToolSpec(
                "write_memory", "Save a workspace fact for later tasks.",
                obj({
                    "key": string("Fact key"),
                    "value": string("Fact value"),
                    "source": string("Where the value came from"),
                }, ["key", "value", "source"]),
                lambda **args: write_memory(runtime_dir, **args), True,
            ),
        }

    def declarations(self, task_kind: str | None = None) -> list[dict[str, Any]]:
        del task_kind
        return [tool.declaration() for tool in self._tools.values()]

    def execute(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        tool = self._tools.get(name)
        if tool is None:
            return {"error": "unknown_tool", "tool": name}
        try:
            return tool.handler(**arguments)
        except TypeError as exc:
            return {"error": "invalid_arguments", "detail": str(exc)}

    def changes_state(self, name: str) -> bool:
        tool = self._tools.get(name)
        return bool(tool and tool.changes_state)
