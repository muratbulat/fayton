# Fayton

Fayton; Brocade FC SAN yapılandırması, VMware vCenter IP/attribute
raporlama, yeni vCenter VM'leri için NetBox tabanlı IP tahsisi ve VM'lere
giriş yapmış kullanıcılar için Active Directory raporlaması amacıyla
yazılmış küçük ve pratik bir Python / PowerShell / Ansible script
koleksiyonudur.

Bu bir framework veya servis değil, bağımsız script'lerden oluşan bir
koleksiyondur - her araç tek bir işi yapar ve tek başına okunup
uyarlanabilir.

[For the English document, see README.md](README.md).

![fayton](content/fayton_s.jpg)

## Araçlar

| Script | Amaç |
| --- | --- |
| [`san/san_alias_ex.py`](san/san_alias_ex.py) | `data/alias.csv` dosyasından Brocade `alicreate` komutlarını önizler (switch'e bağlanmaz). |
| [`san/san_zone_ex.py`](san/san_zone_ex.py) | `data/zone.csv` dosyasından Brocade `zonecreate` komutlarını önizler (switch'e bağlanmaz). |
| [`san/brocade_config_csv.py`](san/brocade_config_csv.py) | `data/alias.csv` ve `data/zone.csv` dosyalarını okuyup gerçek bir Brocade switch üzerinde SSH ile alias/zone yapılandırması uygular. |
| [`san/brocade_config.py`](san/brocade_config.py) | pexpect kullanan, örnek verilerle çalışan bağımsız bir demo script'idir; gerçek kullanım için script içindeki verileri düzenleyin (veya `brocade_config_csv.py` kullanın). |
| [`vcenter/get_vcenter_vmip.py`](vcenter/get_vcenter_vmip.py) | vCenter'daki tüm VM'lerin adını ve birincil IP adresini listeleyip `.xlsx` raporu olarak dışa aktarır. |
| [`vcenter/vmip_to_vmatt.py`](vcenter/vmip_to_vmatt.py) | Her VM'in guest IP adresini vCenter custom attribute'una ("IP Address") yazar; her çalıştırma için bir log dosyası oluşturur. |
| [`ansible/netbox2vcenter.yml`](ansible/netbox2vcenter.yml) | Bir NetBox prefix'inden bir sonraki boş IP'yi alır ve yeni bir vCenter VM'i için netmask/gateway/VLAN/DNS bilgilerini çözer. |
| [`windows/vm_users_ad.ps1`](windows/vm_users_ad.ps1) | Bir VM listesi için o an giriş yapmış kullanıcıyı bulur ve departman bazında AD grup üyeliği sayılarını raporlar. |

## Depo yapısı

```
fayton/
├── ansible/
│   ├── netbox2vcenter.yml   # NetBox -> vCenter IP tahsis playbook'u
│   └── requirements.yml     # gerekli Ansible collection'ları
├── san/
│   ├── san_alias_ex.py      # alias komutlarını önizle (bağlantı yok)
│   ├── san_zone_ex.py       # zone komutlarını önizle (bağlantı yok)
│   ├── brocade_config_csv.py# CSV'den alias/zone'ları SSH ile uygula
│   ├── brocade_config.py    # örnek verilerle çalışan pexpect demo'su
│   ├── data/
│   │   ├── alias.csv        # örnek alias verisi
│   │   └── zone.csv         # örnek zone verisi
│   └── requirements.txt
├── vcenter/
│   ├── get_vcenter_vmip.py  # VM adı/IP -> .xlsx raporu
│   ├── vmip_to_vmatt.py     # VM guest IP -> vCenter custom attribute
│   └── requirements.txt
├── windows/
│   └── vm_users_ad.ps1      # VM'e giriş yapan kullanıcı -> AD grup raporu
└── content/                 # bu README'de kullanılan görseller
```

## Gereksinimler

- **SAN script'leri** (`san/`): Python 3.9+, [`san/requirements.txt`](san/requirements.txt) içindeki paketler (`paramiko`, `pexpect`). Brocade switch'e ağ erişimi/SSH.
- **vCenter script'leri** (`vcenter/`): Python 3.9+, [`vcenter/requirements.txt`](vcenter/requirements.txt) içindeki paketler (`pyvmomi`, `openpyxl`). `get_vcenter_vmip.py` ayrıca [VMware vSphere Automation SDK for Python](https://github.com/vmware/vsphere-automation-sdk-python) gerektirir; bu paket PyPI'da yayınlanmadığı için `vcenter/requirements.txt` içindeki kurulum komutuna bakın.
- **Ansible playbook'u** (`ansible/`): Ansible/`ansible-core` ve [`ansible/requirements.yml`](ansible/requirements.yml) içindeki collection'lar (`netbox.netbox`, `ansible.utils`). Bir NetBox instance'ına ağ erişimi.
- **PowerShell script'i** (`windows/`): `ActiveDirectory` modülü (RSAT) kurulu Windows PowerShell; AD sorgulama ve hedef VM'lere WinRM üzerinden erişim (`Get-CimInstance`) yetkisi olan bir makineden çalıştırılmalı.

## Kurulum

```bash
git clone https://github.com/muratbulat/fayton.git
cd fayton

# SAN script'leri
pip install -r san/requirements.txt

# vCenter script'leri
pip install -r vcenter/requirements.txt
# ayrıca, PyPI'da olmadığı için ayrı bir adım:
pip install "git+https://github.com/vmware/vsphere-automation-sdk-python.git"

# Ansible playbook'u
ansible-galaxy collection install -r ansible/requirements.yml
```

PowerShell script'i, `ActiveDirectory` modülü dışında ayrı bir kuruluma
ihtiyaç duymaz:

```powershell
Install-WindowsFeature RSAT-AD-PowerShell   # bir Windows Server üzerinde, veya
Add-WindowsCapability -Online -Name Rsat.ActiveDirectory.DS-LDS.Tools~~~~0.0.1.0
```

## Yapılandırma

Script'lerin hiçbirinde sabit kodlanmış (hard-coded) kimlik bilgisi
bulunmaz. Aşağıdaki ortam değişkenlerini ayarlayın, veya belirtilen yerlerde
karşılık gelen komut satırı parametrelerini kullanın.

| Script(ler) | Değişken | Notlar |
| --- | --- | --- |
| `san/brocade_config_csv.py`, `san/brocade_config.py` | `BROCADE_SWITCH_IP`, `BROCADE_USERNAME`, `BROCADE_PASSWORD` | Şifre ayarlanmazsa interaktif olarak sorulur. `--switch`/`--username` parametreleri `brocade_config_csv.py` üzerinde ortam değişkenlerini geçersiz kılar. |
| `vcenter/get_vcenter_vmip.py`, `vcenter/vmip_to_vmatt.py` | `VCENTER_SERVER`, `VCENTER_USERNAME`, `VCENTER_PASSWORD` | Şifre ayarlanmazsa interaktif olarak sorulur. `--insecure` self-signed vCenter sertifikaları için TLS doğrulamasını devre dışı bırakır - production'da kullanmaktan kaçının. |
| `ansible/netbox2vcenter.yml` | `NETBOX_TOKEN` | `lookup('env', 'NETBOX_TOKEN')` ile okunur; boşsa playbook net bir hata mesajıyla erken durur. Kendi NetBox instance'ınız/prefix'iniz için `-e` ile `nb_url`/`nb_prefix` değerlerini geçersiz kılın. |
| `windows/vm_users_ad.ps1` | yok (parametreler) | `-VmListPath`, `-OutputPath` ve isteğe bağlı `-Credential` parametrelerini geçin. |

## Kullanım örnekleri

```bash
# Bir CSV'nin üreteceği Brocade komutlarını önizle, switch'e bağlanmadan
python san/san_alias_ex.py --input san/data/alias.csv
python san/san_zone_ex.py --input san/data/zone.csv

# Aynı CSV'leri gerçek bir switch'e uygula
export BROCADE_SWITCH_IP=10.0.0.10
export BROCADE_USERNAME=admin
python san/brocade_config_csv.py --alias-csv san/data/alias.csv --zone-csv san/data/zone.csv
# ...veya sadece önizle, bağlanmadan:
python san/brocade_config_csv.py --alias-csv san/data/alias.csv --zone-csv san/data/zone.csv --dry-run

# VM adı/IP bilgisini Excel'e aktar
export VCENTER_SERVER=vcenter.example.com
export VCENTER_USERNAME=administrator@vsphere.local
python vcenter/get_vcenter_vmip.py --output vm_ip_addresses.xlsx

# Guest IP'lerini custom attribute'a yaz
python vcenter/vmip_to_vmatt.py

# Yeni bir vCenter VM'i için NetBox'tan bir sonraki IP'yi tahsis et
export NETBOX_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ansible-playbook ansible/netbox2vcenter.yml -e nb_prefix=10.48.6.0/24

# Bir VM listesi için AD grup raporu
.\windows\vm_users_ad.ps1 -VmListPath .\vm_list.txt -OutputPath .\DepartmentGroupCounts.csv
```

## Güvenlik notları

- **Bu depoda hiçbir kimlik bilgisi saklanmaz.** Tüm script'ler kimlik
  bilgilerini kaynak kod yerine ortam değişkenlerinden (veya interaktif
  bir promptdan) okur. Bu script'leri fork'layıp uyarlarsanız bu yaklaşımı
  koruyun.
- `san/brocade_config_csv.py` ve `san/brocade_config.py`, paramiko'nun
  `AutoAddPolicy`'sini kullanır; bu, ilk bağlantıda switch'in SSH host
  key'ine güvenilmesi anlamına gelir. Production kullanımı için
  `known_hosts` dosyasını önceden doldurup `RejectPolicy`'ye geçin
  (`brocade_config_csv.py` içindeki yoruma bakın).
- vCenter script'lerindeki `--insecure` parametresi TLS sertifika
  doğrulamasını devre dışı bırakır. Bu, self-signed sertifikalı lab
  ortamları için vardır; riski anlamadan production vCenter'a karşı
  kullanmayın.
- `ansible/netbox2vcenter.yml`, NetBox API token'ını işleyen task'ları
  `no_log: true` ile işaretler; böylece token playbook çıktısında
  görünmez.
- `san/data/alias.csv` ve `san/data/zone.csv` örnek/placeholder WWN'ler
  içerir, gerçek donanım kimlikleri değildir - kullanmadan önce kendi
  verilerinizle değiştirin.
- `netbox2vcenter.yml` içindeki varsayılan NetBox URL'i
  (`https://demo.netbox.dev`), NetBox'ın herkese açık okuma/yazma demo
  instance'ıdır ve bilinçli olarak güvenli bir varsayılan olarak
  bırakılmıştır; kendi ortamınız için `nb_url` değerini geçersiz kılın.

## Windows / Active Directory otomasyonu hakkında notlar

`windows/vm_users_ad.ps1`, deprecated olan `Get-WmiObject` yerine
`Get-CimInstance` (WinRM) kullanır. Hedef VM'lerin, script'i çalıştıran
makineden WinRM bağlantılarına izin vermesi gerekir (`Enable-PSRemoting`);
ortamınız sadece DCOM destekliyorsa script başlığındaki notlara bakın.

## Katkıda bulunma

Bu kişisel bir otomasyon araç seti; issue'lar ve küçük, odaklı pull
request'ler [GitHub](https://github.com/muratbulat/fayton) üzerinden
memnuniyetle karşılanır.
