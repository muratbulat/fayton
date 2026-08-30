#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stamp each VM's guest IP address(es) onto a vCenter custom attribute.

Connects to vCenter, reads each VM's current guest IP addresses (VMware
Tools must be running), and writes the primary address to the "IP
Address" custom attribute if it isn't already set. A per-VM log of
actions taken is written next to the script and echoed to the console
(messages are in Turkish, as in the original script).

Connection settings are read from environment variables, overridable via
CLI flags:
    VCENTER_SERVER    - vCenter hostname/IP
    VCENTER_USERNAME  - vCenter username
    VCENTER_PASSWORD  - vCenter password (prompted interactively if unset)
"""
from __future__ import annotations

import argparse
import datetime
import getpass
import os
import ssl
import sys

from pyVim.connect import Disconnect, SmartConnect
from pyVmomi import vim


def get_guest_ip_addresses(vm: "vim.VirtualMachine") -> list[str]:
    """Return every IP address reported by VMware Tools across all NICs."""
    addresses: list[str] = []
    for nic in vm.guest.net or []:
        for ip in nic.ipAddress or []:
            if ip:
                addresses.append(ip)
    return addresses


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--server", default=os.environ.get("VCENTER_SERVER"))
    parser.add_argument("--username", default=os.environ.get("VCENTER_USERNAME"))
    parser.add_argument(
        "--insecure", action="store_true",
        help="skip TLS certificate verification (self-signed vCenter certs); not recommended",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.server or not args.username:
        print("Error: set --server/--username or VCENTER_SERVER/VCENTER_USERNAME", file=sys.stderr)
        return 1
    password = os.environ.get("VCENTER_PASSWORD") or getpass.getpass(
        f"Password for {args.username}@{args.server}: "
    )

    ssl_context = None
    if args.insecure:
        print("Warning: TLS certificate verification is disabled (--insecure).", file=sys.stderr)
        ssl_context = ssl._create_unverified_context()

    try:
        si = SmartConnect(host=args.server, user=args.username, pwd=password, sslContext=ssl_context)
    except Exception as exc:
        print(f"Error: failed to connect to vCenter: {exc}", file=sys.stderr)
        return 1

    try:
        content = si.RetrieveContent()
        vm_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)
        vms = vm_view.view
        vm_view.Destroy()

        vcenter_name = si.content.about.instanceUuid
        time_stamp = datetime.datetime.now().strftime("%Y%m%d%H%M")
        file_name = f"{vcenter_name}_{time_stamp}.txt"

        with open(file_name, "w", encoding="utf-8") as f:
            for vm in vms:
                ip_addresses = get_guest_ip_addresses(vm)

                if not ip_addresses:
                    print(vm.name, "Sanal sunucu ip bilgisi yok")
                    f.write(f"{vm.name} Sanal sunucu ip bilgisi yok\n")
                    continue

                if len(ip_addresses) == 1:
                    if vm.GetCustomValue("IP Address") is None:
                        vm.SetCustomValue("IP Address", ip_addresses[0])
                        print(vm.name, "Sanal sunucu attribute ip bilgisine", ip_addresses[0], "yazıldı")
                        f.write(f"{vm.name} Sanal sunucu attribute ip bilgisine {ip_addresses[0]} yazıldı\n")
                    else:
                        print(vm.name, "Sanal sunucu attribute ip bilgisi zaten mevcut")
                        f.write(f"{vm.name} Sanal sunucu attribute ip bilgisi zaten mevcut\n")
                else:
                    print(vm.name, "Sanal sunucu birden fazla IP adresine sahip.")
                    f.write(f"{vm.name} Sanal sunucu birden fazla IP adresine sahip.\n")
                    if vm.GetCustomValue("IP Address") is None:
                        vm.SetCustomValue("IP Address", ip_addresses[0])
                        print(vm.name, "Sanal sunucu attribute ip bilgisine", ip_addresses[0], "yazıldı")
                        f.write(f"{vm.name} Sanal sunucu attribute ip bilgisine {ip_addresses[0]} yazıldı\n")
                    for i in range(1, len(ip_addresses)):
                        print(vm.name, f"Sanal sunucu {i}. IP adresi: {ip_addresses[i]}")
                        f.write(f"{vm.name} Sanal sunucu {i}. IP adresi: {ip_addresses[i]}\n")

        print(f"Log written to {file_name}")
    finally:
        Disconnect(si)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
