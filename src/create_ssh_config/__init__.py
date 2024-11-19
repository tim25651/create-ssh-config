# %%
"""Create a SSH config file for multiple hosts and proxyjumps.

Configured with a JSON which defines each host and its hostnames.
The schema is provided in the `schema.json` file.
```
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import jinja2
import jsonschema
import msgspec

from create_ssh_config.schema import Host, HostName_, ParsedHost

if TYPE_CHECKING:
    from collections.abc import Sequence

TEMPLATE_FILE = Path(__file__).parent / "template.j2"
CHECK_SUBNET_FILE = Path(__file__).parent / "check-subnet"

PREAMBLE = """\
# Keep SSH connections alive
TCPKeepAlive yes
ServerAliveInterval 160

# Hosts
"""

POSTAMBLE = """
# Default settings

Host *
    Compression yes
    PreferredAuthentications publickey
    IdentityFile ~/.ssh/id_ed25519
    GSSAPIAuthentication yes
    GSSAPIDelegateCredentials yes
    {no_x11}ForwardX11 yes
    {no_x11}ForwardX11Trusted yes
    XAuthLocation /opt/X11/bin/xauth
"""


def create_body(
    template: str, hosts: Sequence[Host], localhost: str | None, check_subnet: Path
) -> str:
    """Apply the content of the hosts file to the template and return the config."""
    j2_template = jinja2.Template(template)

    parsed_hosts: dict[str, list[ParsedHost]] = {}

    for host in hosts:
        lhost, user = host.host, host.user
        auth = host.auth
        ifile = host.identityfile
        if lhost in parsed_hosts:
            raise ValueError(f"Duplicate host {lhost}")

        if localhost and lhost == localhost:
            parsed_hosts[lhost] = [("localhost", user, None, None, None, None, None)]
            continue

        parsed_hosts[lhost] = []

        hostnames = host.hostnames
        multiple = len(hostnames) > 1
        has_proxyjump = any(hostname.proxyjump for hostname in hostnames)
        lforce = multiple and has_proxyjump

        for ix, hostname in enumerate(hostnames):
            last = ix == len(hostnames) - 1

            luser = user if last else None
            lauth = auth if last else None

            lhostname = hostname.hostname
            ljump = hostname.proxyjump
            lcheck: Literal["ping"] | HostName_ | None = hostname.check_subnet
            if lforce and not ljump and not last:
                ljump = "none"

            lport = hostname.port
            if lcheck == "ping":
                if lhostname is None:
                    raise ValueError(f"Missing hostname for {lhost}")
                lcheck = lhostname

            if last and lcheck:
                raise ValueError(f"Last hostname must not have check-subnet {lcheck}")

            parsed_hosts[lhost].append(
                (lhostname, luser, lport, ljump, lcheck, lauth, ifile)
            )

    return j2_template.render(
        hosts=parsed_hosts, check_subnet_executable=str(check_subnet)
    )


def finalize_config(body: str, forward_x11: bool = False) -> str:
    """Add the preamble and postamble to the body."""
    return PREAMBLE + body + POSTAMBLE.format(no_x11="" if forward_x11 else "# ")


def save_config(config: str, overwrite: bool = False) -> None:
    """Save the config to the $HOME/.ssh/config file.

    Args:
        config: The content of the config file.
        overwrite: Overwrite the existing config file.
    """
    config_path = Path.home() / ".ssh/config"
    if not overwrite and config_path.exists():
        print(config)  # noqa: T201
        print("=" * 40)  # noqa: T201
        raise FileExistsError("ssh config already exists")

    # if .ssh directory does not exists, create it with 0700 permissions
    ssh_dir = config_path.parent
    if not ssh_dir.exists():
        ssh_dir.mkdir(0o700)

    config_path.write_text(config)


def get_hosts(hostsfile: Path | str) -> list[Host]:
    """Get the validated hosts from the hosts file."""
    if isinstance(hostsfile, Path):
        hosts_content = hostsfile.read_bytes()
    else:
        hosts_content = hostsfile.encode("utf-8")

    raw_hosts = msgspec.json.decode(hosts_content)

    # Validate with the extra attributes provided in the annotations
    # if it succeeds continue with the converted objects
    schema = msgspec.json.schema(list[Host])
    jsonschema.validate(raw_hosts, schema)

    return msgspec.convert(raw_hosts, list[Host])


def validate_check_subnet_script(check_subnet: Path) -> Path:
    """Try to locate the check-subnet script and check if it's in PATH."""
    # try if just the basename is in PATH
    only_name = shutil.which(check_subnet.name)
    if only_name:
        return Path(check_subnet.name)
        # check if the full check-subnet script is in PATH

    full_path = shutil.which(check_subnet)
    if not full_path:
        raise FileNotFoundError(f"check-subnet script {check_subnet} not found")
    return check_subnet


def validate_check_subnet(check_subnet: Path | str, ignore_missing: bool) -> Path:
    """Validate the check_subnet argument."""
    if isinstance(check_subnet, str):
        if not ignore_missing:
            raise ValueError(
                "check_subnet must be Path to be validated or add --ignore-missing"
            )
        check_subnet = Path(check_subnet)

    if not ignore_missing:
        check_subnet = validate_check_subnet_script(check_subnet)

    return check_subnet


def create_config(
    hostsfile: Path | str,
    localhost: str | None = None,
    forward_x11: bool = False,
    template: Path | str = TEMPLATE_FILE,
    check_subnet: Path | str = CHECK_SUBNET_FILE,
    ignore_missing: bool = False,
) -> str:
    """Create an SSH config file from a hosts file."""
    check_subnet = validate_check_subnet(check_subnet, ignore_missing)

    if isinstance(template, Path):
        template = template.read_text("utf-8")

    hosts = get_hosts(hostsfile)
    body = create_body(template, hosts, localhost, check_subnet)
    return finalize_config(body, forward_x11)
