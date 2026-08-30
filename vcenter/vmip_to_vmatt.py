#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import datetime

# Connect to vCenter server
si = SmartConnect(host="<VCENTER_SERVER_IP>", user="<USERNAME>", pwd="<PASSWORD>")
content = si.RetrieveContent()

# Get all VMs
vm_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)
vms = vm_view.view

# Create file name with vCenter name and script run time stamp
vcenter_name = si.content.about.instanceUuid
time_stamp = datetime.datetime.now().strftime("%Y%m%d%H%M")
file_name = f"{vcenter_name}_{time_stamp}.txt"

# Open file for writing logs
with open(file_name, "w") as f:
  # Loop through each VM
  for vm in vms:
    # Get the network adapter info from the annotation
    ip_address=None
    ip_address=vm.guest.ipAddress
    # Set the IP address as an attribute of the VM, if it exists
    if vm.guest.ipAddress != None:
      if len(vm.guest.ipAddress) == 1:
        if vm.GetCustomValue("IP Address") == None:
          vm.SetCustomValue("IP Address", ip_address)
          print(vm.name, "Sanal sunucu attribute ip bilgisine", ip_address, "yazıldı")
          f.write(f"{vm.name} Sanal sunucu attribute ip bilgisine {ip_address} yazıldı\n")
        else:
          print(vm.name, "Sanal sunucu attribute ip bilgisi zaten mevcut")
          f.write(f"{vm.name} Sanal sunucu attribute ip bilgisi zaten mevcut\n")
      else:
        print(vm.name, "Sanal sunucu birden fazla IP adresine sahip.")
        f.write(f"{vm.name} Sanal sunucu birden fazla IP adresine sahip.\n")
        if vm.GetCustomValue("IP Address") == None:
          vm.SetCustomValue("IP Address", vm.guest.ipAddress[0])
          print(vm.name, "Sanal sunucu attribute ip bilgisine", vm.guest.ipAddress[0], "yazıldı")
          f.write(f"{vm.name} Sanal sunucu attribute ip bilgisine {vm.guest.ipAddress[0]} yazıldı\n")
        for i in range(1,len(vm.guest.ipAddress)):
          print(vm.name, f"Sanal sunucu {i}. IP adresi: {vm.guest.ipAddress[i]}\n")
          f.write(f"{vm.name} Sanal sunucu {i}. IP adresi: {vm.guest.ipAddress[i]}\n")
    else:
      print(vm.name, "Sanal sunucu ip bilgisi yok")
      f.write(f"{vm.name} Sanal sunucu ip bilgisi yok\n")

# Disconnect from vCenter server
Disconnect(si)