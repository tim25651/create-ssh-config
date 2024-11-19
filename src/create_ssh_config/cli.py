"""Create an SSH config file from a hosts file."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import TYPE_CHECKING

from create_ssh_config import (
    CHECK_SUBNET_FILE,
    TEMPLATE_FILE,
    create_config,
    save_config,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


class Namespace(argparse.Namespace):
    """Namespace for the command line arguments."""

    hostsfile: Path
    localhost: str | None
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
    parser.add_argument(
        "--localhost", help="Which host is the local machine?", type=str, default=None
    )
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


def cli(argv: Sequence[str] | None = None) -> int:
    """Main entry point of the script."""
    args = parse_args(argv)

    config = create_config(
        args.hostsfile,
        args.localhost,
        args.forward_x11,
        args.template,
        args.check_subnet,
        args.ignore_missing,
    )

    if args.no_store:
        print(config, end="")  # noqa: T201
    else:
        save_config(config, args.overwrite)

    return 0
