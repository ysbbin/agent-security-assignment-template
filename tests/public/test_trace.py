import json

from tracing.logger import TraceLogger


def test_trace_redacts_secret_fields(lab_root):
    logger = TraceLogger(lab_root / "traces", "redaction-test")
    logger.log(
        "tool_call",
        run_id="redaction-test",
        step=1,
        arguments={"api_key": "do-not-store", "query": "safe"},
        nested={"Authorization": "Bearer secret"},
    )
    record = json.loads(logger.path.read_text(encoding="utf-8"))
    assert record["arguments"]["api_key"] == "[REDACTED]"
    assert record["nested"]["Authorization"] == "[REDACTED]"
    assert "do-not-store" not in logger.path.read_text(encoding="utf-8")
