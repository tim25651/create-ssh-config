"""Fixtures for tests."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

import create_ssh_config
from create_ssh_config import CHECK_SUBNET_FILE, TEMPLATE_FILE

SRC_DIR = Path(create_ssh_config.__file__).parent
TESTS_DIR = Path(__file__).parent
DATA_DIR = TESTS_DIR / "data"


@pytest.fixture(scope="session", autouse=True)
def add_to_path() -> None:
    os.environ["PATH"] += os.pathsep + str(CHECK_SUBNET_FILE.parent)


@pytest.fixture
def template() -> str:
    return TEMPLATE_FILE.read_text("utf-8")


@pytest.fixture(autouse=True)
def patch_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)


@pytest.fixture
def create_existing() -> None:
    ssh_dir = Path.home() / ".ssh"
    config_file = ssh_dir / "config"
    ssh_dir.mkdir(0o700)
    config_file.touch()
