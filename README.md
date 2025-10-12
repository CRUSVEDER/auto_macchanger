#  Auto MAC Changer

An **advanced and interactive MAC address rotation tool** built in Python.  
It allows you to **automatically randomize** your network interface's MAC address at fixed time intervals — with options for restoring the original MAC, logging activity, and using vendor-style prefixes (OUI).

---

##  Features

- Interactive CLI (asks step-by-step inputs — no command-line flags needed)  
- Random MAC address generation at user-specified intervals  
- Option to restore your original MAC on exit  
- Countdown display between rotations  
- Supports **`ip`** and **`ifconfig`** (Linux/macOS)  
- Optional **log file** to record all MAC changes  
- Safe exit with cleanup (Ctrl + C supported)  
- Works for both Ethernet (`eth0`) and Wireless (`wlan0`) interfaces  
- Dry-run mode to simulate commands without making changes  

---

##  Requirements

- Python **3.6+**
- Root or sudo privileges  
- Either of the following installed on your system:
  - `ip` (recommended)  
  - or `ifconfig`  

---

##  Installation

1. Clone or download this repository:
   ```bash
   git clone https://github.com/<your-username>/auto-macchanger.git
   cd auto-macchanger

2. Make the script executable:

chmod +x auto_macchanger.py


3. Run the script with sudo (required to change MAC addresses):

sudo ./auto_macchanger.py




---

## Usage

When you run the script, it will guide you interactively:

==========  Auto MAC Changer ==========

Interface name (e.g., wlan0, eth0): wlan0
Change interval in seconds (e.g., 60): 120
How many times to change? (0 = infinite): 5
OUI/prefix (optional, e.g., 02:11:22):
Dry-run mode? (y/n): n
Restore original MAC on exit? (y/n): y
Show countdown timer? (y/n): y
Log file path (optional, e.g., mac_log.txt): maclog.txt

Example Output:

[2025-10-12 18:41:23] Original MAC: 74:d4:35:xx:xx:xx
[2025-10-12 18:41:23] [1] Generated random MAC: 02:12:34:ab:cd:ef
[2025-10-12 18:41:23] Setting MAC: 02:12:34:ab:cd:ef
[2025-10-12 18:41:23] MAC successfully changed to 02:12:34:ab:cd:ef
Next change in 120s...


---

## Options (Prompts Explained)

Prompt	Description

Interface name	Your network device (e.g., eth0, wlan0)
Change interval	How many seconds between each MAC change
Count	Number of times to change (0 = infinite)
OUI/prefix	Optional vendor-like prefix (e.g., 02:11:22)
Dry-run mode	Only shows commands without executing them
Restore on exit	Restores your original MAC when you quit
Show countdown	Displays timer until next change
Log file path	Saves all actions into a log file



---

## Example Scenarios

1. Random MAC every 60s indefinitely:

Interface: wlan0
Interval: 60
Count: 0
Restore: yes

2. 5 rotations every 30s with vendor prefix:

Interface: eth0
Interval: 30
Count: 5
Prefix: 02:11:22

3. Dry-run (test without applying changes):

Dry-run mode: yes


---

## Safe Exit

You can stop the tool anytime with:

Ctrl + C

If restore on exit is enabled, your original MAC address will automatically be restored.


---

## Logging Example

When you specify a log file (e.g., mac_log.txt), all actions are stored like:

[2025-10-12 19:01:42] Original MAC: 84:7a:88:de:45:32
[2025-10-12 19:01:42] [1] Generated random MAC: 02:12:34:56:78:9a
[2025-10-12 19:03:42] MAC successfully changed to 02:12:34:56:78:9a


---

## Disclaimer

This tool is provided for educational and privacy-testing purposes only.
Do not use it to interfere with or impersonate network devices you don’t own or control.
Use responsibly within your own network or in authorized pentesting environments.


---

## Author

Crusveder 
Cybersecurity & Forensics Enthusiast
GitHub Profile
https://github.com/CRUSVEDER

---

## Example command to start directly

sudo python3 auto_macchanger.py

 Stay private, stay rotating!

