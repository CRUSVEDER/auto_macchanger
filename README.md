# Auto MAC Identity Engine

An **advanced and intelligent MAC address identity rotation tool** built in Python.  
Automatically randomizes your network interface's MAC address with **vendor profiling**, **believability scoring**, **IP tracking**, and **persistent network identity management**.

---

## Features

### Core Functionality
- **Interactive CLI** - Step-by-step guided setup (no command-line flags needed)
- **Smart MAC Rotation** - Automatic MAC address changes at fixed intervals
- **Vendor Profiling** - Choose from 7 vendor profiles (Apple, Intel, Samsung, Realtek, Raspberry Pi, VMware, VirtualBox)
- **Identity Fingerprinting** - Automatically sets matching hostname and TTL values
- **Believability Scoring** - Real-time scoring system (0-100) to evaluate identity realism
- **IP Address Tracking** - Logs IP addresses after each MAC change
- **Network Persistence** - Remembers vendor profiles per SSID for consistent identity

### Advanced Options
- **Auto-Select Mode** - Intelligently chooses vendor based on interface type and network
- **Fully Random Mode** - Generate completely random MAC addresses
- **Custom OUI** - Use your own vendor prefix (e.g., `00:11:22`)
- **Countdown Timer** - Visual timer showing seconds until next change
- **Activity Logging** - Save all changes, IPs, and scores to a log file
- **Dry-Run Mode** - Test without making actual changes
- **Safe Exit** - Automatically restores original MAC on exit (Ctrl+C supported)

### Compatibility
- Supports both `ip` and `ifconfig` tools
- Works on Ethernet (`eth0`, `en0`) and Wireless (`wlan0`, `wlp3s0`) interfaces
- Linux and macOS compatible

---

## Requirements

- **Python 3.6+**
- **Root/sudo privileges**
- One of the following installed:
  - `ip` (recommended, iproute2 package)
  - `ifconfig` (net-tools package)
- Optional: `iwgetid` for WiFi SSID detection

---

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/CRUSVEDER/auto_mac.git
   cd auto_mac
   ```

2. **Make the script executable:**
   ```bash
   chmod +x auto_mac.py
   ```

3. **Run with sudo:**
   ```bash
   sudo ./auto_mac.py
   ```

---

## Usage

### Interactive Setup

When you run the script, it will guide you through setup:

```
 █████╗ ██╗   ██╗████████╗ ██████╗     ███╗   ███╗ █████╗  ██████╗
██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗    ████╗ ████║██╔══██╗██╔════╝
███████║██║   ██║   ██║   ██║   ██║    ██╔████╔██║███████║██║     
██╔══██║██║   ██║   ██║   ██║   ██║    ██║╚██╔╝██║██╔══██║██║     
██║  ██║╚██████╔╝   ██║   ╚██████╔╝    ██║ ╚═╝ ██║██║  ██║╚██████╗
╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝     ╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝
        AUTO MAC IDENTITY ENGINE — CRUSVEDER

Interface name [e.g., wlan0, eth0]: eth0
Change interval in seconds [e.g., 60]: 60
How many times to change? [0 = infinite]: 0
Dry-run mode? [y/n]: n
Restore original MAC on exit? [y/n]: y
Log file path [optional, e.g., mac_log.txt]: mac_changes.log
Show countdown timer? [y/n]: y

