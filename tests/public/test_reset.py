from pathlib import Path

from reset import reset_state
from tools.memory_tools import read_memory, write_memory
from tools.storage import read_json, write_json


def test_memory_reset_restores_seed(lab_root: Path):
    runtime = lab_root / "environment" / "runtime"
    write_memory(runtime, "temporary", "value", "user")
    reset_state(lab_root, "memory")
    assert read_memory(runtime, "temporary")["entry"] is None
    assert read_memory(runtime, "office_timezone")["entry"]["value"] == "Asia/Seoul"


def test_session_reset_does_not_reset_files(lab_root: Path):
    runtime = lab_root / "environment" / "runtime"
    files = read_json(runtime / "files.json")
    files[0]["shared_with"].append("person@office.test")
    write_json(runtime / "files.json", files)
    reset_state(lab_root, "session")
    assert read_json(runtime / "session.json") == {}
    assert "person@office.test" in read_json(runtime / "files.json")[0]["shared_with"]


def test_all_reset_removes_trace_and_restores_files(lab_root: Path):
    trace = lab_root / "traces" / "temp.jsonl"
    trace.write_text("{}\n", encoding="utf-8")
    files = read_json(lab_root / "environment" / "runtime" / "files.json")
    files[0]["deleted"] = True
    write_json(lab_root / "environment" / "runtime" / "files.json", files)
    reset_state(lab_root, "all")
    assert not trace.exists()
    assert read_json(lab_root / "environment" / "runtime" / "files.json")[0]["deleted"] is False
