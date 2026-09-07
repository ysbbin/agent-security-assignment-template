from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from agent.config import Config
from reset import reset_state


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def lab_root(tmp_path: Path) -> Path:
    shutil.copytree(PROJECT_ROOT / "environment" / "seed", tmp_path / "environment" / "seed")
    shutil.copytree(PROJECT_ROOT / "plugins", tmp_path / "plugins")
    (tmp_path / "environment" / "runtime").mkdir(parents=True)
    (tmp_path / "traces").mkdir()
    reset_state(tmp_path, "all")
    return tmp_path


@pytest.fixture
def config(lab_root: Path) -> Config:
    return Config(base_dir=lab_root, provider="scripted", trace_enabled=True)
