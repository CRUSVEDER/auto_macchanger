#!/usr/bin/env python3

# Elite MAC Identity Engine
# Author: github.com/CRUSVEDER


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
#====================== BANNER =====================

def print_banner():
    banner = r"""
 █████╗ ██╗   ██╗████████╗ ██████╗     ███╗   ███╗ █████╗  ██████╗
██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗    ████╗ ████║██╔══██╗██╔════╝
███████║██║   ██║   ██║   ██║   ██║    ██╔████╔██║███████║██║     
██╔══██║██║   ██║   ██║   ██║   ██║    ██║╚██╔╝██║██╔══██║██║     
██║  ██║╚██████╔╝   ██║   ╚██████╔╝    ██║ ╚═╝ ██║██║  ██║╚██████╗
╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝     ╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝

                 AUTO  MAC  IDENTITY  ENGINE
                   by github.com/CRUSVEDER
"""
    print(banner)
# ===================== INPUT STYLING =====================

BOLD = "\033[1m"
CYAN = "\033[96m"
RED = "\033[91m"
RESET = "\033[0m"

def prompt(text):
    return input(f"{BOLD}{CYAN}{text}{RESET} ")


# ===================== CONFIG =====================

NETWORK_PROFILE_FILE = "/var/lib/mac_identity_profiles.json"
DHCP_SETTLE_DELAY = 2  # seconds

VENDOR_OUIS = {
    "apple": ["f0:18:98", "3c:15:c2", "a4:5e:60"],
    "intel": ["3c:fd:fe", "98:4f:ee"],
    "samsung": ["bc:14:ef", "d8:55:a3"],
    "realtek": ["00:e0:4c", "52:54:00"],
    "raspberrypi": ["b8:27:eb", "dc:a6:32"],
    "vmware": ["00:50:56"],
    "virtualbox": ["08:00:27"]
}

INTERFACE_VENDOR_MAP = {
    "wlan": ["apple", "samsung", "realtek", "raspberrypi"],
    "eth": ["intel", "realtek"],
    "vm": ["vmware", "virtualbox"]
}

HOSTNAME_PROFILES = {
    "apple": ["MacBook-Pro", "MacBook-Air"],
    "intel": ["ThinkPad", "Dell-Laptop"],
    "samsung": ["Galaxy-S21"],
    "raspberrypi": ["raspberrypi"],
    "vmware": ["vmware-host"],
    "virtualbox": ["vbox"]
}

TTL_PROFILES = {
    "apple": 64,
    "intel": 64,
    "samsung": 64,
    "raspberrypi": 64,
    "realtek": 64,
    "vmware": 128,
    "virtualbox": 128
}

# ===================== BASIC UTILS =====================

def require_root():
    if os.geteuid() != 0:
        print(f"{BOLD}{RED}[-] Run as root.{RESET}")
        
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
    return subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0

# ===================== NETWORK HELPERS =====================

def detect_interface_type(iface):
    if iface.startswith("wl"):
        return "wlan"
    if iface.startswith(("eth", "en")):
        return "eth"
    if iface.startswith("vm"):
        return "vm"
    return "unknown"

