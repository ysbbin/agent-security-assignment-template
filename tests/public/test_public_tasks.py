import json
from pathlib import Path

import pytest

from agent.core import OfficeAgent
from agent.llm.scripted_client import ScriptedLLM
from evaluation.public_security import unexpected_changes
from evaluation.utility import evaluate_task, load_trace
from reset import reset_state


TASKS = json.loads(
    (Path(__file__).resolve().parents[2] / "tasks" / "public_tasks.json").read_text(encoding="utf-8")
)


@pytest.mark.parametrize("task", TASKS, ids=lambda task: task["task_id"])
def test_public_task(config, task):
    reset_state(config.base_dir, "all")
    result = OfficeAgent(config, ScriptedLLM(task["script"])).run(
        task["prompt"], task["user_id"], task["task_id"], task["kind"]
    )
    events = load_trace(result.trace_path)
    evaluation = evaluate_task(events, task["expected_tool_calls"])
    assert evaluation["passed"], evaluation
    assert unexpected_changes(events, task["expected_tool_calls"]) == []
