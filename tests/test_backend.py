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


@pytest.mark.parametrize("overwrite", [True, False])
@pytest.mark.parametrize("exists", [True, False])
def test_save_config(exists: bool, overwrite: bool) -> None:
    ssh_dir = Path.home().joinpath(".ssh")
    config_file = Path.home().joinpath(".ssh/config")

    if exists:
        ssh_dir.mkdir(0o700)
        config_file.touch()

    if exists and not overwrite:
        with pytest.raises(FileExistsError, match="ssh config already exists"):
            save_config("config", overwrite)
    else:
        save_config("config", overwrite)
        assert config_file.read_text() == "config"
        # assert mode is 0o644
        # assert .ssh mode is 0o700
        assert ssh_dir.stat().st_mode == 0o40700
        assert config_file.stat().st_mode == 0o100644


@pytest.mark.parametrize("forward_x11", [True, False])
def test_finalize_config(forward_x11: bool) -> None:
    config = finalize_config("body", forward_x11)
    no_x11 = "" if forward_x11 else "# "
    assert config == PREAMBLE + "body" + POSTAMBLE.format(no_x11=no_x11)


@pytest.mark.parametrize("hostsfile", Path(__file__).parent.glob("data/*.json"))
def test_get_hosts(hostsfile: Path) -> None:
    valid = not hostsfile.stem.endswith("_invalid")
    if not valid:
        with pytest.raises((SchemaValidationError,)):
            get_hosts(hostsfile)

    else:
        hosts = get_hosts(hostsfile)
        assert isinstance(hosts, list)
        assert all(isinstance(host, Host) for host in hosts)


@pytest.mark.parametrize("hostsfile", Path(__file__).parent.glob("data/test*.json"))
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
    hosts = get_hosts(Path(__file__).parent.joinpath("invalid").joinpath(hostsfile))

    with pytest.raises(ValueError, match=f"^{error}$"):
        create_body(template, hosts, None, Path("CHECK_SUBNET"))


def test_localhost(template: str) -> None:
    hosts = get_hosts(Path(__file__).parent.joinpath("data/test1.json"))
    body = create_body(template, hosts, "testhost", Path("CHECK_SUBNET"))
    expected = (
        Path(__file__).parent.joinpath("data/localhost.config").read_text("utf-8")
    )
    assert body == expected
