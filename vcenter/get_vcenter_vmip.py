#!/usr/bin/env python3
"""Export VM name / IP address pairs from vCenter to an Excel file.

Uses the VMware vSphere Automation SDK for Python. Only NICs of type
VMXNET3 on a standard port group are reported, matching a VM's primary
adapter in most simple deployments.

Connection settings are read from environment variables, overridable via
CLI flags:
    VCENTER_SERVER    - vCenter hostname/IP
    VCENTER_USERNAME  - vCenter username
    VCENTER_PASSWORD  - vCenter password (prompted interactively if unset)
"""
from __future__ import annotations

import argparse
import getpass
import os
import sys

from openpyxl import Workbook
from vmware.vapi.vsphere.client import create_vsphere_client


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--server", default=os.environ.get("VCENTER_SERVER"))
    parser.add_argument("--username", default=os.environ.get("VCENTER_USERNAME"))
    parser.add_argument("--output", default="vm_ip_addresses.xlsx", help="output .xlsx path")
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

    session = None
    if args.insecure:
        import requests
        import urllib3

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        print("Warning: TLS certificate verification is disabled (--insecure).", file=sys.stderr)
        session = requests.Session()
        session.verify = False

    try:
        client = create_vsphere_client(
            server=args.server, username=args.username, password=password, session=session
        )
    except Exception as exc:  # the SDK raises assorted connection/auth errors
        print(f"Error: failed to connect to vCenter: {exc}", file=sys.stderr)
        return 1

    network = client.vcenter.vm.Network
    vms = client.vcenter.VM.list()

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "VM IP Addresses"
    worksheet.cell(row=1, column=1, value="VM Name")
    worksheet.cell(row=1, column=2, value="IP Address")

    for i, vm in enumerate(vms):
        ip_address = None
        for nic_info in network.list(vm.vm):
            if nic_info.nic_type == "VMXNET3":
                nic = nic_info.nic
                if nic.backing.network_type == "STANDARD_PORTGROUP":
                    ip_address = nic.ip_address.ip_address
        worksheet.cell(row=i + 2, column=1, value=vm.name)
        worksheet.cell(row=i + 2, column=2, value=ip_address)

    workbook.save(filename=args.output)
    print(f"Wrote {len(vms)} VM(s) to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
