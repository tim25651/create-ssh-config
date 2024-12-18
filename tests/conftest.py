"""Fixtures for tests."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

import create_ssh_config
from create_ssh_config import Assets

sys.path.append(str(Path(__file__).parent))

SRC_DIR = Path(create_ssh_config.__file__).parent
TESTS_DIR = Path(__file__).parent
DATA_DIR = TESTS_DIR / "data"
CLI_CONFIG = DATA_DIR / "cli.config"


@pytest.fixture(scope="session", autouse=True)
def add_to_path() -> None:
    os.environ["PATH"] += os.pathsep + str(Assets.SCRIPT.parent)


@pytest.fixture
def template() -> str:
    return Assets.TEMPLATE.read_text("utf-8")


@pytest.fixture(autouse=True)
def patch_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def get_tmp_path() -> Path:
        """Return the tmp_path."""
        return tmp_path

    monkeypatch.setattr(Path, "home", get_tmp_path)


@pytest.fixture
def create_existing() -> None:
    ssh_dir = Path.home() / ".ssh"
    config_file = ssh_dir / "config"
    ssh_dir.mkdir(0o700)
    config_file.touch()


@pytest.fixture
def expected_content() -> str:
    return CLI_CONFIG.read_text("utf-8")
