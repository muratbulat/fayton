#!/usr/bin/env python3
"""Preview Brocade `zonecreate` commands generated from a CSV of zones.

This script only prints the commands it would run - it never connects to a
switch. Use it to review the output before feeding the same CSV file to
brocade_config_csv.py, which actually applies the configuration over SSH.

CSV format (no header row): zone_name,member[,member...]
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


def generate_zone_commands(csv_path: Path) -> list[str]:
    """Return one `zonecreate` command per non-empty row in the CSV file."""
    commands = []
    with csv_path.open("r", newline="") as csvfile:
        for row_num, row in enumerate(csv.reader(csvfile), start=1):
            if not row:
                continue
            if len(row) < 2:
                print(f"Skipping malformed row {row_num}: {row}", file=sys.stderr)
                continue
            zone_name = row[0]
            members = ",".join(row[1:])
            commands.append(f'zonecreate "{zone_name}";{members}')
    return commands


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-i", "--input",
        type=Path,
        default=Path("data/zone.csv"),
        help="path to the zone CSV file (default: data/zone.csv)",
    )
    args = parser.parse_args()

    if not args.input.is_file():
        print(f"Error: input file not found: {args.input}", file=sys.stderr)
        return 1

    commands = generate_zone_commands(args.input)

    print("ZONES")
    print("::::::::::::::::::::::::::::::::::::::::::::")
    for command in commands:
        print(command)
    print("::::::::::::::::::::::::::::::::::::::::::::")
    print("ZONES")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
