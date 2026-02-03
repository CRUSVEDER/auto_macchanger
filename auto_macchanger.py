#!/usr/bin/env python3
# ============================================================
# AUTO MAC IDENTITY ENGINE
# Author: github.com/CRUSVEDER
# ============================================================

import os
import sys
import time
import json
import re
import random
import shutil
import subprocess
import signal
from datetime import datetime

# ============================================================
# CONSTANTS / CONFIG
# ============================================================

PROFILE_FILE = "/var/lib/mac_identity_profiles.json"
DHCP_DELAY = 2

VENDOR_OUIS = {
    "apple": ["f0:18:98", "3c:15:c2", "a4:5e:60"],
    "intel": ["3c:fd:fe", "98:4f:ee"],
    "samsung": ["bc:14:ef", "d8:55:a3"],
    "realtek": ["00:e0:4c", "52:54:00"],
    "raspberrypi": ["b8:27:eb", "dc:a6:32"],
    "vmware": ["00:50:56"],
    "virtualbox": ["08:00:27"],
}

INTERFACE_VENDOR_MAP = {
    "wlan": ["apple", "samsung", "realtek", "raspberrypi"],
    "eth": ["intel", "realtek"],
    "vm": ["vmware", "virtualbox"],
}

HOSTNAME_PROFILES = {
    "apple": ["MacBook-Pro", "MacBook-Air"],
    "intel": ["ThinkPad", "Dell-Laptop"],
    "samsung": ["Galaxy-S21"],
    "raspberrypi": ["raspberrypi"],
    "vmware": ["vmware-host"],
    "virtualbox": ["vbox"],
}

TTL_PROFILES = {
    "apple": 64,
    "intel": 64,
    "samsung": 64,
    "raspberrypi": 64,
    "realtek": 64,
    "vmware": 128,
    "virtualbox": 128,
}

# ============================================================
# UI / STYLING
# ============================================================

BOLD = "\033[1m"
CYAN = "\033[96m"
RED = "\033[91m"
RESET = "\033[0m"

def banner():
    print(r"""
 █████╗ ██╗   ██╗████████╗ ██████╗     ███╗   ███╗ █████╗  ██████╗
██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗    ████╗ ████║██╔══██╗██╔════╝
███████║██║   ██║   ██║   ██║   ██║    ██╔████╔██║███████║██║     
██╔══██║██║   ██║   ██║   ██║   ██║    ██║╚██╔╝██║██╔══██║██║     
██║  ██║╚██████╔╝   ██║   ╚██████╔╝    ██║ ╚═╝ ██║██║  ██║╚██████╗
╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝     ╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝
        AUTO MAC IDENTITY ENGINE — CRUSVEDER
""")

def prompt(msg):
    return input(f"{BOLD}{CYAN}{msg}{RESET} ").strip()

# ============================================================
# SYSTEM HELPERS
# ============================================================

def require_root():
    if os.geteuid() != 0:
        print(f"{RED}[-] Run as root{RESET}")
        sys.exit(1)

def iface_exists(iface):
    return os.path.exists(f"/sys/class/net/{iface}")

def detect_tool():
    if shutil.which("ip"):
        return "ip"
    if shutil.which("ifconfig"):
        return "ifconfig"
    sys.exit("[-] ip/ifconfig not found")

def run(cmd, dry=False):
    if dry:
        print("[DRY]", " ".join(cmd))
        return True
    return subprocess.run(cmd, stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL).returncode == 0

# ============================================================
# NETWORK LOGIC
# ============================================================

def iface_type(iface):
    if iface.startswith("wl"):
        return "wlan"
    if iface.startswith(("eth", "en")):
        return "eth"
    if iface.startswith("vm"):
        return "vm"
    return "unknown"

def current_ssid():
    try:
        r = subprocess.run(["iwgetid", "-r"],
                           stdout=subprocess.PIPE, text=True)
        return r.stdout.strip() or None
    except:
        return None

def load_profiles():
    if not os.path.exists(PROFILE_FILE):
        return {}
    with open(PROFILE_FILE) as f:
        return json.load(f)

def save_profiles(p):
    os.makedirs(os.path.dirname(PROFILE_FILE), exist_ok=True)
    with open(PROFILE_FILE, "w") as f:
        json.dump(p, f, indent=2)

def auto_vendor(iface):
    return random.choice(INTERFACE_VENDOR_MAP.get(iface_type(iface), []))

