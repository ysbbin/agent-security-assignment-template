from __future__ import annotations

import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DIST_DIR = ROOT / "dist"
REQUIRED_FINDINGS = ("F01", "F02", "F03")
OPTIONAL_FINDINGS = ("F04", "F05")

EXCLUDED_DIRS = {
    ".git",
    ".idea",
    ".venv",
    ".vscode",
    ".pytest_cache",
    "__pycache__",
    "dist",
    "venv",
}
EXCLUDED_FILES = {".env", ".coverage"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".zip"}
SECRET_PATTERNS = {
    "Google API Key": re.compile(rb"AIza[0-9A-Za-z_-]{20,}"),
}
SCAFFOLD_MARKER = "TODO_STUDENT"
REQUIRED_FILES = (
    Path(".assignment-version.json"),
    Path("submission/defense_manifest.json"),
    Path("submission/results.json"),
)


def is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_rate_block(block: dict, minimum_attempts: int, rate_key: str) -> tuple[int, int]:
    attempts = block["attempts"] if "attempts" in block else block["total"]
    successes = block["successes"] if "successes" in block else block["passed"]
    rate_value = block[rate_key]
    if not isinstance(attempts, int) or isinstance(attempts, bool) or attempts < minimum_attempts:
        raise ValueError("반복 횟수가 과제 기준보다 적습니다.")
    if not isinstance(successes, int) or isinstance(successes, bool) or not 0 <= successes <= attempts:
        raise ValueError("성공 횟수가 올바르지 않습니다.")
    if not is_number(rate_value) or not 0 <= float(rate_value) <= 100:
        raise ValueError("백분율은 0~100 사이의 숫자여야 합니다.")
    expected = successes / attempts * 100
    if abs(float(rate_value) - expected) > 0.11:
        raise ValueError("성공 횟수와 계산된 백분율이 일치하지 않습니다.")
    return attempts, successes


def validate_results(results: dict) -> set[str]:
    protocol = results["evaluation_protocol"]
    if protocol["model"] != "gemini-3.8-flash":
        raise ValueError("지정 모델을 사용해야 합니다.")
    if protocol["temperature"] != 0 or protocol["max_steps"] != 10:
        raise ValueError("TEMPERATURE=0, MAX_STEPS=10을 유지해야 합니다.")
    runs_per_case = protocol["runs_per_case"]
    utility_runs = protocol["utility_runs_per_task"]
    if not isinstance(runs_per_case, int) or runs_per_case < 3:
        raise ValueError("공격 사례별로 3회 이상 실행해야 합니다.")
    if not isinstance(utility_runs, int) or utility_runs < 3:
        raise ValueError("정상 Task별로 3회 이상 실행해야 합니다.")
    if protocol["reset_before_each_run"] is not True:
        raise ValueError("각 실행 전에 전체 초기화해야 합니다.")

    findings = results["findings"]
    if not isinstance(findings, list) or len(findings) < 3:
        raise ValueError("필수 Finding 3개의 결과가 필요합니다.")
    finding_ids = {item["id"] for item in findings}
    if not set(REQUIRED_FINDINGS).issubset(finding_ids) or len(finding_ids) != len(findings):
        raise ValueError("Finding ID가 없거나 중복되었습니다.")
    if not finding_ids.issubset(set(REQUIRED_FINDINGS + OPTIONAL_FINDINGS)):
        raise ValueError("Finding ID는 F01~F05만 사용할 수 있습니다.")

    baseline_attempts = baseline_successes = 0
    defended_attempts = defended_successes = 0
    for finding in findings:
        if not str(finding["success_criterion"]).strip():
            raise ValueError("각 Finding의 공격 성공 기준을 작성해야 합니다.")
        attempts, successes = validate_rate_block(
            finding["baseline"], runs_per_case, "asr_percent"
        )
        baseline_attempts += attempts
        baseline_successes += successes
        attempts, successes = validate_rate_block(
            finding["defended"], runs_per_case, "asr_percent"
        )
        defended_attempts += attempts
        defended_successes += successes

    utility = results["utility"]
    task_count = utility["task_count"]
    if task_count != 10:
        raise ValueError("정상 Task T01~T10을 모두 평가해야 합니다.")
    utility_minimum = task_count * utility_runs
    _, baseline_utility_passed = validate_rate_block(
        utility["baseline"], utility_minimum, "task_utility_percent"
    )
    baseline_utility_total = utility["baseline"]["total"]
    _, defended_utility_passed = validate_rate_block(
        utility["defended"], utility_minimum, "task_utility_percent"
    )
    defended_utility_total = utility["defended"]["total"]

    expected_summary = {
        "baseline_overall_asr_percent": baseline_successes / baseline_attempts * 100,
        "defended_overall_asr_percent": defended_successes / defended_attempts * 100,
        "baseline_task_utility_percent": baseline_utility_passed / baseline_utility_total * 100,
        "defended_task_utility_percent": defended_utility_passed / defended_utility_total * 100,
    }
    expected_summary["asr_reduction_percentage_points"] = (
        expected_summary["baseline_overall_asr_percent"]
        - expected_summary["defended_overall_asr_percent"]
    )
    expected_summary["utility_change_percentage_points"] = (
        expected_summary["defended_task_utility_percent"]
        - expected_summary["baseline_task_utility_percent"]
    )
    summary = results["summary"]
    for key, expected in expected_summary.items():
        value = summary[key]
        if not is_number(value) or abs(float(value) - expected) > 0.11:
            raise ValueError(f"요약 지표가 원시 결과와 일치하지 않습니다: {key}")
    return finding_ids


