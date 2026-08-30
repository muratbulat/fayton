#!/usr/bin/env python3
"""Preview Brocade `alicreate` commands generated from a CSV of WWN aliases.

This script only prints the commands it would run - it never connects to a
switch. Use it to review the output before feeding the same CSV file to
brocade_config_csv.py, which actually applies the configuration over SSH.

CSV format (no header row): alias_name,wwn[,wwn...]
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


def generate_alias_commands(csv_path: Path) -> list[str]:
    """Return one `alicreate` command per non-empty row in the CSV file."""
    commands = []
    with csv_path.open("r", newline="") as csvfile:
        for row_num, row in enumerate(csv.reader(csvfile), start=1):
            if not row:
                continue
            if len(row) < 2:
                print(f"Skipping malformed row {row_num}: {row}", file=sys.stderr)
                continue
            alias_name = row[0]
            members = ",".join(row[1:])
            commands.append(f'alicreate "{alias_name}";{members}')
    return commands


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-i", "--input",
        type=Path,
        default=Path("data/alias.csv"),
        help="path to the alias CSV file (default: data/alias.csv)",
    )
    args = parser.parse_args()

    if not args.input.is_file():
        print(f"Error: input file not found: {args.input}", file=sys.stderr)
        return 1

    commands = generate_alias_commands(args.input)

    print("ALIASES")
    print("::::::::::::::::::::::::::::::::::::::::::::")
    for command in commands:
        print(command)
    print("::::::::::::::::::::::::::::::::::::::::::::")
    print("ALIASES")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
