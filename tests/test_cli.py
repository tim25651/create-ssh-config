"""Test the command line interface."""

from __future__ import annotations

import runpy
from pathlib import Path

import pytest
from helpers import run_cli

from create_ssh_config import Assets
from create_ssh_config.cli import Namespace, parse_args


def test_parse_args() -> None:
    namespace = parse_args(["hostsfile"])
    expected = Namespace(
        check_subnet=Assets.SCRIPT,
        forward_x11=False,
        hostsfile=Path("hostsfile"),
        localhost=None,
        no_store=False,
        overwrite=False,
        template=Assets.TEMPLATE,
        ignore_missing=False,
    )
    assert namespace == expected


def test_cli_no_store(expected_content: str, capsys: pytest.CaptureFixture) -> None:
    out, err, _ = run_cli(["--no-store"], capsys)
    assert not err
    assert out == expected_content


def test_cli(expected_content: str, capsys: pytest.CaptureFixture) -> None:
    out, err, ssh_content = run_cli([], capsys)
    assert not err
    assert not out
    assert ssh_content == expected_content


@pytest.mark.parametrize("overwrite", [True, False])
def test_cli_overwrite(
    overwrite: bool,
    expected_content: str,
    create_existing: None,
    capsys: pytest.CaptureFixture,
) -> None:
    del create_existing

    if not overwrite:
        with pytest.raises(FileExistsError, match="^ssh config already exists$"):
            run_cli([], capsys)
        out, err = capsys.readouterr()
        assert out == expected_content + "\n" + "=" * 40 + "\n"

    else:
        out, err, ssh_content = run_cli(["--overwrite"], capsys)
        assert not err
        assert not out
        assert ssh_content == expected_content


def test_main(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that __main__ calls the cli."""
    monkeypatch.setattr("create_ssh_config.cli.cli", lambda: 0)
    runpy.run_module("create_ssh_config")
