#!/usr/bin/env python3
"""Configure Brocade FC switch aliases and zones from CSV files over SSH.

Reads alias and zone definitions from CSV files and pushes the
corresponding `alicreate` / `zonecreate` commands to a Brocade FOS switch
over SSH (paramiko), then saves and enables the configuration.

This script makes real configuration changes on the target switch. Use
--dry-run first, or preview the same CSV files with san_alias_ex.py /
san_zone_ex.py, before running it against production hardware.

Credentials are never hard-coded; they are read from environment variables
or CLI flags:
    BROCADE_SWITCH_IP  - switch management IP or hostname
    BROCADE_USERNAME   - switch username
    BROCADE_PASSWORD   - switch password (prompted interactively if unset)

CSV format (no header row), matching san_alias_ex.py / san_zone_ex.py:
    alias.csv: alias_name,wwn
    zone.csv:  zone_name,alias_name[,alias_name...]
"""
from __future__ import annotations

import argparse
import csv
import getpass
import os
import sys
from pathlib import Path


def read_aliases(csv_path: Path) -> list[tuple[str, str]]:
    """Return [(alias_name, wwn), ...] from a headerless CSV file."""
    aliases: list[tuple[str, str]] = []
    with csv_path.open("r", newline="") as csvfile:
        for row in csv.reader(csvfile):
            if not row:
                continue
            aliases.append((row[0], row[1]))
    return aliases


def read_zones(csv_path: Path) -> list[tuple[str, list[str]]]:
    """Return [(zone_name, [alias_name, ...]), ...] from a headerless CSV file."""
    zones: list[tuple[str, list[str]]] = []
    with csv_path.open("r", newline="") as csvfile:
        for row in csv.reader(csvfile):
            if not row:
                continue
            zones.append((row[0], row[1:]))
    return zones


def run_command(ssh, command: str) -> None:
    """Execute a command over the SSH session and echo its output."""
    _, stdout, stderr = ssh.exec_command(command)
    out = stdout.read().decode(errors="replace").strip()
    err = stderr.read().decode(errors="replace").strip()
    if out:
        print(out)
    if err:
        print(err, file=sys.stderr)


def create_aliases(ssh, aliases: list[tuple[str, str]]) -> None:
    for alias_name, wwn in aliases:
        run_command(ssh, f'alicreate "{alias_name}","{wwn}"')


def create_zones(ssh, zones: list[tuple[str, list[str]]]) -> None:
    for zone_name, members in zones:
        run_command(ssh, f'zonecreate "{zone_name}","{";".join(members)}"')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--alias-csv", type=Path, default=Path("data/alias.csv"))
    parser.add_argument("--zone-csv", type=Path, default=Path("data/zone.csv"))
    parser.add_argument(
        "--switch", default=os.environ.get("BROCADE_SWITCH_IP"),
        help="switch IP/hostname (env: BROCADE_SWITCH_IP)",
    )
    parser.add_argument(
        "--username", default=os.environ.get("BROCADE_USERNAME"),
        help="switch username (env: BROCADE_USERNAME)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="print the commands that would be run and exit, without connecting",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    for path in (args.alias_csv, args.zone_csv):
        if not path.is_file():
            print(f"Error: CSV file not found: {path}", file=sys.stderr)
            return 1

    aliases = read_aliases(args.alias_csv)
    zones = read_zones(args.zone_csv)

    if args.dry_run:
        for alias_name, wwn in aliases:
            print(f'alicreate "{alias_name}","{wwn}"')
        for zone_name, members in zones:
            print(f'zonecreate "{zone_name}","{";".join(members)}"')
        return 0

    if not args.switch:
        print("Error: switch not set (use --switch or BROCADE_SWITCH_IP)", file=sys.stderr)
        return 1
    if not args.username:
        print("Error: username not set (use --username or BROCADE_USERNAME)", file=sys.stderr)
        return 1
    password = os.environ.get("BROCADE_PASSWORD") or getpass.getpass(
        f"Password for {args.username}@{args.switch}: "
    )

    import paramiko

    ssh = paramiko.SSHClient()
    # AutoAddPolicy trusts unknown host keys on first connect. For
    # production use, pre-populate known_hosts and switch to
    # ssh.load_system_host_keys() + paramiko.RejectPolicy() instead.
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(args.switch, username=args.username, password=password, timeout=15)
        create_aliases(ssh, aliases)
        create_zones(ssh, zones)
        run_command(ssh, "cfgsave")
        run_command(ssh, "cfgenable")
    except (paramiko.SSHException, OSError) as exc:
        print(f"Error: SSH failure: {exc}", file=sys.stderr)
        return 1
    finally:
        ssh.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
