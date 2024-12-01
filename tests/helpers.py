"""Helper functions for tests."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from create_ssh_config.cli import cli

if TYPE_CHECKING:
    import pytest
TESTS_DIR = Path(__file__).parent
DATA_DIR = TESTS_DIR / "data"
CLI_HOSTSFILE = DATA_DIR / "cli.yaml"


def run_cli(
    args: list[str], capsys: pytest.CaptureFixture
) -> tuple[str, str, str | None]:
    """Run the CLI."""
    args = [str(CLI_HOSTSFILE), *args]
    cli(args)

    ssh_file = Path.home() / ".ssh" / "config"
    try:
        ssh_content = ssh_file.read_text("utf-8")
    except FileNotFoundError:
        ssh_content = None

    out, err = capsys.readouterr()
    return out, err, ssh_content
