import csv
import paramiko

# Define variables for the switch's IP address, username, and password
switch_ip = "192.168.0.1"
switch_username = "admin"
switch_password = "password"

# Define variables for the paths to the alias.csv and zone.csv files
alias_csv_file = "data/alias.csv"
zone_csv_file = "data/zone.csv"

# Create a dictionary to store the alias information
alias_dict = {}

# Open the alias.csv file and read its contents
with open(alias_csv_file, 'r') as csvfile:
    reader = csv.reader(csvfile)
    # Skip the header row
    next(reader)
    # Loop through each row in the file
    for row in reader:
        # Add the alias name and WWN to the dictionary
        alias_dict[row[0]] = row[1]

# Create a list to store the WWNs that need aliases
wwn_list = []

# Open the zone.csv file and read its contents
with open(zone_csv_file, 'r') as csvfile:
    reader = csv.reader(csvfile)
    # Skip the header row
    next(reader)
    # Loop through each row in the file
    for row in reader:
        # Loop through each WWN in the row
        for wwn in row[1:]:
            # If the WWN is not already an alias, add it to the list
            if wwn not in alias_dict.values() and wwn not in wwn_list:
                wwn_list.append(wwn)

# Connect to the switch using SSH
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(switch_ip, username=switch_username, password=switch_password)

# Create aliases for the WWNs that don't already have aliases
for wwn in wwn_list:
    # Generate an alias name for the WWN
    alias_name = "alias_" + wwn.replace(":", "")
    # Create the alias configuration command
    command = "alicreate \"" + alias_name + "\",\"" + wwn + "\""
    # Execute the command on the switch
    stdin, stdout, stderr = ssh.exec_command(command)
    # Print any output or errors from the command
    print(stdout.read())
    print(stderr.read())
    # Add the alias name and WWN to the dictionary
    alias_dict[alias_name] = wwn

# Create a list to store the zone information
zone_list = []

# Open the zone.csv file and read its contents
with open(zone_csv_file, 'r') as csvfile:
    reader = csv.reader(csvfile)
    # Skip the header row
    next(reader)
    # Loop through each row in the file
    for row in reader:
        # Create a list to store the aliases in the zone
        alias_list = []
        # Loop through each WWN in the row
        for wwn in row[1:]:
            # Look up the alias name for the WWN
            alias_name = [k for k, v in alias_dict.items() if v == wwn]
            # Add the alias name to the list
            alias_list.extend(alias_name)
        # Add the zone name and alias list to the zone list
        zone_list.append((row[0], alias_list))

# Configure the switch with the zone information
for zone_name, alias_list in zone_list:
    # Create the zone configuration command
    members = ";".join(alias_list)
    command = "zonecreate \"" + zone_name + "\",\"" + members + "\""
    # Execute the command on the switch
    stdin, stdout, stderr = ssh.exec_command(command)
    # Print any output or errors from the command
    print(stdout.read())
    print(stderr.read())

# Save the configuration to the startup configuration file
stdin, stdout, stderr = ssh.exec_command("cfgsave")
# Print any output or errors from the command
print(stdout.read())
print(stderr.read())

# Enable the configuration
stdin, stdout, stderr = ssh.exec_command("cfgenable")
# Print any output or errors from the command
print(stdout.read())
print(stderr.read())

# Close the SSH connection
ssh.close()
