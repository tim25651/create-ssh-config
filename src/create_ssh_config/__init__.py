"""Create a SSH config file for multiple hosts and proxyjumps.

Configured with a JSON which defines each host and its hostnames.

```json
[
    {
        "host": "host1",
        "user": "user1",
        "auth": "password,publickey", # optional, default: publickey
        "identityfile": "/path/to/identityfile", # optional, default: ~/.ssh/id_ed25519
        "hostname": [
            # at least one hostname is required
            # the last hostnames check_subnet must be undefined or null
            # everything else is optional
            # if the check_subnet is "ping" the hostname is used.
            {
                # everything is optional
                "hostname": "host1.example.com", # no default
                "proxyjump": "other host" # default: none
                "check_subnet": "ping", # default: arguments to check_subnet script
                                        # if ping, the hostname is used
                "port": 1222 # default: 22
            }
            #
        ]
    }
]
```
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict

import jinja2
import msgspec
from typing_extensions import NotRequired, TypeAlias

if TYPE_CHECKING:
    from collections.abc import Sequence

TEMPLATE_FILE = Path(__file__).parent / "template.j2"
CHECK_SUBNET_FILE = Path(__file__).parent / "check_subnet"

ParsedHost: TypeAlias = "tuple[str | None, str | None, int | None, str | None, str | None, str | None, str | None]"  # noqa: E501


class HostnameDef(TypedDict, total=False):
    """Layout of a single hostname in a host."""

    hostname: str
    proxyjump: str
    check_subnet: str
    port: int


class Host(TypedDict):
    """Layout of a host in the hosts file."""

    host: str
    user: str
    hostname: list[HostnameDef]
    auth: NotRequired[str]
    identityfile: NotRequired[str]


class Namespace(argparse.Namespace):
    """Namespace for the command line arguments."""

    hostsfile: Path
    localhost: str
    overwrite: bool
    forward_x11: bool
    no_store: bool
    template: Path
    check_subnet: Path


def parse_args() -> Namespace:
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
        help="Path to the check_subnet script",
        type=Path,
        default=CHECK_SUBNET_FILE,
    )
    return parser.parse_args()  # type: ignore[return-value]


def create_config(
    template: str,
    hosts: Sequence[Host],
    localhost: str,
    check_subnet: Path,
    forward_x11: bool,
) -> str:
    """Apply the content of the hosts file to the template and return the config."""
    j2_template = jinja2.Template(template)

    parsed_hosts: dict[str, list[ParsedHost]] = {}

    no_x11 = "# " if not forward_x11 else ""

    for host in hosts:
        lhost, user = host["host"], host["user"]
        auth = host.get("auth")
        ifile = host.get("identityfile")
        if lhost in parsed_hosts:
            raise ValueError(f"Duplicate host {lhost}")

        if lhost == localhost:
            parsed_hosts[lhost] = [("localhost", user, None, None, None, None, None)]
            continue

        parsed_hosts[lhost] = []

        hostnames = host["hostname"]
        if not hostnames:
            raise ValueError(f"Missing hostname for {lhost}")

        multiple = len(hostnames) > 1
        has_proxyjump = any(hostname.get("proxyjump") for hostname in hostnames)
        lforce = multiple and has_proxyjump

        for ix, hostname in enumerate(hostnames):
            last = ix == len(hostnames) - 1

            luser = user if last else None
            lauth = auth if last else None

            lhostname = hostname.get("hostname")
            ljump = hostname.get("proxyjump")
            lcheck = hostname.get("check_subnet")
            if lforce and not ljump and not last:
                ljump = "none"

            lport = hostname.get("port")
            if lcheck == "ping":
                if lhostname is None:
                    raise ValueError(f"Missing hostname for {lhost}")
                lcheck = lhostname

            if last and lcheck:
                raise ValueError(f"Last hostname must not have check_subnet {lcheck}")

            parsed_hosts[lhost].append(
                (lhostname, luser, lport, ljump, lcheck, lauth, ifile)
            )

    return j2_template.render(
        hosts=parsed_hosts, check_subnet_executable=str(check_subnet), no_x11=no_x11
    )


def print_config(config: str) -> None:
    """Print the config to the console."""
    print(config)  # noqa: T201


def save_config(config: str, overwrite: bool = False) -> None:
    """Save the config to the $HOME/.ssh/config file.

    Args:
        config: The content of the config file.
        overwrite: Overwrite the existing config file.
    """
    config_path = Path.home() / ".ssh/config"
    if not overwrite and config_path.exists():
        print_config(config)
        print("=" * 40)  # noqa: T201
        raise FileExistsError("ssh config already exists")

    # if .ssh directory does not exists, create it with 0700 permissions
    ssh_dir = config_path.parent
    if not ssh_dir.exists():
        ssh_dir.mkdir(0o700)

    config_path.write_text(config)


def cli() -> int:
    """Main entry point of the script."""
    args = parse_args()

    # try if name is in PATH
    only_name = shutil.which(args.check_subnet.name)
    if only_name:
        args.check_subnet = Path(args.check_subnet.name)
    else:
        # check if the full check_subnet script is in PATH
        full_path = shutil.which(args.check_subnet)
        if not full_path:
            raise FileNotFoundError(
                f"check_subnet script {args.check_subnet} not found"
            )

    template = args.template.read_text("utf-8")
    hosts_content = args.hostsfile.read_bytes()
    raw_hosts = msgspec.json.decode(hosts_content)
    hosts = msgspec.convert(raw_hosts, list[Host])
    config = create_config(
        template, hosts, args.localhost, args.check_subnet, args.forward_x11
    )

    if args.no_store:
        print_config(config)
    else:
        save_config(config, args.overwrite)

    return 0
