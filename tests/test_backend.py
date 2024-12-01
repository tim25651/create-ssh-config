# %%
"""just a raw draft of the tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from jsonschema.exceptions import ValidationError as SchemaValidationError

from create_ssh_config import (
    Assets,
    Host,
    create_body,
    create_config,
    get_hosts,
    save_config,
    validate_check_subnet,
    validate_check_subnet_script,
)

TESTS_DIR = Path(__file__).parent
DATA_DIR = TESTS_DIR / "data"
INVALID_AT_RUNTIME = DATA_DIR / "invalid_at_runtime"
INVALID_AT_VALIDATION = DATA_DIR / "invalid_at_validation"
VALID = DATA_DIR / "valid"


@pytest.mark.parametrize("overwrite", [True, False])
@pytest.mark.parametrize("exists", [True, False])
def test_save_config(exists: bool, overwrite: bool) -> None:
    ssh_dir = Path.home() / ".ssh"
    config_file = ssh_dir / "config"

    if exists:
        ssh_dir.mkdir(0o700)
        config_file.touch()

    if exists and not overwrite:
        with pytest.raises(FileExistsError, match="ssh config already exists"):
            save_config("config", overwrite)
    else:
        save_config("config", overwrite)
        assert config_file.read_text() == "config"
        assert ssh_dir.stat().st_mode == 0o40700
        assert config_file.stat().st_mode == 0o100644


invalid_paths = list(INVALID_AT_VALIDATION.glob("*.yaml"))
invalid_contents = [hosts.read_text("utf-8") for hosts in invalid_paths]
invalid_all: list[Path | str] = invalid_paths + invalid_contents


@pytest.mark.parametrize("hostsfile", invalid_all)
def test_get_hosts_invalid(hostsfile: Path | str) -> None:
    with pytest.raises((SchemaValidationError,)):
        get_hosts(hostsfile)


valid_paths = list(VALID.glob("*.yaml"))
valid_contents = [hosts.read_text("utf-8") for hosts in valid_paths]
valid_all: list[Path | str] = valid_paths + valid_contents


@pytest.mark.parametrize("hostsfile", valid_all)
def test_get_hosts_valid(hostsfile: Path | str) -> None:
    hosts = get_hosts(hostsfile)
    assert isinstance(hosts, list)
    assert all(isinstance(host, Host) for host in hosts)


@pytest.mark.parametrize("hostsfile", VALID.glob("*.yaml"))
def test_create_body(hostsfile: Path, template: str) -> None:
    hosts = get_hosts(hostsfile)
    body = create_body(template, hosts, None, Path("CHECK_SUBNET"))
    expected = Path(hostsfile.with_suffix(".config")).read_text("utf-8")
    assert body == expected


@pytest.mark.parametrize(
    ("hostsfile", "error"),
    [
        ("check_subnet_in_last.yaml", "Last hostname must not have check-subnet other"),
        ("duplicate_hosts.yaml", "Duplicate host testhost"),
        ("missing_hostname.yaml", "Missing hostname for testhost"),
    ],
)
def test_check_subnet_in_last(hostsfile: str, error: str, template: str) -> None:
    hosts = get_hosts(INVALID_AT_RUNTIME / hostsfile)

    with pytest.raises(ValueError, match=f"^{error}$"):
        create_body(template, hosts, None, Path("CHECK_SUBNET"))


def test_localhost(template: str) -> None:
    hosts = get_hosts(DATA_DIR / "localhost.yaml")
    body = create_body(template, hosts, "testhost", Path("CHECK_SUBNET"))
    expected = DATA_DIR / "localhost.config"
    expected_content = expected.read_text("utf-8")
    assert body == expected_content


def test_validate_check_subnet_script_not_found() -> None:
    with pytest.raises(
        FileNotFoundError, match="^check-subnet script NOT_FOUND not found$"
    ):
        validate_check_subnet_script(Path("NOT_FOUND"))


def test_validate_check_subnet_script_success() -> None:
    assert validate_check_subnet_script(Path("/bin/sh")) == Path("sh")


def test_validate_check_subnet_script_not_in_path(tmp_path: Path) -> None:
    special_sh = tmp_path / "special_sh"
    special_sh.symlink_to("/bin/sh")
    assert validate_check_subnet_script(special_sh) == special_sh


def test_validate_check_subnet_str_no_ignore_missing() -> None:
    with pytest.raises(
        ValueError,
        match="^check_subnet must be Path to be validated or add --ignore-missing$",
    ):
        validate_check_subnet("NOT_FOUND", ignore_missing=False)


@pytest.mark.parametrize("check_subnet", [Path("NOT_FOUND"), "NOT_FOUND"])
def test_validate_check_subnet_ignore_missing(check_subnet: Path | str) -> None:
    assert validate_check_subnet(check_subnet, ignore_missing=True) == Path("NOT_FOUND")


def test_validate_check_subnet_success() -> None:
    assert validate_check_subnet(Path("/bin/sh"), ignore_missing=False) == Path("sh")


@pytest.mark.parametrize(
    "template", [Assets.TEMPLATE.read_text("utf-8"), Assets.TEMPLATE]
)
def test_create_config(template: Path | str) -> None:
    cli_json = DATA_DIR / "cli.yaml"
    config = create_config(cli_json, "localhost", False, template=template)
    expected = DATA_DIR / "cli.config"
    expected_content = expected.read_text("utf-8")
    assert config == expected_content
