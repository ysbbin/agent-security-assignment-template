from __future__ import annotations

import pytest

from agent.config import Config


def test_default_model_is_course_model(lab_root, monkeypatch) -> None:
    monkeypatch.delenv("LLM_MODEL", raising=False)

    config = Config.from_env(lab_root)

    assert config.model == "gemini-3.8-flash"


def test_non_course_model_is_rejected(lab_root, monkeypatch) -> None:
    monkeypatch.setenv("LLM_MODEL", "gemini-2.5-flash-lite")

    with pytest.raises(ValueError, match="gemini-3.8-flash"):
        Config.from_env(lab_root)