def get_current_ssid():
    try:
        r = subprocess.run(["iwgetid", "-r"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        return r.stdout.strip() or None
    except:
        return None

def load_profiles():
    if not os.path.exists(NETWORK_PROFILE_FILE):
        return {}
    with open(NETWORK_PROFILE_FILE) as f:
        return json.load(f)

def save_profiles(p):
    os.makedirs(os.path.dirname(NETWORK_PROFILE_FILE), exist_ok=True)
    with open(NETWORK_PROFILE_FILE, "w") as f:
        json.dump(p, f, indent=2)

def auto_vendor(iface):
    return random.choice(INTERFACE_VENDOR_MAP.get(detect_interface_type(iface), []))

def persistent_vendor(iface):
    ssid = get_current_ssid()
    profiles = load_profiles()

    if ssid and ssid in profiles:
        return profiles[ssid]

    v = auto_vendor(iface)
    if ssid and v:
        profiles[ssid] = v
        save_profiles(profiles)
    return v

# ===================== VENDOR MENU =====================

def vendor_menu(iface):
    print(f"\n{BOLD}{CYAN}MAC Vendor Mode:{RESET}")
    print(f"{BOLD}1){RESET} Auto (interface + network based) [Recommended]")
    print(f"{BOLD}2){RESET} Manual vendor selection")
    print(f"{BOLD}3){RESET} Custom OUI")
    print(f"{BOLD}4){RESET} Fully random")

    choice = prompt("Select option [1-4]:")

    if choice == "1":
        return persistent_vendor(iface), None

    if choice == "2":
        vendors = list(VENDOR_OUIS.keys())
        print(f"\n{BOLD}{CYAN}Available Vendors:{RESET}")
        for i, v in enumerate(vendors, 1):
            print(f"{BOLD}{i}){RESET} {v}")

        try:
            idx = int(prompt("Choose vendor number:")) - 1
            return vendors[idx], None
        except (ValueError, IndexError):
            print("[-] Invalid selection, falling back to AUTO mode")
            return persistent_vendor(iface), None

    if choice == "3":
        prefix = prompt("Enter OUI (e.g. 00:11:22):").strip()
        return None, prefix

    return None, None


# ===================== MAC + FINGERPRINT =====================

def random_mac(vendor=None, prefix=None):
    if vendor:
        prefix = random.choice(VENDOR_OUIS[vendor])

    if prefix:
        p = prefix.split(":")
        while len(p) < 3:
            p.append(f"{random.randint(0,255):02x}")
        first = p[:3]
    else:
        first_byte = (random.randint(0,255) & 0b11111100) | 0b00000010
        first = [f"{first_byte:02x}", f"{random.randint(0,255):02x}", f"{random.randint(0,255):02x}"]

    last = [f"{random.randint(0,255):02x}" for _ in range(3)]
    return ":".join(first + last)

def apply_fingerprint(vendor, dry=False):
    if not vendor:
        return
    hostname = random.choice(HOSTNAME_PROFILES.get(vendor, ["linux-host"]))
    ttl = TTL_PROFILES.get(vendor, 64)

    if dry:
        print(f"[DRY] hostname → {hostname}")
        print(f"[DRY] TTL → {ttl}")
        return

    subprocess.run(["hostnamectl", "set-hostname", hostname])
    subprocess.run(["sysctl", "-w", f"net.ipv4.ip_default_ttl={ttl}"], stdout=subprocess.DEVNULL)

# ===================== BELIEVABILITY =====================

def believability(iface, vendor, mac):
    score = 0
    if vendor in INTERFACE_VENDOR_MAP.get(detect_interface_type(iface), []):
        score += 30
    if vendor and mac[:8] in VENDOR_OUIS.get(vendor, []):
        score += 20
    if vendor:
        ttl = int(subprocess.run(["sysctl", "-n", "net.ipv4.ip_default_ttl"],
                  stdout=subprocess.PIPE, text=True).stdout.strip())
        if ttl == TTL_PROFILES.get(vendor, 64):
            score += 20
    if vendor:
        hn = subprocess.run(["hostname"], stdout=subprocess.PIPE, text=True).stdout.strip().lower()
        if any(h.lower() in hn for h in HOSTNAME_PROFILES.get(vendor, [])):
            score += 20
    if get_current_ssid() in load_profiles():
        score += 10
    return score

# ===================== CORE =====================

class MacChanger:
    def __init__(self, iface, tool, dry=False, log=None):
        self.iface = iface
        self.tool = tool
        self.dry = dry
        self.log_file = log
        self.original = self.current_mac()
        self.restored = False

    def log(self, m):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {m}"
        print(line)
        if self.log_file:
            with open(self.log_file, "a") as f:
                f.write(line + "\n")

    def current_mac(self):
        r = subprocess.run(["ip", "link", "show", self.iface], stdout=subprocess.PIPE, text=True)
        m = re.search(r"link/ether\s+([0-9a-f:]{17})", r.stdout)
        return m.group(1) if m else None

    def set_mac(self, mac):
        cmds = (
            [["ip","link","set",self.iface,"down"],
             ["ip","link","set",self.iface,"address",mac],
             ["ip","link","set",self.iface,"up"]]
            if self.tool == "ip"
            else
            [["ifconfig",self.iface,"down"],
             ["ifconfig",self.iface,"ether",mac],
             ["ifconfig",self.iface,"up"]]
        )
        for c in cmds:
            run(c, self.dry)
        time.sleep(DHCP_SETTLE_DELAY)

    def restore(self):
        if not self.restored and self.original:
            self.log(f"Restoring MAC → {self.original}")
            self.set_mac(self.original)
            self.restored = True

# ===================== SIGNAL =====================

changer = None
restore_on_exit = True

def exit_safe(*_):
    print("\n[!] Exiting safely")
    if restore_on_exit and changer:
        changer.restore()
    sys.exit(0)

signal.signal(signal.SIGINT, exit_safe)
signal.signal(signal.SIGTERM, exit_safe)

# ===================== MAIN =====================
require_root()

print_banner()
print("\n====== Auto MAC Identity Engine | CRUSVEDER ======\n")

iface = prompt("Interface:").strip()
if not iface_exists(iface):
    sys.exit("[-] Interface not found")

# ---- Safe numeric inputs ----
try:
    interval = int(prompt("Interval seconds [60]:") or 60)
except ValueError:
    interval = 60

try:
    count = int(prompt("Change count (0=∞):") or 0)
except ValueError:
    count = 0

dry = prompt("Dry-run? (y/n):").lower() == "y"
restore_on_exit = prompt("Restore on exit? (y/n):").lower() == "y"
logf = prompt("Log file (optional):").strip() or None

tool = detect_tool()
changer = MacChanger(iface, tool, dry, logf)

vendor, custom_prefix = vendor_menu(iface)
changer.log(f"Vendor profile → {vendor}")

i = 0
try:
    while True:
        i += 1
        if count and i > count:
            break
        mac = random_mac(vendor, custom_prefix)
        changer.log(f"[{i}] MAC → {mac}")
        changer.set_mac(mac)
        apply_fingerprint(vendor, dry)
        s = believability(iface, vendor, mac)
        changer.log(f"Believability score → {s}/100")
        time.sleep(interval)
finally:
    exit_safe()
