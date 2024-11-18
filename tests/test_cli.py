"""Test the command line interface."""

from __future__ import annotations

import runpy
from pathlib import Path

import pytest

from create_ssh_config import CHECK_SUBNET_FILE, TEMPLATE_FILE
from create_ssh_config.cli import Namespace, cli, parse_args, validate_check_subnet


def test_validate_check_subnet(tmp_path: Path) -> None:
    with pytest.raises(
        FileNotFoundError, match="^check-subnet script NOT_FOUND not found$"
    ):
        validate_check_subnet(Path("NOT_FOUND"))
    assert validate_check_subnet(Path("/bin/sh")) == Path("sh")

    special_sh = tmp_path / "special_sh"
    special_sh.symlink_to("/bin/sh")
    assert validate_check_subnet(special_sh) == special_sh


def test_parse_args() -> None:
    namespace = parse_args(["hostsfile", "localhost"])
    expected = Namespace(
        check_subnet=CHECK_SUBNET_FILE,
        forward_x11=False,
        hostsfile=Path("hostsfile"),
        localhost="localhost",
        no_store=False,
        overwrite=False,
        template=TEMPLATE_FILE,
        ignore_missing=False,
    )
    assert namespace == expected


@pytest.fixture
def expected_content() -> str:
    expected = "cli.config"
    return (Path(__file__).parent / expected).read_text("utf-8")


def run_cli(
    args: list[str], capsys: pytest.CaptureFixture
) -> tuple[str, str, str | None]:
    """Run the CLI."""
    hostsfile = Path(__file__).parent / "cli.json"
    args = [str(hostsfile), "localhost", *args]
    cli(args)

    ssh_file = Path.home().joinpath(".ssh/config")
    try:
        ssh_content = ssh_file.read_text("utf-8")
    except FileNotFoundError:
        ssh_content = None

    out, err = capsys.readouterr()
    return out, err, ssh_content


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


@pytest.mark.parametrize("ignore_missing", [True, False])
def test_ignore_missing(
    ignore_missing: bool, expected_content: str, capsys: pytest.CaptureFixture
) -> None:
    args = ["--check-subnet", "NOT_FOUND"]

    if not ignore_missing:
        with pytest.raises(
            FileNotFoundError, match="^check-subnet script NOT_FOUND not found$"
        ):
            run_cli(args, capsys)

        out, err = capsys.readouterr()
        assert not out
        assert not err
    else:
        out, err, ssh_content = run_cli([*args, "--ignore-missing"], capsys)
        assert not err
        assert not out
        assert ssh_content == expected_content.replace("check-subnet", "NOT_FOUND")


def test_main(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that __main__ calls the cli."""
    monkeypatch.setattr("create_ssh_config.cli.cli", lambda: 0)
    runpy.run_module("create_ssh_config")
