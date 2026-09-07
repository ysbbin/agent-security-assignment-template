from agent.session import SessionManager


def test_session_starts_with_user_profile(lab_root):
    session = SessionManager(lab_root / "environment" / "runtime").start("alice")
    assert session["active_user"] == "alice"
    assert session["role"] == "employee"
    assert "file:read" in session["capability_scope"]
