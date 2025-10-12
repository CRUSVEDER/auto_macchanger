#!/usr/bin/env python

import subprocess 


interface = input("interface> ")
new_mac = input("new_mac> ")

print("[+] Changing MAC adderss for " + interface + " to " + new_mac)


subprocess.call("ifconfig " + interface + " down", shell=True) 
subprocess.call("ifconfig " + interface + " hw ether " + new_mac, shell=True) 
subprocess.call("ifconfig " + interface + " up", shell=True)