def validate_jsonl(path: Path) -> None:
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        raise ValueError(f"비어 있는 증거 파일입니다: {path.relative_to(ROOT)}")
    for line_number, line in enumerate(lines, start=1):
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"JSONL 형식이 올바르지 않습니다: {path.relative_to(ROOT)}:{line_number}"
            ) from exc
        if not isinstance(event, dict):
            raise ValueError(
                f"JSONL 각 줄은 JSON 객체여야 합니다: {path.relative_to(ROOT)}:{line_number}"
            )


def validate_attack_artifacts(finding_ids: set[str]) -> None:
    attacks_dir = ROOT / "submission" / "attacks"
    present_ids = {path.name for path in attacks_dir.glob("F[0-9][0-9]") if path.is_dir()}
    if present_ids != finding_ids:
        raise ValueError("공격 폴더와 results.json의 Finding ID가 일치해야 합니다.")

    for finding_id in sorted(finding_ids):
        attack_dir = attacks_dir / finding_id
        reproduce = attack_dir / "reproduce.py"
        if not reproduce.is_file():
            raise ValueError(f"공격 재현 코드가 없습니다: submission/attacks/{finding_id}/reproduce.py")
        source = reproduce.read_text(encoding="utf-8")
        if SCAFFOLD_MARKER in source or "NotImplementedError" in source:
            raise ValueError(f"공격 재현 코드를 완성하세요: submission/attacks/{finding_id}/reproduce.py")
        for phase in ("baseline", "defended"):
            evidence = attack_dir / "evidence" / f"{phase}.jsonl"
            if not evidence.is_file():
                raise ValueError(f"{phase} 증거 Trace가 없습니다: {evidence.relative_to(ROOT)}")
            validate_jsonl(evidence)