MAC Vendor Mode:
1) Auto (interface + network based) [Recommended]
2) Manual vendor selection
3) Custom OUI
4) Fully random
Select option [1-4]: 1
```

### Example Output

```
[2026-02-04 14:47:22] Vendor profile → realtek
[2026-02-04 14:47:22] [1] MAC → 52:54:00:24:26:67
[2026-02-04 14:47:25] [1] IP  → 192.168.0.131
[2026-02-04 14:47:25] Believability score → 75/100
Next change in 60s...
```

---

## Vendor Modes Explained

### 1. Auto Mode (Recommended)
Intelligently selects vendor based on:
- Interface type (wlan → Apple/Samsung, eth → Intel/Realtek)
- Current WiFi network (SSID)
- Saves vendor preference per network for consistency

**Best for:** Maintaining persistent identity across reconnections

### 2. Manual Vendor Selection
Choose from available vendors:
- **Apple** - MacBook Pro/Air profiles
- **Intel** - ThinkPad/Dell laptop profiles
- **Samsung** - Galaxy device profiles
- **Realtek** - Common network adapters
- **Raspberry Pi** - IoT device profiles
- **VMware** - Virtual machine profiles
- **VirtualBox** - Virtual machine profiles

**Best for:** Impersonating specific device types

### 3. Custom OUI
Enter your own vendor prefix (e.g., `00:11:22`)

**Best for:** Advanced users with specific OUI requirements

### 4. Fully Random
Generates completely random MAC addresses

**Best for:** Maximum anonymity (lower believability scores)

---

## Believability Score Explained

AUTO MAC evaluates how realistic the identity looks:

| Check | Points |
|-------|--------|
| Vendor matches interface type | 20 |
| Valid vendor OUI | 20 |
| TTL matches vendor profile | 15 |
| Hostname matches vendor style | 15 |
| Persistent network identity | 10 |
| MAC quality (not sequential/broadcast) | 10 |
| IP acquisition success | 10 |
| **Total** | **100** |

**Score Ranges:**
- **85-95** - Perfect identity (vendor mode with persistence)
- **70-85** - Good identity (vendor mode)
- **55-70** - Decent identity (random mode or partial match)
- **30-55** - Weak identity (poor configuration)

---

## Configuration Options

| Prompt | Description | Example |
|--------|-------------|---------|
| **Interface name** | Your network device | `eth0`, `wlan0`, `en0` |
| **Change interval** | Seconds between MAC changes | `60`, `300`, `3600` |
| **Count** | Number of rotations (0 = infinite) | `0`, `5`, `10` |
| **Dry-run mode** | Test without applying changes | `y` or `n` |
| **Restore on exit** | Restore original MAC when quitting | `y` or `n` |
| **Log file path** | Save activity to file | `mac_log.txt` or empty |
| **Show countdown** | Display timer between changes | `y` or `n` |
| **Vendor mode** | Identity selection method | `1-4` |

---

## Logging Example

When you specify a log file, all activity is recorded:

```
[2026-02-04 14:47:22] Vendor profile → realtek
[2026-02-04 14:47:22] [1] MAC → 52:54:00:24:26:67
[2026-02-04 14:47:25] [1] IP  → 192.168.0.131
[2026-02-04 14:47:25] Believability score → 75/100
[2026-02-04 14:48:22] [2] MAC → 00:e0:4c:64:b6:78
[2026-02-04 14:48:25] [2] IP  → 192.168.0.152
[2026-02-04 14:48:25] Believability score → 75/100
[2026-02-04 14:49:15] Restoring MAC → 00:e0:4c:0b:e9:67
```

---

## Example Scenarios

### Scenario 1: Stealth Browsing (Auto Mode)
```
Interface: wlan0
Interval: 300 (5 minutes)
Count: 0 (infinite)
Vendor Mode: 1 (Auto)
Restore: yes
Score: 80-90/100
```
**Use case:** Browse anonymously with consistent identity per network

### Scenario 2: Penetration Testing (Manual Vendor)
```
Interface: eth0
Interval: 60
Count: 10
Vendor Mode: 2 (Manual → Intel)
Restore: yes
Log: pentest_session.log
Score: 70-85/100
```
**Use case:** Test network access controls with different device types

### Scenario 3: Maximum Anonymity (Random Mode)
```
Interface: wlan0
Interval: 120
Count: 0
Vendor Mode: 4 (Fully random)
Restore: yes
Score: 55-70/100
```
**Use case:** Maximum MAC randomization (trade-off: lower believability)

### Scenario 4: Custom OUI Testing
```
Interface: eth0
Interval: 180
Count: 5
Vendor Mode: 3 (Custom OUI: 00:11:22)
Restore: yes
Score: Varies
```
**Use case:** Test with specific vendor prefix

---

## Safe Exit

Stop the tool anytime with **Ctrl+C**

If **restore on exit** is enabled, your original MAC will automatically be restored:
```
^C
[!] Exiting safely
[2026-02-04 15:30:45] Restoring MAC → 00:e0:4c:0b:e9:67
```

---

## Persistent Network Profiles

The tool saves vendor preferences per WiFi network in:
```
/var/lib/mac_identity_profiles.json
```

Example:
```json
{
  "HomeWiFi": "apple",
  "OfficeNetwork": "intel",
  "CafeGuest": "samsung"
}
```

This ensures **consistent identity** when reconnecting to known networks.

---

## Technical Details

### MAC Address Format
- First 3 octets: OUI (vendor prefix)
- Last 3 octets: Random
- Locally administered bit set (bit 1 of first byte)
- Unicast address (bit 0 of first byte = 0)

### Fingerprint Spoofing
The tool modifies system fingerprints to match vendor profiles:
- **Hostname**: Changed to match vendor style (e.g., `MacBook-Pro`, `ThinkPad`)
- **TTL**: Adjusted to match vendor profile (64 for most, 128 for VMs)

### Supported Interfaces
- **Wireless**: `wlan0`, `wlan1`, `wlp3s0`, `wlp2s0b1`
- **Ethernet**: `eth0`, `eth1`, `en0`, `enp3s0`
- **Virtual**: `vmnet0`, `vboxnet0`

---

## Disclaimer

This tool is provided for **educational and privacy-testing purposes only**.

- Use in your own network or authorized testing environments
- Test network security and privacy configurations
- Learn about MAC address spoofing and network identity
- Do NOT use to interfere with networks you don't own
- Do NOT use to impersonate other devices maliciously
- Do NOT use for illegal activities

**Use responsibly and ethically.**

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

Areas for improvement:
- Additional vendor profiles
- More sophisticated scoring algorithms
- IPv6 support
- GUI interface
- Network traffic analysis integration

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## Author

**CRUSVEDER**  
GitHub: [@CRUSVEDER](https://github.com/CRUSVEDER)

---

## Quick Start Command

```bash
sudo python3 auto_macchanger.py
```

---


## Support

If you encounter any issues or have questions:
1. Check the [Issues](https://github.com/CRUSVEDER/auto_macchanger/issues) page
2. Create a new issue with detailed information
3. Include your OS, Python version, and error messages

---

## Star History

If you find this tool useful, please consider giving it a star on GitHub!

---

**Stay private, stay rotating!**
