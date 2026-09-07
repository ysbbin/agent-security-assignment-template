from agent.core import OfficeAgent
from agent.llm.base import ModelReply, ToolCall
from agent.llm.scripted_client import ScriptedLLM
from evaluation.utility import load_trace, tool_calls


def test_agent_executes_tool_and_writes_trace(config):
    llm = ScriptedLLM([
        ModelReply(tool_calls=[ToolCall("search_email", {"query": "weekly update"})]),
        ModelReply(text="Done"),
    ])
    result = OfficeAgent(config, llm).run("Find the update", "alice", "test")
    events = load_trace(result.trace_path)
    assert result.final_text == "Done"
    assert tool_calls(events) == ["search_email"]
    assert {event["event_type"] for event in events} >= {
        "user_input", "context", "llm", "tool_call", "tool_result", "final"
    }


def test_agent_stops_at_max_steps(config):
    llm = ScriptedLLM([
        ModelReply(tool_calls=[ToolCall("search_email", {"query": "x"})])
        for _ in range(config.max_steps)
    ])
    result = OfficeAgent(config, llm).run("Loop", "alice")
    assert result.steps == config.max_steps
    assert result.final_text.startswith("Stopped")
