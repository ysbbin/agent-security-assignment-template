from tools.calendar_tools import create_calendar_event, search_calendar


def test_search_and_create_calendar_event(lab_root):
    runtime = lab_root / "environment" / "runtime"
    assert search_calendar(runtime, "Python workshop")["matches"][0]["id"] == "cal-004"
    result = create_calendar_event(
        runtime, "Review", "2026-09-20T10:00:00+09:00", ["alice@office.test"]
    )
    assert result["created"] is True
