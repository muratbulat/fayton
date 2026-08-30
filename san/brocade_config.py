#!/usr/bin/env python3
"""Example: create Brocade FC aliases/zones over SSH using pexpect.

This is a self-contained demo script with example alias/zone data baked
in below - edit ALIAS_INFO / ZONE_INFO (or use the CSV-driven
san/brocade_config_csv.py instead) before pointing it at a real switch.

Credentials are never hard-coded; they are read from environment variables
or prompted interactively:
    BROCADE_SWITCH_IP  - switch management IP or hostname
    BROCADE_USERNAME   - switch username
    BROCADE_PASSWORD   - switch password (prompted interactively if unset)
"""
from __future__ import annotations

import getpass
import os
import sys

import pexpect

# Example alias/zone data - replace with your own before running this
# against a real switch, or drive it from CSV via brocade_config_csv.py.
ALIAS_INFO = {
    "server1": "10:00:00:00:00:00:00:01",
    "server2": "10:00:00:00:00:00:00:02",
    "storage1": "10:00:00:00:00:00:00:03",
    "storage2": "10:00:00:00:00:00:00:04",
}

ZONE_INFO = {
    "myzone1": ["server1", "storage1"],
    "myzone2": ["server2", "storage2"],
    "myzone3": ["server1", "storage2"],
}


def main() -> int:
    switch_ip = os.environ.get("BROCADE_SWITCH_IP")
    username = os.environ.get("BROCADE_USERNAME")
    if not switch_ip or not username:
        print("Error: set BROCADE_SWITCH_IP and BROCADE_USERNAME", file=sys.stderr)
        return 1
    password = os.environ.get("BROCADE_PASSWORD") or getpass.getpass(
        f"Password for {username}@{switch_ip}: "
    )

    ssh = pexpect.spawn(f"ssh {username}@{switch_ip}", timeout=15)
    try:
        ssh.expect("password:")
        ssh.sendline(password)
        ssh.expect("#")

        ssh.sendline("configure terminal")
        ssh.expect("#")

        for alias_name, wwpn in ALIAS_INFO.items():
            ssh.sendline(f'alicreate "{alias_name}", "{wwpn}"')
            ssh.expect("#")

        for zone_name, alias_names in ZONE_INFO.items():
            members = ", ".join(f'"{alias}"' for alias in alias_names)
            ssh.sendline(f'zonecreate "{zone_name}", {members}')
            ssh.expect("#")

        ssh.sendline("cfgsave")
        # expect() treats the pattern as a regex, so parentheses/'?' must
        # be escaped or this prompt will never match.
        ssh.expect(r"Do you want to save the configuration\? \(yes, y, no, n\) \[no\]:")
        ssh.sendline("yes")
        ssh.expect("#")

        ssh.sendline("exit")
        ssh.expect(pexpect.EOF)
    except pexpect.exceptions.TIMEOUT as exc:
        print(f"Error: timed out waiting for switch response: {exc}", file=sys.stderr)
        return 1
    except pexpect.exceptions.EOF as exc:
        print(f"Error: connection closed unexpectedly: {exc}", file=sys.stderr)
        return 1
    finally:
        ssh.close()

    print("Aliases created:")
    for alias_name, wwpn in ALIAS_INFO.items():
        print(f"- {alias_name} for WWPN {wwpn}")

    print("Zones created:")
    for zone_name, alias_names in ZONE_INFO.items():
        print(f"- {zone_name} with aliases {alias_names}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
