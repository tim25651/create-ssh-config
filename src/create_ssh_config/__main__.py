"""Run the create_ssh_config cli if it is called as module."""

from __future__ import annotations

from create_ssh_config.cli import cli

if __name__ == "__main__":
    raise SystemExit(cli())
