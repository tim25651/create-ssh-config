"""Create an SSH config file from a hosts file."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from create_ssh_config import (
    CHECK_SUBNET_FILE,
    TEMPLATE_FILE,
    create_body,
    finalize_config,
    get_hosts,
    save_config,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


class Namespace(argparse.Namespace):
    """Namespace for the command line arguments."""

    hostsfile: Path
    localhost: str
    overwrite: bool
    forward_x11: bool
    no_store: bool
    template: Path
    check_subnet: Path
    ignore_missing: bool


def parse_args(argv: Sequence[str] | None = None) -> Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("hostsfile", help="Path to the hosts file", type=Path)
    parser.add_argument("localhost", help="Which host is the local machine?", type=str)
    parser.add_argument(
        "--overwrite", help="Overwrite the existing config file", action="store_true"
    )
    parser.add_argument(
        "--forward-x11",
        help="Enable X11 forwarding",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--no-store",
        help="Print the config to the console instead of saving it",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--template",
        help="Path to a custom Jinja2 template file",
        type=Path,
        default=TEMPLATE_FILE,
    )
    parser.add_argument(
        "--check-subnet",
        help="Path to the check-subnet script",
        type=Path,
        default=CHECK_SUBNET_FILE,
    )
    parser.add_argument(
        "--ignore-missing",
        help="Ignore missing check-subnet script",
        action="store_true",
        default=False,
    )
    return parser.parse_args(argv)  # type: ignore[return-value]


def validate_check_subnet(check_subnet: Path) -> Path:
    """Validate the check-subnet script."""
    # try if just the basename is in PATH
    only_name = shutil.which(check_subnet.name)
    if only_name:
        return Path(check_subnet.name)
        # check if the full check-subnet script is in PATH

    full_path = shutil.which(check_subnet)
    if not full_path:
        raise FileNotFoundError(f"check-subnet script {check_subnet} not found")
    return check_subnet


def cli(argv: Sequence[str] | None = None) -> int:
    """Main entry point of the script."""
    args = parse_args(argv)

    if not args.ignore_missing:
        args.check_subnet = validate_check_subnet(args.check_subnet)

    template = args.template.read_text("utf-8")

    hosts = get_hosts(args.hostsfile)

    body = create_body(template, hosts, args.localhost, args.check_subnet)

    config = finalize_config(body, args.forward_x11)

    if args.no_store:
        print(config, end="")  # noqa: T201
    else:
        save_config(config, args.overwrite)

    return 0
