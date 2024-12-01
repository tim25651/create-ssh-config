#%%
"""Define the schema for the hosts file."""

from __future__ import annotations

from typing import Annotated, Literal, TypeAlias

from msgspec import Meta, Struct

AuthMethods = Literal["password", "publickey", "keyboard-interactive"]
User_ = Annotated[
    str, Meta(min_length=1, max_length=32, pattern="^[a-zA-Z_][a-zA-Z0-9_-]*$")
]

SchemaPath = Annotated[str, Meta(extra_json_schema={"type": "string", "format": "uri"})]
Port = Annotated[int, Meta(ge=0, le=65535)]

# Hostname can either be an IPv4 or a UnixName but including periods.
HostName_ = Annotated[
    str,
    Meta(
        extra_json_schema={
            "anyOf": [
                {
                    "type": "string",
                    "pattern": r"^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$",  # noqa: E501
                },
                {
                    "type": "string",
                    "pattern": r"^((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.?\b){4}$",
                },
                # allow a-AA-Z0-9, hyphen
                {"type": "string", "pattern": r"^[a-zA-Z0-9-]+$"},
            ]
        }
    ),
]
# Host can also include globbing characters
Host_ = Annotated[str, Meta(pattern=r"^[a-zA-Z0-9*\.-]+$")]

ParsedHost: TypeAlias = "tuple[str | None, str | None, int | None, str | None, HostName_ | None, list[AuthMethods] | None, str | None]"  # noqa: E501


class Hostname(
    Struct, rename={"check_subnet": "check-subnet"}, forbid_unknown_fields=True
):
    """Layout of a hostname in the hosts file."""

    hostname: HostName_ | None = None
    proxyjump: HostName_ | None = None
    check_subnet: HostName_ | Literal["ping"] | None = None
    port: Port | None = None


class Host(Struct, forbid_unknown_fields=True):
    """Layout of a host in the hosts file."""

    host: Host_
    user: User_
    hostnames: Annotated[list[Hostname], Meta(min_length=1)]
    auth: list[AuthMethods] | None = None
    identityfile: SchemaPath | None = None
