from __future__ import annotations

import json
import zipfile
from pathlib import Path

import package_submission


def completed_results(finding_ids: tuple[str, ...] = ("F01", "F02", "F03")) -> dict:
    return {
        "evaluation_protocol": {
            "provider": "gemini",
            "model": "gemini-3.8-flash",
            "temperature": 0,
            "max_steps": 10,
            "runs_per_case": 3,
            "utility_runs_per_task": 3,
            "reset_before_each_run": True,
        },
        "findings": [
            {
                "id": finding_id,
                "success_criterion": "Unauthorized state change",
                "baseline": {"attempts": 3, "successes": 3, "asr_percent": 100.0},
                "defended": {"attempts": 3, "successes": 0, "asr_percent": 0.0},
            }
            for finding_id in finding_ids
        ],
        "utility": {
            "task_count": 10,
            "baseline": {"passed": 30, "total": 30, "task_utility_percent": 100.0},
            "defended": {"passed": 27, "total": 30, "task_utility_percent": 90.0},
        },
        "summary": {
            "baseline_overall_asr_percent": 100.0,
            "defended_overall_asr_percent": 0.0,
            "asr_reduction_percentage_points": 100.0,
            "baseline_task_utility_percent": 100.0,
            "defended_task_utility_percent": 90.0,
            "utility_change_percentage_points": -10.0,
        },
        "notes": "test",
    }


def create_completed_submission(
    root: Path, finding_ids: tuple[str, ...] = ("F01", "F02", "F03")
) -> None:
    (root / ".assignment-version.json").write_text("{}", encoding="utf-8")
    (root / "agent").mkdir()
    (root / "agent/core.py").write_text("print('defended')\n", encoding="utf-8")
    submission = root / "submission"
    submission.mkdir()
    (submission / "results.json").write_text(
        json.dumps(completed_results(finding_ids)), encoding="utf-8"
    )
    for finding_id in finding_ids:
        defense_id = "D" + finding_id[1:]
        attack_dir = submission / "attacks" / finding_id
        defense_dir = submission / "defenses" / defense_id
        attack_dir.mkdir(parents=True)
        defense_dir.mkdir(parents=True)
        (attack_dir / f"student_attack_{finding_id}.py").write_text(
            "print('attack')\n", encoding="utf-8"
        )
        evidence_dir = attack_dir / "my_evidence"
        evidence_dir.mkdir()
        (evidence_dir / "runs.any-name").write_text("baseline and defended runs\n", encoding="utf-8")
        (defense_dir / f"student_defense_{defense_id}.py").write_text(
            "print('defense')\n", encoding="utf-8"
        )


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
    arbitrary = tmp_path / "submission" / "attacks" / "F01" / "any-name.bin"
    arbitrary.parent.mkdir(parents=True)
    arbitrary.write_text("artifact", encoding="utf-8")
    raw_trace = tmp_path / "traces" / "raw.jsonl"
    raw_trace.parent.mkdir()
    raw_trace.write_text("{}\n", encoding="utf-8")

    assert package_submission.should_include(source)
    assert package_submission.should_include(arbitrary)
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


def test_accepts_arbitrary_names_and_nested_files(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(package_submission, "ROOT", tmp_path)
    create_completed_submission(tmp_path)

    package_submission.ensure_required_results()


def test_rejects_empty_template_directory(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(package_submission, "ROOT", tmp_path)
    create_completed_submission(tmp_path)
    attack_dir = tmp_path / "submission/attacks/F01"
    for path in sorted(attack_dir.rglob("*"), reverse=True):
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            path.rmdir()
    (attack_dir / ".gitkeep").write_text("", encoding="utf-8")

    try:
        package_submission.ensure_required_results()
    except ValueError as exc:
        assert "공격 결과 파일" in str(exc)
    else:
        raise AssertionError("Empty attack directory was not rejected")


def test_accepts_complete_bonus_pair(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(package_submission, "ROOT", tmp_path)
    create_completed_submission(tmp_path, ("F01", "F02", "F03", "F04"))

    package_submission.ensure_required_results()


def test_rejects_unpaired_defense_directory(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(package_submission, "ROOT", tmp_path)
    create_completed_submission(tmp_path)
    defense = tmp_path / "submission/defenses/D03"
    for path in defense.iterdir():
        path.unlink()
    defense.rmdir()

    try:
        package_submission.ensure_required_results()
    except ValueError as exc:
        assert "같은 번호의 방어 폴더" in str(exc)
    else:
        raise AssertionError("Missing defense directory was not rejected")


def test_main_packages_every_file_under_attack_and_defense(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(package_submission, "ROOT", tmp_path)
    monkeypatch.setattr(package_submission, "DIST_DIR", tmp_path / "dist")
    monkeypatch.setattr(package_submission, "run_public_tests", lambda: None)
    create_completed_submission(tmp_path)
    env_file = tmp_path / ".env"
    env_file.write_text("GEMINI_API_KEY=not-packaged", encoding="utf-8")

    assert package_submission.main() == 0
    archive_path = tmp_path / "dist/agent_security_submission.zip"
    with zipfile.ZipFile(archive_path) as archive:
        names = set(archive.namelist())
    prefix = "agent_security_submission/"
    assert prefix + "submission/attacks/F03/student_attack_F03.py" in names
    assert prefix + "submission/attacks/F03/my_evidence/runs.any-name" in names
    assert prefix + "submission/defenses/D03/student_defense_D03.py" in names
    assert prefix + "agent/core.py" in names
    assert prefix + ".env" not in names


def test_validate_results_rejects_incorrect_summary() -> None:
    results = completed_results()
    results["summary"]["defended_overall_asr_percent"] = 50.0

    try:
        package_submission.validate_results(results)
    except ValueError as exc:
        assert "defended_overall_asr_percent" in str(exc)
    else:
        raise AssertionError("Incorrect summary was not rejected")


def test_validate_results_requires_three_findings() -> None:
    results = completed_results(("F01", "F02"))

    try:
        package_submission.validate_results(results)
    except ValueError as exc:
        assert "3개" in str(exc)
    else:
        raise AssertionError("Missing required finding was not rejected")


def test_validate_results_requires_max_steps_ten() -> None:
    results = completed_results()
    results["evaluation_protocol"]["max_steps"] = 6

    try:
        package_submission.validate_results(results)
    except ValueError as exc:
        assert "MAX_STEPS=10" in str(exc)
    else:
        raise AssertionError("Incorrect max steps was not rejected")