def persistent_vendor(iface):
    ssid = current_ssid()
    profiles = load_profiles()
    if ssid and ssid in profiles:
        return profiles[ssid]
    vendor = auto_vendor(iface)
    if ssid and vendor:
        profiles[ssid] = vendor
        save_profiles(profiles)
    return vendor

# ============================================================
# MAC / FINGERPRINT
# ============================================================

def random_mac(vendor=None, prefix=None):
    if vendor:
        prefix = random.choice(VENDOR_OUIS[vendor])

    if prefix:
        base = prefix.split(":")
        while len(base) < 3:
            base.append(f"{random.randint(0,255):02x}")
        first = base[:3]
    else:
        b = (random.randint(0,255) & 0b11111100) | 0b00000010
        first = [f"{b:02x}", f"{random.randint(0,255):02x}",
                 f"{random.randint(0,255):02x}"]

    last = [f"{random.randint(0,255):02x}" for _ in range(3)]
    return ":".join(first + last)

def apply_fingerprint(vendor, dry):
    if not vendor:
        return
    hostname = random.choice(HOSTNAME_PROFILES.get(vendor, ["linux-host"]))
    ttl = TTL_PROFILES.get(vendor, 64)

    if dry:
        print(f"[DRY] hostname → {hostname}")
        print(f"[DRY] TTL → {ttl}")
        return

    subprocess.run(["hostnamectl", "set-hostname", hostname])
    subprocess.run(["sysctl", "-w",
                    f"net.ipv4.ip_default_ttl={ttl}"],
                   stdout=subprocess.DEVNULL)

# ============================================================
# CORE CLASS
# ============================================================

class MACIdentityChanger:
    def __init__(self, iface, tool, dry=False, log=None):
        self.iface = iface
        self.tool = tool
        self.dry = dry
        self.log_file = log
        self.original = self.current_mac()
        self.restored = False

    def log(self, msg):
        line = f"[{datetime.now():%F %T}] {msg}"
        print(line)
        if self.log_file:
            with open(self.log_file, "a") as f:
                f.write(line + "\n")

    def current_mac(self):
        r = subprocess.run(["ip", "link", "show", self.iface],
                           stdout=subprocess.PIPE, text=True)
        m = re.search(r"link/ether\s+([0-9a-f:]{17})", r.stdout)
        return m.group(1) if m else None

    def set_mac(self, mac):
        cmds = (
            [["ip", "link", "set", self.iface, "down"],
             ["ip", "link", "set", self.iface, "address", mac],
             ["ip", "link", "set", self.iface, "up"]]
            if self.tool == "ip" else
            [["ifconfig", self.iface, "down"],
             ["ifconfig", self.iface, "ether", mac],
             ["ifconfig", self.iface, "up"]]
        )
        for c in cmds:
            run(c, self.dry)
        time.sleep(DHCP_DELAY)

    def restore(self):
        if not self.restored and self.original:
            self.log(f"Restoring MAC → {self.original}")
            self.set_mac(self.original)
            self.restored = True

# ============================================================
# SIGNAL HANDLING
# ============================================================

changer = None
restore_on_exit = True

def safe_exit(*_):
    print("\n[!] Exiting safely")
    if restore_on_exit and changer:
        changer.restore()
    sys.exit(0)

signal.signal(signal.SIGINT, safe_exit)
signal.signal(signal.SIGTERM, safe_exit)

# ============================================================
# MAIN
# ============================================================

def main():
    global changer, restore_on_exit

    require_root()
    banner()

    iface = prompt("Interface:")
    if not iface_exists(iface):
        sys.exit("[-] Interface not found")

    interval = int(prompt("Interval seconds [60]:") or 60)
    count = int(prompt("Change count (0=∞):") or 0)

    dry = prompt("Dry-run? (y/n):").lower() == "y"
    restore_on_exit = prompt("Restore on exit? (y/n):").lower() == "y"
    logf = prompt("Log file (optional):") or None

    vendor = persistent_vendor(iface)
    tool = detect_tool()

    changer = MACIdentityChanger(iface, tool, dry, logf)
    changer.log(f"Vendor profile → {vendor}")

    i = 0
    try:
        while True:
            i += 1
            if count and i > count:
                break
            mac = random_mac(vendor)
            changer.log(f"[{i}] MAC → {mac}")
            changer.set_mac(mac)
            apply_fingerprint(vendor, dry)
            time.sleep(interval)
    finally:
        safe_exit()

if __name__ == "__main__":
    main()
