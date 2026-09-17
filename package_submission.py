from __future__ import annotations

import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
STUDENT_FILE = ROOT / "STUDENT.md"
DIST_DIR = ROOT / "dist"

EXCLUDED_DIRS = {
    ".git",
    ".venv",
    ".pytest_cache",
    "__pycache__",
    "dist",
}
EXCLUDED_FILES = {".env", ".coverage"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".zip"}
SECRET_PATTERNS = {
    "Google API Key": re.compile(rb"AIza[0-9A-Za-z_-]{20,}"),
}

REQUIRED_FILES = (
    Path("STUDENT.md"),
    Path(".assignment-version.json"),
    Path("submission/red_team/vulnerability_01.md"),
    Path("submission/red_team/vulnerability_02.md"),
    Path("submission/red_team/vulnerability_03.md"),
    Path("submission/blue_team/defense_report.md"),
    Path("submission/blue_team/results.json"),
)
REQUIRED_MARKDOWN_FILES = REQUIRED_FILES[2:6]


def read_student() -> tuple[str, str]:
    text = STUDENT_FILE.read_text(encoding="utf-8")
    student_id_match = re.search(r"^학번:\s*(.+?)\s*$", text, re.MULTILINE)
    name_match = re.search(r"^이름:\s*(.+?)\s*$", text, re.MULTILINE)
    if not student_id_match or not name_match:
        raise ValueError("STUDENT.md에 학번과 이름을 모두 작성하세요.")
    student_id = student_id_match.group(1).strip()
    name = name_match.group(1).strip()
    if not re.fullmatch(r"[0-9A-Za-z_-]+", student_id):
        raise ValueError("학번에는 숫자, 영문자, '-' 또는 '_'만 사용할 수 있습니다.")
    if not re.fullmatch(r"[0-9A-Za-z가-힣_-]+", name):
        raise ValueError("이름에는 한글, 영문자, 숫자, '-' 또는 '_'만 사용할 수 있습니다.")
    return student_id, name


def ensure_required_results() -> None:
    missing = [str(path) for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    if missing:
        raise ValueError("필수 파일이 없습니다: " + ", ".join(missing))

    for relative in REQUIRED_MARKDOWN_FILES:
        text = (ROOT / relative).read_text(encoding="utf-8")
        if "<!-- REQUIRED:" in text:
            raise ValueError(f"작성 완료 표식이 남아 있습니다: {relative}")
        body_lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        if not body_lines:
            raise ValueError(f"작성되지 않은 제출 문서입니다: {relative}")

    results_path = ROOT / "submission/blue_team/results.json"
    try:
        results = json.loads(results_path.read_text(encoding="utf-8"))
        validate_results(results)
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"submission/blue_team/results.json 형식 또는 계산값이 올바르지 않습니다: {exc}"
        ) from exc

    trace_files = list((ROOT / "submission/red_team/traces").glob("*.jsonl"))
    if not trace_files:
        raise ValueError("submission/red_team/traces/에 증거 JSONL Trace를 하나 이상 넣으세요.")


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


def validate_results(results: dict) -> None:
    protocol = results["evaluation_protocol"]
    if protocol["model"] != "gemini-3.8-flash":
        raise ValueError("지정 모델을 사용해야 합니다.")
    if protocol["temperature"] != 0 or protocol["max_steps"] != 6:
        raise ValueError("temperature와 max_steps를 지정값으로 유지해야 합니다.")
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
    if not {"F01", "F02", "F03"}.issubset(finding_ids) or len(finding_ids) != len(findings):
        raise ValueError("Finding ID가 없거나 중복되었습니다.")

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


def build_archive(files: list[Path], student_id: str, name: str) -> Path:
    DIST_DIR.mkdir(exist_ok=True)
    archive_path = DIST_DIR / f"정보보호론_{student_id}_{name}.zip"
    root_name = f"정보보호론_{student_id}_{name}"
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            relative = path.relative_to(ROOT)
            archive.write(path, Path(root_name) / relative)
    return archive_path


def main() -> int:
    try:
        run_public_tests()
        print("[2/4] 학생 정보와 필수 제출물 검사")
        student_id, name = read_student()
        ensure_required_results()
        print("[3/4] 제외 대상과 API Key 검사")
        files = collect_files()
        check_secrets(files)
        print("[4/4] 제출 ZIP 생성")
        archive_path = build_archive(files, student_id, name)
    except (OSError, ValueError) as exc:
        print(f"제출 ZIP 생성 실패: {exc}", file=sys.stderr)
        return 1
    print(f"완료: {archive_path.relative_to(ROOT)}")
    print("이 ZIP과 최종 PDF를 LMS/eCampus에 제출하세요.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
