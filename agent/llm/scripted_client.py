from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from .base import ModelReply, ToolCall


class ScriptedLLM:
    """Deterministic LLM replacement used by tests and offline exercises."""

    def __init__(self, replies: Iterable[ModelReply | dict[str, Any]]):
        self._replies = [self._coerce(item) for item in replies]
        self._index = 0

    @classmethod
    def from_file(cls, path: str | Path) -> "ScriptedLLM":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    @staticmethod
    def _coerce(item: ModelReply | dict[str, Any]) -> ModelReply:
        if isinstance(item, ModelReply):
            return item
        calls = [
            ToolCall(
                name=call["name"],
                arguments=call.get("arguments", {}),
                call_id=call.get("call_id"),
            )
            for call in item.get("tool_calls", [])
        ]
        return ModelReply(
            text=item.get("text", ""),
            tool_calls=calls,
            usage=item.get("usage", {}),
        )

    def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        system_prompt: str,
    ) -> ModelReply:
        del messages, tools, system_prompt
        if self._index >= len(self._replies):
            return ModelReply(text="Script completed.")
        reply = self._replies[self._index]
        self._index += 1
        return reply
