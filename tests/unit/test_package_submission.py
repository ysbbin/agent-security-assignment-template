from __future__ import annotations

import json
import zipfile
from pathlib import Path

import package_submission


def test_should_include_excludes_secrets_and_runtime(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(package_submission, "ROOT", tmp_path)
    source = tmp_path / "agent" / "core.py"
    source.parent.mkdir()
    source.write_text("print('ok')", encoding="utf-8")
    env_file = tmp_path / ".env"
    env_file.write_text("GEMINI_API_KEY=secret", encoding="utf-8")
    runtime = tmp_path / "environment" / "runtime" / "memory.json"
    runtime.parent.mkdir(parents=True)
    runtime.write_text("{}", encoding="utf-8")
    evidence = tmp_path / "submission" / "red_team" / "traces" / "evidence.jsonl"
    evidence.parent.mkdir(parents=True)
    evidence.write_text("{}\n", encoding="utf-8")
    raw_trace = tmp_path / "traces" / "raw.jsonl"
    raw_trace.parent.mkdir()
    raw_trace.write_text("{}\n", encoding="utf-8")

    assert package_submission.should_include(source)
    assert package_submission.should_include(evidence)
    assert not package_submission.should_include(env_file)
    assert not package_submission.should_include(runtime)
    assert not package_submission.should_include(raw_trace)


def test_check_secrets_rejects_google_api_key(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(package_submission, "ROOT", tmp_path)
    source = tmp_path / "answer.txt"
    source.write_text("AIza" + "A" * 30, encoding="utf-8")

    try:
        package_submission.check_secrets([source])
    except ValueError as exc:
        assert "Google API Key" in str(exc)
    else:
        raise AssertionError("API Key pattern was not rejected")


def test_ensure_required_results_accepts_completed_submission(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(package_submission, "ROOT", tmp_path)
    monkeypatch.setattr(package_submission, "STUDENT_FILE", tmp_path / "STUDENT.md")
    for relative in package_submission.REQUIRED_FILES:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Heading\n작성 내용\n", encoding="utf-8")
    results = {
        "baseline": {"attack_success_rate": 1.0, "normal_task_success_rate": 0.9},
        "defended": {"attack_success_rate": 0.1, "normal_task_success_rate": 0.8},
        "runs_per_case": 3,
        "notes": "test",
    }
    (tmp_path / "submission/blue_team/results.json").write_text(
        json.dumps(results), encoding="utf-8"
    )
    trace = tmp_path / "submission/red_team/traces/evidence.jsonl"
    trace.parent.mkdir(parents=True)
    trace.write_text('{}\n', encoding="utf-8")

    package_submission.ensure_required_results()


def test_main_builds_sanitized_submission_archive(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(package_submission, "ROOT", tmp_path)
    monkeypatch.setattr(package_submission, "STUDENT_FILE", tmp_path / "STUDENT.md")
    monkeypatch.setattr(package_submission, "DIST_DIR", tmp_path / "dist")
    monkeypatch.setattr(package_submission, "run_public_tests", lambda: None)

    for relative in package_submission.REQUIRED_FILES:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Heading\n작성 내용\n", encoding="utf-8")
    (tmp_path / "STUDENT.md").write_text("# Student\n\n학번: 20260001\n\n이름: 홍길동\n", encoding="utf-8")
    results = {
        "baseline": {"attack_success_rate": 1.0, "normal_task_success_rate": 1.0},
        "defended": {"attack_success_rate": 0.0, "normal_task_success_rate": 0.9},
        "runs_per_case": 3,
        "notes": "completed",
    }
    (tmp_path / "submission/blue_team/results.json").write_text(
        json.dumps(results), encoding="utf-8"
    )
    evidence = tmp_path / "submission/red_team/traces/evidence.jsonl"
    evidence.parent.mkdir(parents=True)
    evidence.write_text("{}\n", encoding="utf-8")
    env_file = tmp_path / ".env"
    env_file.write_text("GEMINI_API_KEY=not-packaged", encoding="utf-8")
    raw_trace = tmp_path / "traces/raw.jsonl"
    raw_trace.parent.mkdir()
    raw_trace.write_text("{}\n", encoding="utf-8")

    assert package_submission.main() == 0
    archive_path = tmp_path / "dist/정보보호론_20260001_홍길동.zip"
    assert archive_path.is_file()
    with zipfile.ZipFile(archive_path) as archive:
        names = set(archive.namelist())
    prefix = "정보보호론_20260001_홍길동/"
    assert prefix + "STUDENT.md" in names
    assert prefix + "submission/red_team/traces/evidence.jsonl" in names
    assert prefix + ".env" not in names
    assert prefix + "traces/raw.jsonl" not in names
