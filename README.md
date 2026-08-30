# Fayton

Fayton is a small, practical toolkit of Python, PowerShell and Ansible
scripts for infrastructure automation: Brocade FC SAN provisioning,
VMware vCenter IP/attribute reporting, NetBox-driven IP allocation for new
vCenter VMs, and Active Directory reporting for logged-in VM users.

It is a collection of standalone scripts, not a framework or a service -
each tool does one job and can be read, copied and adapted on its own.

[Türkçe döküman için README_TR.md dosyasına bakın](README_TR.md).

![fayton](content/fayton_s.jpg)

## Tools

| Script | Purpose |
| --- | --- |
| [`san/san_alias_ex.py`](san/san_alias_ex.py) | Preview Brocade `alicreate` commands from `data/alias.csv` (no switch connection). |
| [`san/san_zone_ex.py`](san/san_zone_ex.py) | Preview Brocade `zonecreate` commands from `data/zone.csv` (no switch connection). |
| [`san/brocade_config_csv.py`](san/brocade_config_csv.py) | Read `data/alias.csv` and `data/zone.csv` and apply the aliases/zones to a real Brocade switch over SSH. |
| [`san/brocade_config.py`](san/brocade_config.py) | Self-contained pexpect example that creates a small set of demo aliases/zones over SSH; edit the data in the script (or use `brocade_config_csv.py`) for real use. |
| [`vcenter/get_vcenter_vmip.py`](vcenter/get_vcenter_vmip.py) | List every VM's name and primary IP address from vCenter and export it to an `.xlsx` report. |
| [`vcenter/vmip_to_vmatt.py`](vcenter/vmip_to_vmatt.py) | Stamp each VM's guest IP address onto a vCenter custom attribute ("IP Address"), with a per-run log file. |
| [`ansible/netbox2vcenter.yml`](ansible/netbox2vcenter.yml) | Allocate the next free IP from a NetBox prefix and resolve netmask/gateway/VLAN/DNS for a new vCenter VM. |
| [`windows/vm_users_ad.ps1`](windows/vm_users_ad.ps1) | For a list of VMs, resolve the logged-in user and report AD group membership counts by department. |

## Repository structure

```
fayton/
├── ansible/
│   ├── netbox2vcenter.yml   # NetBox -> vCenter IP allocation playbook
│   └── requirements.yml     # required Ansible collections
├── san/
│   ├── san_alias_ex.py      # preview alias commands (no connection)
│   ├── san_zone_ex.py       # preview zone commands (no connection)
│   ├── brocade_config_csv.py# apply aliases/zones from CSV over SSH
│   ├── brocade_config.py    # pexpect demo with inline example data
│   ├── data/
│   │   ├── alias.csv        # example alias data
│   │   └── zone.csv         # example zone data
│   └── requirements.txt
├── vcenter/
│   ├── get_vcenter_vmip.py  # VM name/IP -> .xlsx report
│   ├── vmip_to_vmatt.py     # VM guest IP -> vCenter custom attribute
│   └── requirements.txt
├── windows/
│   └── vm_users_ad.ps1      # VM logged-in user -> AD group report
└── content/                 # images used in this README
```

## Requirements

