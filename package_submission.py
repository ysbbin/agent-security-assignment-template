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
    Path("submission/blue_team/defense_report.md"),
    Path("submission/blue_team/results.json"),
)


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

    for relative in REQUIRED_FILES[2:5]:
        text = (ROOT / relative).read_text(encoding="utf-8")
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
        required_numbers = (
            results["baseline"]["attack_success_rate"],
            results["baseline"]["normal_task_success_rate"],
            results["defended"]["attack_success_rate"],
            results["defended"]["normal_task_success_rate"],
        )
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise ValueError("submission/blue_team/results.json 형식이 올바르지 않습니다.") from exc
    if not all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in required_numbers):
        raise ValueError("results.json의 방어 전후 Security/Utility 수치를 모두 입력하세요.")

    trace_files = list((ROOT / "submission/red_team/traces").glob("*.jsonl"))
    if not trace_files:
        raise ValueError("submission/red_team/traces/에 증거 JSONL Trace를 하나 이상 넣으세요.")


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
