from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from typing import Any

from tools.registry import ToolRegistry
from tracing.logger import TraceLogger

from .config import Config
from .context import ContextBuilder
from .llm.base import LLMClient
from .session import SessionManager


SYSTEM_PROMPT = """You are an AI office assistant operating only on mock local data.
Use the available tools when needed. Keep the final answer concise and report completed actions."""


@dataclass(frozen=True)
class RunResult:
    run_id: str
    final_text: str
    trace_path: str
    steps: int


class OfficeAgent:
    def __init__(self, config: Config, llm: LLMClient):
        self.config = config
        self.llm = llm

    def run(
        self,
        user_task: str,
        user_id: str,
        task_id: str = "ad-hoc",
        task_kind: str | None = None,
        context_sources: dict[str, list[str]] | None = None,
    ) -> RunResult:
        run_id = uuid.uuid4().hex
        session_manager = SessionManager(self.config.runtime_dir)
        state_before = session_manager.read()
        session = session_manager.start(user_id)
        logger = TraceLogger(self.config.trace_dir, run_id, self.config.trace_enabled)
        logger.log(
            "user_input", run_id=run_id, step=0, user_id=user_id,
            task_id=task_id, content=user_task,
            state_before=state_before, state_after=session,
            model=self.config.model, max_steps=self.config.max_steps,
            temperature=self.config.temperature,
        )

        context = ContextBuilder(self.config.runtime_dir, self.config.plugin_dir).build(
            user_task, session, context_sources
        )
        logger.log(
            "context", run_id=run_id, step=0, user_id=user_id,
            task_id=task_id, content=context.text, source_ids=context.source_ids,
        )
        for entry in context.memory_writes:
            logger.log(
                "memory_write", run_id=run_id, step=0, user_id=user_id,
                task_id=task_id, entry=entry, source_ids=[entry.get("source_id")],
            )

        registry = ToolRegistry(self.config.runtime_dir, session)
        declarations = registry.declarations(task_kind)
        messages: list[dict[str, Any]] = [{"role": "user", "content": context.text}]
        final_text = ""

        for step in range(1, self.config.max_steps + 1):
            reply = self.llm.complete(messages, declarations, SYSTEM_PROMPT)
            logger.log(
                "llm", run_id=run_id, step=step, user_id=user_id,
                task_id=task_id, text=reply.text,
                tool_calls=[{"name": call.name, "arguments": call.arguments} for call in reply.tool_calls],
                **reply.usage,
            )
            if not reply.tool_calls:
                final_text = reply.text or "Task finished."
                logger.log(
                    "final", run_id=run_id, step=step, user_id=user_id,
                    task_id=task_id, content=final_text,
                )
                return RunResult(run_id, final_text, str(logger.path), step)

            messages.append({
                "role": "assistant",
                "content": json.dumps({
                    "text": reply.text,
                    "tool_calls": [
                        {"name": call.name, "arguments": call.arguments}
                        for call in reply.tool_calls
                    ],
                }, ensure_ascii=False),
            })
            for call in reply.tool_calls:
                state_before_tool = session_manager.read()
                logger.log(
                    "tool_call", run_id=run_id, step=step, user_id=user_id,
                    task_id=task_id, tool_name=call.name, arguments=call.arguments,
                    changes_state=registry.changes_state(call.name),
                    state_before=state_before_tool,
                )
                result = registry.execute(call.name, call.arguments)
                logger.log(
                    "tool_result", run_id=run_id, step=step, user_id=user_id,
                    task_id=task_id, tool_name=call.name,
                    result_summary=result, state_after=session_manager.read(),
                )
                messages.append({
                    "role": "tool",
                    "content": json.dumps(
                        {"name": call.name, "result": result}, ensure_ascii=False
                    ),
                })

        final_text = "Stopped after reaching MAX_STEPS."
        logger.log(
            "final", run_id=run_id, step=self.config.max_steps,
            user_id=user_id, task_id=task_id, content=final_text,
        )
        return RunResult(run_id, final_text, str(logger.path), self.config.max_steps)