- **SAN scripts** (`san/`): Python 3.9+, packages in [`san/requirements.txt`](san/requirements.txt) (`paramiko`, `pexpect`). Network access/SSH to the Brocade switch.
- **vCenter scripts** (`vcenter/`): Python 3.9+, packages in [`vcenter/requirements.txt`](vcenter/requirements.txt) (`pyvmomi`, `openpyxl`). `get_vcenter_vmip.py` additionally needs the [VMware vSphere Automation SDK for Python](https://github.com/vmware/vsphere-automation-sdk-python), which is not published on PyPI - see the comment in `vcenter/requirements.txt` for the install command.
- **Ansible playbook** (`ansible/`): Ansible/`ansible-core`, plus the collections in [`ansible/requirements.yml`](ansible/requirements.yml) (`netbox.netbox`, `ansible.utils`). Network access to a NetBox instance.
- **PowerShell script** (`windows/`): Windows PowerShell with the `ActiveDirectory` module (RSAT), run from a host with rights to query AD and query target VMs over WinRM (`Get-CimInstance`).

## Installation

```bash
git clone https://github.com/muratbulat/fayton.git
cd fayton

# SAN scripts
pip install -r san/requirements.txt

# vCenter scripts
pip install -r vcenter/requirements.txt
# plus, separately (not on PyPI):
pip install "git+https://github.com/vmware/vsphere-automation-sdk-python.git"

# Ansible playbook
ansible-galaxy collection install -r ansible/requirements.yml
```

The PowerShell script needs no separate install beyond the `ActiveDirectory`
module:

```powershell
Install-WindowsFeature RSAT-AD-PowerShell   # on a Windows Server host, or
Add-WindowsCapability -Online -Name Rsat.ActiveDirectory.DS-LDS.Tools~~~~0.0.1.0
```

## Configuration

None of the scripts contain hard-coded credentials. Set the environment
variables below, or pass the equivalent CLI flags where noted.

| Script(s) | Variable | Notes |
| --- | --- | --- |
| `san/brocade_config_csv.py`, `san/brocade_config.py` | `BROCADE_SWITCH_IP`, `BROCADE_USERNAME`, `BROCADE_PASSWORD` | Password is prompted interactively if unset. `--switch`/`--username` flags override the env vars on `brocade_config_csv.py`. |
| `vcenter/get_vcenter_vmip.py`, `vcenter/vmip_to_vmatt.py` | `VCENTER_SERVER`, `VCENTER_USERNAME`, `VCENTER_PASSWORD` | Password is prompted interactively if unset. `--insecure` disables TLS certificate verification for self-signed vCenter certs - avoid in production. |
| `ansible/netbox2vcenter.yml` | `NETBOX_TOKEN` | Read via `lookup('env', 'NETBOX_TOKEN')`; the play fails fast with a clear message if it's empty. Override `nb_url`/`nb_prefix` with `-e` for your own NetBox instance and prefix. |
| `windows/vm_users_ad.ps1` | n/a (parameters) | Pass `-VmListPath`, `-OutputPath`, and optionally `-Credential`. |

## Usage examples

```bash
# Preview the Brocade commands a CSV would generate, no switch connection
python san/san_alias_ex.py --input san/data/alias.csv
python san/san_zone_ex.py --input san/data/zone.csv

# Apply the same CSVs to a real switch
export BROCADE_SWITCH_IP=10.0.0.10
export BROCADE_USERNAME=admin
python san/brocade_config_csv.py --alias-csv san/data/alias.csv --zone-csv san/data/zone.csv
# ...or preview only, without connecting:
python san/brocade_config_csv.py --alias-csv san/data/alias.csv --zone-csv san/data/zone.csv --dry-run

# Export VM name/IP to Excel
export VCENTER_SERVER=vcenter.example.com
export VCENTER_USERNAME=administrator@vsphere.local
python vcenter/get_vcenter_vmip.py --output vm_ip_addresses.xlsx

# Stamp guest IPs onto a custom attribute
python vcenter/vmip_to_vmatt.py

# Allocate the next NetBox IP for a new vCenter VM
export NETBOX_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ansible-playbook ansible/netbox2vcenter.yml -e nb_prefix=10.48.6.0/24

# AD group report for a list of VMs
.\windows\vm_users_ad.ps1 -VmListPath .\vm_list.txt -OutputPath .\DepartmentGroupCounts.csv
```

## Security considerations

- **No credentials are stored in this repository.** All scripts read
  credentials from environment variables (or an interactive prompt) rather
  than source code. If you fork or adapt these scripts, keep it that way.
- `san/brocade_config_csv.py` and `san/brocade_config.py` use paramiko's
  `AutoAddPolicy`, which trusts a switch's SSH host key on first connect.
  For production use, pre-populate `known_hosts` and switch to
  `RejectPolicy` (see the comment in `brocade_config_csv.py`).
- `--insecure` on the vCenter scripts disables TLS certificate
  verification. It exists for labs with self-signed certificates; do not
  use it against production vCenter without understanding the risk.
- `ansible/netbox2vcenter.yml` marks the tasks that handle the NetBox API
  token with `no_log: true` so the token isn't printed in playbook output.
- `san/data/alias.csv` and `san/data/zone.csv` contain example/placeholder
  WWNs, not real hardware identifiers - replace them with your own data
  before use.
- The default NetBox URL in `netbox2vcenter.yml` (`https://demo.netbox.dev`)
  is NetBox's public read/write demo instance, intentionally left as a
  safe-to-run default; override `nb_url` for your own environment.

## Notes on Windows / Active Directory automation

`windows/vm_users_ad.ps1` uses `Get-CimInstance` (WinRM) rather than the
deprecated `Get-WmiObject` cmdlet. Target VMs must allow WinRM connections
from the host running the script (`Enable-PSRemoting`); if your environment
only supports DCOM, see the notes in the script header.

## Contributing

This is a personal automation toolkit; issues and small, focused pull
requests are welcome via [GitHub](https://github.com/muratbulat/fayton).
