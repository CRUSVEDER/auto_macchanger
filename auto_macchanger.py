#!/usr/bin/env python3

#An advanced and interactive MAC address rotation tool
#by github.com/CRUSVEDER

import subprocess
import random
import re
import shutil
import time
import signal
import sys
from datetime import datetime
from pathlib import Path

# -------------------- Helper Functions --------------------

def normalize_mac(mac: str) -> str:
    """Normalize MAC address format (xx:xx:xx:xx:xx:xx)."""
    mac = mac.strip().lower().replace("-", ":")
    parts = mac.split(":")
    if len(parts) != 6:
        raise ValueError("Invalid MAC address format.")
    return ":".join(p.zfill(2) for p in parts)

def random_mac(prefix=None):
    """Generate a random, locally administered MAC address."""
    if prefix:
        prefix = prefix.strip().lower().replace("-", ":")
        parts = prefix.split(":")
        if len(parts) not in (1, 2, 3):
            raise ValueError("Prefix must be 1–3 bytes (e.g. 02, 02:11, 02:11:22).")
        while len(parts) < 3:
            parts.append("%02x" % random.randint(0, 255))
        first_three = parts[:3]
    else:
        first = random.randint(0, 255)
        first = (first & 0b11111100) | 0b00000010  # locally administered bit
        first_three = [f"{first:02x}", f"{random.randint(0,255):02x}", f"{random.randint(0,255):02x}"]
    last_three = [f"{random.randint(0,255):02x}" for _ in range(3)]
    return ":".join(first_three + last_three)

def detect_tool():
    if shutil.which("ip"):
        return "ip"
    elif shutil.which("ifconfig"):
        return "ifconfig"
    else:
        print("[-] No supported tool found ('ip' or 'ifconfig'). Exiting.")
        sys.exit(1)

def run(cmd, dry=False):
    if dry:
        print("[DRY-RUN]", " ".join(cmd))
        return
    subprocess.run(cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# -------------------- Main Class --------------------

class MacChanger:
    def __init__(self, iface, tool, dry=False, log_path=None):
        self.iface = iface
        self.tool = tool
        self.dry = dry
        self.log_path = log_path
        self.original_mac = self.get_current_mac()

    def log(self, msg):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {msg}"
        print(line)
        if self.log_path:
            with open(self.log_path, "a") as f:
                f.write(line + "\n")

    def get_current_mac(self):
        try:
            if self.tool == "ip":
                res = subprocess.run(["ip", "link", "show", self.iface], stdout=subprocess.PIPE, text=True)
                m = re.search(r"link/ether\s+([0-9a-fA-F:]{17})", res.stdout)
            else:
                res = subprocess.run(["ifconfig", self.iface], stdout=subprocess.PIPE, text=True)
                m = re.search(r"(?:ether|HWaddr)\s+([0-9a-fA-F:]{17})", res.stdout)
            return m.group(1).lower() if m else None
        except Exception as e:
            self.log(f"Error getting current MAC: {e}")
            return None

    def set_mac(self, mac):
        mac = normalize_mac(mac)
        self.log(f"Setting MAC: {mac}")
        if self.tool == "ip":
            run(["ip", "link", "set", self.iface, "down"], self.dry)
            run(["ip", "link", "set", self.iface, "address", mac], self.dry)
            run(["ip", "link", "set", self.iface, "up"], self.dry)
        else:
            run(["ifconfig", self.iface, "down"], self.dry)
            run(["ifconfig", self.iface, "ether", mac], self.dry)
            run(["ifconfig", self.iface, "up"], self.dry)
        self.log(f"MAC successfully changed to {mac}")

    def restore(self):
        if self.original_mac:
            self.log(f"Restoring original MAC: {self.original_mac}")
            self.set_mac(self.original_mac)
        else:
            self.log("No original MAC found.")

# -------------------- Signal Handling --------------------

def handle_exit(sig, frame):
    global changer
    print("\n[!] Exiting safely...")
    if restore_on_exit and changer:
        changer.restore()
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

# -------------------- Interactive Setup --------------------

print("==========  Auto MAC Changer ~by Crus ==========\n")

iface = input("Interface name (e.g., wlan0, eth0): ").strip()
interval = float(input("Change interval in seconds (e.g., 60): ").strip() or "60")
count = input("How many times to change? (0 = infinite): ").strip()
count = int(count) if count.isdigit() else 0
prefix = input("OUI/prefix (optional, e.g., 02:11:22): ").strip() or None
dry_mode = input("Dry-run mode? (y/n): ").strip().lower() == "y"
restore_on_exit = input("Restore original MAC on exit? (y/n): ").strip().lower() == "y"
show_countdown = input("Show countdown timer? (y/n): ").strip().lower() == "y"
log_file = input("Log file path (optional, e.g., mac_log.txt): ").strip() or None

tool = detect_tool()
changer = MacChanger(iface, tool, dry_mode, log_file)
changer.log(f"Original MAC: {changer.original_mac}")

# -------------------- MAC Rotation --------------------

i = 0
try:
    while True:
        i += 1
        if count and i > count:
            changer.log("Reached specified count. Stopping.")
            break

        new_mac = random_mac(prefix)
        changer.log(f"[{i}] Generated random MAC: {new_mac}")
        changer.set_mac(new_mac)

        # Countdown
        remaining = interval
        while remaining > 0:
            if show_countdown:
                print(f"\rNext change in {int(remaining)}s...", end="", flush=True)
            time.sleep(1)
            remaining -= 1
        if show_countdown:
            print("")

except KeyboardInterrupt:
    handle_exit(None, None)
finally:
    if restore_on_exit:
        changer.restore()
    changer.log("Program exited.")
