import pexpect

# Define switch connection details
ip_address = '192.168.1.1'
username = 'admin'
password = 'password'

# Define alias details
alias_info = {
    'server1': '10:00:00:00:00:00:00:01',
    'server2': '10:00:00:00:00:00:00:02',
    'storage1': '10:00:00:00:00:00:00:03',
    'storage2': '10:00:00:00:00:00:00:04'
}

# Define zone details
zone_info = {
    'myzone1': ['server1', 'storage1'],
    'myzone2': ['server2', 'storage2'],
    'myzone3': ['server1', 'storage2']
}

# Establish SSH connection to switch
ssh = pexpect.spawn(f'ssh {username}@{ip_address}')
ssh.expect('password:')
ssh.sendline(password)
ssh.expect('#')

# Enter configuration mode
ssh.sendline('configure terminal')
ssh.expect('#')

# Create aliases
for alias_name, wwpn in alias_info.items():
    ssh.sendline(f'alicreate "{alias_name}", "{wwpn}"')
    ssh.expect('#')

# Create zones
for zone_name, alias_names in zone_info.items():
    members = ', '.join(f'"{alias}"' for alias in alias_names)
    ssh.sendline(f'zonecreate "{zone_name}", {members}')
    ssh.expect('#')

# Save configuration changes
ssh.sendline('cfgsave')
ssh.expect('Do you want to save the configuration? (yes, y, no, n) [no]:')
ssh.sendline('yes')
ssh.expect('#')

# Close SSH connection
ssh.sendline('exit')
ssh.expect(pexpect.EOF)
ssh.close()

print('Aliases created:')
for alias_name, wwpn in alias_info.items():
    print(f'- {alias_name} for WWPN {wwpn}')

print('Zones created:')
for zone_name, alias_names in zone_info.items():
    print(f'- {zone_name} with aliases {alias_names}')