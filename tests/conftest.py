"""Fixtures for tests."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

import create_ssh_config
from create_ssh_config import CHECK_SUBNET_FILE


@pytest.fixture(scope="session", autouse=True)
def add_to_path() -> None:
    os.environ["PATH"] += os.pathsep + str(CHECK_SUBNET_FILE.parent)


@pytest.fixture
def template() -> str:
    return (
        Path(create_ssh_config.__file__)
        .parent.joinpath("template.j2")
        .read_text("utf-8")
    )


@pytest.fixture(autouse=True)
def patch_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)


@pytest.fixture
def create_existing() -> None:
    ssh_dir = Path.home().joinpath(".ssh")
    config_file = Path.home().joinpath(".ssh/config")
    ssh_dir.mkdir(0o700)
    config_file.touch()