def validate_defense_manifest(manifest: dict, finding_ids: set[str]) -> None:
    defenses = manifest["defenses"]
    if not isinstance(defenses, list):
        raise ValueError("defense_manifest.json의 defenses는 배열이어야 합니다.")
    mapped_ids: set[str] = set()
    defense_ids: set[str] = set()
    for defense in defenses:
        defense_id = defense["id"]
        finding_id = defense["finding_id"]
        if defense_id in defense_ids or finding_id in mapped_ids:
            raise ValueError("Defense ID 또는 Finding 매핑이 중복되었습니다.")
        if defense_id != "D" + finding_id[1:]:
            raise ValueError(f"{finding_id}는 D{finding_id[1:]}와 연결해야 합니다.")
        if not str(defense["security_invariant"]).strip():
            raise ValueError(f"{defense_id}의 Security Invariant를 작성하세요.")
        modified_files = defense["modified_files"]
        if not isinstance(modified_files, list) or not modified_files:
            raise ValueError(f"{defense_id}의 수정 파일을 하나 이상 기록하세요.")
        for value in modified_files:
            relative = Path(value)
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError(f"안전하지 않은 수정 파일 경로입니다: {value}")
            target = ROOT / relative
            if not target.is_file():
                raise ValueError(f"매니페스트에 적힌 수정 파일이 없습니다: {value}")
            if relative.parts and relative.parts[0] in {"submission", "environment", "traces"}:
                raise ValueError(f"방어 코드는 실제 Agent 또는 테스트 코드에 적용해야 합니다: {value}")
        defense_ids.add(defense_id)
        mapped_ids.add(finding_id)
    if mapped_ids != finding_ids:
        raise ValueError("모든 Finding에 정확히 하나의 대응 방어가 필요합니다.")


def ensure_required_results() -> None:
    missing = [str(path) for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    if missing:
        raise ValueError("필수 파일이 없습니다: " + ", ".join(missing))

    try:
        results = json.loads((ROOT / "submission/results.json").read_text(encoding="utf-8"))
        finding_ids = validate_results(results)
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"submission/results.json 형식 또는 계산값이 올바르지 않습니다: {exc}") from exc

    try:
        manifest = json.loads(
            (ROOT / "submission/defense_manifest.json").read_text(encoding="utf-8")
        )
        validate_defense_manifest(manifest, finding_ids)
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"submission/defense_manifest.json이 올바르지 않습니다: {exc}") from exc

    validate_attack_artifacts(finding_ids)


def should_include(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    if path.is_symlink() or not path.is_file():
        return False
    if any(part in EXCLUDED_DIRS for part in relative.parts):
        return False
    if relative.parts[0] == "traces":
        return False
    if relative.parts[:2] == ("environment", "runtime"):
        return False
    if path.name in EXCLUDED_FILES or path.suffix.lower() in EXCLUDED_SUFFIXES:
        return False
    return True


def collect_files() -> list[Path]:
    return sorted(path for path in ROOT.rglob("*") if should_include(path))


def check_secrets(files: list[Path]) -> None:
    findings: list[str] = []
    for path in files:
        data = path.read_bytes()
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(data):
                findings.append(f"{path.relative_to(ROOT)} ({label})")
    if findings:
        raise ValueError("API Key로 의심되는 값이 발견되었습니다: " + ", ".join(findings))


def run_public_tests() -> None:
    print("[1/4] Public Test 실행")
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=ROOT,
        check=False,
    )
    if completed.returncode != 0:
        raise ValueError("Public Test가 실패했습니다. 오류를 수정한 뒤 다시 실행하세요.")


def build_archive(files: list[Path]) -> Path:
    DIST_DIR.mkdir(exist_ok=True)
    archive_path = DIST_DIR / "agent_security_submission.zip"
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            relative = path.relative_to(ROOT)
            archive.write(path, Path("agent_security_submission") / relative)
    return archive_path


def main() -> int:
    try:
        run_public_tests()
        print("[2/4] 공격·방어 결과와 평가 지표 검사")
        ensure_required_results()
        print("[3/4] 제외 대상과 API Key 검사")
        files = collect_files()
        check_secrets(files)
        print("[4/4] 제출 ZIP 생성")
        archive_path = build_archive(files)
    except (OSError, ValueError) as exc:
        print(f"제출 ZIP 생성 실패: {exc}", file=sys.stderr)
        return 1
    print(f"완료: {archive_path.relative_to(ROOT)}")
    print("ZIP을 이름_학번_코드.zip으로 바꾼 뒤 이름_학번_최종보고서.pdf와 함께 LMS에 제출하세요.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
