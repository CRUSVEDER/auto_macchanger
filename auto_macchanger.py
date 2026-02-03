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
        print(f"{RED}[!] Run as root{RESET}")
        sys.exit(1)

def iface_exists(iface):
    return os.path.exists(f"/sys/class/net/{iface}")

def detect_tool():
    if shutil.which("ip"):
        return "ip"
    if shutil.which("ifconfig"):
        return "ifconfig"
    sys.exit("[!] ip/ifconfig not found")

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
# VENDOR SELECTION
# ============================================================

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

# ============================================================
# BELIEVABILITY SCORING
# ============================================================

def believability_score(iface, vendor, mac):
    """Calculate how realistic the MAC identity appears (balanced scoring)"""
    score = 0
    
    # Check 1: Vendor matches interface type (20 points)
    iface_type_detected = iface_type(iface)
    if vendor and vendor in INTERFACE_VENDOR_MAP.get(iface_type_detected, []):
        score += 20
    elif vendor and iface_type_detected == "unknown":
        score += 8  # Partial credit for unknown interface types
    elif not vendor:
        # Random MAC gets base credit if properly formatted
        try:
            first_byte = int(mac.split(':')[0], 16)
            if (first_byte & 0b00000001) == 0:  # Unicast
                score += 10
        except:
            pass
    
    # Check 2: Valid vendor OUI prefix (20 points)
    if vendor:
        mac_prefix = mac[:8].lower()
        vendor_prefixes = [p.lower() for p in VENDOR_OUIS.get(vendor, [])]
        if mac_prefix in vendor_prefixes:
            score += 20
        else:
            # Check if at least the first 3 octets match any vendor OUI
            for prefix in vendor_prefixes:
                if mac_prefix.startswith(prefix[:5]):
                    score += 8  # Partial match
                    break
    else:
        # Random MAC: check if it's properly formatted
        try:
            first_byte = int(mac.split(':')[0], 16)
            # Locally administered bit set (bit 1 of first byte)
            if (first_byte & 0b00000010) != 0:
                score += 15  # Good random MAC
            else:
                score += 8   # Looks like manufacturer MAC
        except:
            pass
    
    # Check 3: TTL matches vendor profile (15 points)
    if vendor:
        try:
            ttl = int(subprocess.run(["sysctl", "-n", "net.ipv4.ip_default_ttl"],
                      stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True).stdout.strip())
            expected_ttl = TTL_PROFILES.get(vendor, 64)
            if ttl == expected_ttl:
                score += 15
            elif abs(ttl - expected_ttl) <= 1:
                score += 7  # Close enough
        except:
            pass
    else:
        # Random vendor: give credit if TTL is common (64 or 128)
        try:
            ttl = int(subprocess.run(["sysctl", "-n", "net.ipv4.ip_default_ttl"],
                      stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True).stdout.strip())
            if ttl in [64, 128, 255]:
                score += 12
            elif ttl in [32, 60, 63, 65]:
                score += 6
        except:
            pass
    
    # Check 4: Hostname matches vendor style (15 points)
    if vendor:
        try:
            hn = subprocess.run(["hostname"], stdout=subprocess.PIPE, 
                              stderr=subprocess.DEVNULL, text=True).stdout.strip().lower()
            expected_hostnames = [h.lower() for h in HOSTNAME_PROFILES.get(vendor, [])]
            
            # Full match
            if any(h in hn for h in expected_hostnames):
                score += 15
            # Partial match (contains vendor name)
            elif vendor.lower() in hn:
                score += 7
        except:
            pass
    else:
        # Random: check if hostname looks generic/normal
        try:
            hn = subprocess.run(["hostname"], stdout=subprocess.PIPE, 
                              stderr=subprocess.DEVNULL, text=True).stdout.strip().lower()
            # Generic hostnames are good for random MACs
            generic_patterns = ['linux', 'ubuntu', 'debian', 'user', 'host', 'pc', 'laptop', 'desktop']
            if any(pattern in hn for pattern in generic_patterns):
                score += 10
        except:
            pass
    
    # Check 5: Persistent network identity (10 points)
    ssid = current_ssid()
    profiles = load_profiles()
    if ssid and ssid in profiles:
        if profiles[ssid] == vendor:
            score += 10  # Perfect match
        elif vendor:
            score += 4   # Has profile but different vendor
    elif not vendor:
        # Random mode: no profile is actually good (less fingerprinting)
        score += 8
    
    # Check 6: MAC address quality (10 points)
    if mac:
        try:
            parts = mac.split(':')
            # Check for bad patterns
            is_sequential = all(int(parts[i], 16) == int(parts[i-1], 16) + 1 for i in range(1, len(parts)))
            is_same = len(set(parts)) == 1
            is_broadcast = mac.lower() == 'ff:ff:ff:ff:ff:ff'
            is_null = mac.lower() == '00:00:00:00:00:00'
            
            if not (is_sequential or is_same or is_broadcast or is_null):
                score += 10
            elif not (is_broadcast or is_null):
                score += 4  # Not great but not terrible
        except:
            pass
    
    # Check 7: IP address acquisition (10 points)
    # This will be checked in the main loop after getting IP
    # For now, assume it will work
    score += 10
    
    return min(score, 100)  # Cap at 100

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

    def get_ip_address(self):
        """Get current IP address of the interface"""
        try:
            r = subprocess.run(["ip", "addr", "show", self.iface],
                             stdout=subprocess.PIPE, text=True)
            # Match IPv4 address
            m = re.search(r"inet\s+(\d+\.\d+\.\d+\.\d+)", r.stdout)
            return m.group(1) if m else "No IP"
        except:
            return "No IP"

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
    
    # Basic configuration
    iface = prompt("Interface name [e.g., wlan0, eth0]:")
    if not iface_exists(iface):
        sys.exit(f"{RED}[!] Interface not found{RESET}")
    
    interval = int(prompt("Change interval in seconds [e.g., 60]:") or 60)
    count = int(prompt("How many times to change? [0 = infinite]:") or 0)
    dry = prompt("Dry-run mode? [y/n]:").lower() == "y"
    restore_on_exit = prompt("Restore original MAC on exit? [y/n]:").lower() == "y"
    logf = prompt("Log file path [optional, e.g., mac_log.txt]:") or None
    show_countdown = prompt("Show countdown timer? [y/n]:").lower() == "y"
    
    # Vendor selection
    vendor, custom_prefix = vendor_menu(iface)
    
    tool = detect_tool()
    changer = MACIdentityChanger(iface, tool, dry, logf)
    changer.log(f"Vendor profile → {vendor if vendor else 'Random'}")
    
    i = 0
    try:
        while True:
            i += 1
            if count and i > count:
                break
            mac = random_mac(vendor, custom_prefix)
            changer.log(f"[{i}] MAC → {mac}")
            changer.set_mac(mac)
            
            # Log IP address
            ip = changer.get_ip_address()
            changer.log(f"[{i}] IP  → {ip}")
            
            apply_fingerprint(vendor, dry)
            
            # Calculate and log believability score
            score = believability_score(iface, vendor, mac)
            changer.log(f"Believability score → {score}/100")
            
            if show_countdown:
                for remaining in range(interval, 0, -1):
                    sys.stdout.write(f"\r{CYAN}Next change in {remaining}s...{RESET}   ")
                    sys.stdout.flush()
                    time.sleep(1)
                print()  # New line after countdown
            else:
                time.sleep(interval)
    finally:
        safe_exit()

if __name__ == "__main__":
    main()
