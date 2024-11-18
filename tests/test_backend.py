# %%
"""just a raw draft of the tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from jsonschema.exceptions import ValidationError as SchemaValidationError

from create_ssh_config import (
    POSTAMBLE,
    PREAMBLE,
    Host,
    create_body,
    finalize_config,
    get_hosts,
    save_config,
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


@pytest.mark.parametrize("forward_x11", [True, False])
def test_finalize_config(forward_x11: bool) -> None:
    config = finalize_config("body", forward_x11)
    no_x11 = "" if forward_x11 else "# "
    assert config == PREAMBLE + "body" + POSTAMBLE.format(no_x11=no_x11)


@pytest.mark.parametrize("hostsfile", INVALID_AT_VALIDATION.glob("*.json"))
def test_get_hosts(hostsfile: Path) -> None:
    valid = not hostsfile.stem.endswith("_invalid")
    if not valid:
        with pytest.raises((SchemaValidationError,)):
            get_hosts(hostsfile)

    else:
        hosts = get_hosts(hostsfile)
        assert isinstance(hosts, list)
        assert all(isinstance(host, Host) for host in hosts)


@pytest.mark.parametrize("hostsfile", VALID.glob("*.json"))
def test_create_body(hostsfile: Path, template: str) -> None:
    hosts = get_hosts(hostsfile)
    body = create_body(template, hosts, None, Path("CHECK_SUBNET"))
    expected = Path(hostsfile.with_suffix(".config")).read_text("utf-8")
    print(repr(body))
    print(repr(expected))
    assert body == expected


@pytest.mark.parametrize(
    ("hostsfile", "error"),
    [
        ("check_subnet_in_last.json", "Last hostname must not have check-subnet other"),
        ("duplicate_hosts.json", "Duplicate host testhost"),
        ("missing_hostname.json", "Missing hostname for testhost"),
    ],
)
def test_check_subnet_in_last(hostsfile: str, error: str, template: str) -> None:
    hosts = get_hosts(INVALID_AT_RUNTIME / hostsfile)

    with pytest.raises(ValueError, match=f"^{error}$"):
        create_body(template, hosts, None, Path("CHECK_SUBNET"))


def test_localhost(template: str) -> None:
    hosts = get_hosts(DATA_DIR / "localhost.json")
    body = create_body(template, hosts, "testhost", Path("CHECK_SUBNET"))
    expected = DATA_DIR / "localhost.config"
    expected_content = expected.read_text("utf-8")
    assert body == expected_content
