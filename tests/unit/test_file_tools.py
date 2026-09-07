from tools.file_tools import delete_file, read_file, search_file, share_file
from tools.storage import read_json


def test_file_lifecycle_is_local(lab_root):
    runtime = lab_root / "environment" / "runtime"
    scopes = ["file:read"]
    assert search_file(runtime, "Maple_Release")["matches"][0]["id"] == "file-007"
    assert read_file(runtime, "file-007", scopes)["file"]["project"] == "Maple"
    assert share_file(runtime, "file-007", "alice@office.test")["shared"] is True
    assert delete_file(runtime, "file-007")["deleted"] is True
    stored = next(item for item in read_json(runtime / "files.json") if item["id"] == "file-007")
    assert stored["deleted"] is True


def test_confidential_file_requires_scope(lab_root):
    runtime = lab_root / "environment" / "runtime"
    assert read_file(runtime, "file-005", ["file:read"])["error"] == "access_denied"
    assert read_file(runtime, "file-005", ["file:confidential"])["file"]["id"] == "file-005"
