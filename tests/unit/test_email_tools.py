from tools.email_tools import read_email, search_email, send_email
from tools.storage import read_json


def test_search_and_read_email(lab_root):
    runtime = lab_root / "environment" / "runtime"
    result = search_email(runtime, "weekly update")
    assert result["matches"][0]["id"] == "mail-001"
    assert read_email(runtime, "mail-001")["email"]["subject"] == "Orion weekly update"


def test_send_email_only_changes_mock_outbox(lab_root):
    runtime = lab_root / "environment" / "runtime"
    result = send_email(runtime, "person@office.test", "Hello", "Body")
    assert result["sent"] is True
    assert read_json(runtime / "outbox.json")[0]["to"] == "person@office.test"
