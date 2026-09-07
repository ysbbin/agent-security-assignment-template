from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: dict[str, Any] = field(default_factory=dict)
    call_id: str | None = None


@dataclass(frozen=True)
class ModelReply:
    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    usage: dict[str, int] = field(default_factory=dict)


class LLMClient(Protocol):
    def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        system_prompt: str,
    ) -> ModelReply:
        """Return the next assistant message or requested tool calls."""
