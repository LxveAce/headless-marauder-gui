# Headless Marauder

**The all-in-one ESP32 Marauder controller and multi-firmware flasher.** Open source, cross-platform, one-click standalone exe — no Python, no browser, no cloud. Just download, run, and plug in your board.

> Works with any ESP32 running Marauder firmware — headless boards (like a Lonely Binary "Gold" with an antenna and no screen) or screened devices (CYD, M5Stack, Flipper devboards). The "Gold" and most headless dev boards are **classic ESP32** (WROOM, CH340 USB-serial), not S3. A full-featured GUI for controlling and flashing ESP32 Marauder from a Raspberry Pi, laptop, or cyberdeck.

**Runs on:** Linux (Kali, Debian, Ubuntu, Arch, Fedora), Windows 10/11, macOS (Apple Silicon), Raspberry Pi (ARM64)

---

## What sets this apart

Most Marauder UIs are browser-based and depend on the Web Serial API (Chromium only). On Kali that means Firefox doesn't work at all, and even in Chrome the feature set is limited.

Headless Marauder is different:

- **All-in-one** — controller AND flasher in a single app. Connect, scan, attack, flash firmware, flash a suicide build — all without switching tools. No separate esptool workflow, no Arduino IDE, no web flasher.
- **One-click exe** — standalone binaries for Windows, Linux x64, Linux ARM64, and macOS (Apple Silicon). Everything is bundled (Python, PyQt5, all deps). Download, double-click, go. No install, no setup, no dependencies.
- **Open source** — MIT licensed, fully transparent. Read every line, fork it, modify it, contribute back.
- **Suicide build support** — the only Marauder controller with built-in support for flashing anti-forensic Suicide-Marauder bundles. Provision once, flash from the app with integrity verification. See [below](#suicide-build).
- **Community-driven** — built by and for the community, with many more features to come. PRs, ideas, and bug reports welcome.

---

## What it does

### Control

- **Four front-ends, one core** — PyQt5 desktop GUI (recommended), Tkinter GUI, Textual TUI for terminal/SSH, and a browser UI (Flask + WebSocket at localhost:5000). Dark theme across all of them.
- **The full Marauder command set** — 70 commands organized into categories as buttons and tree entries, with parameter forms and a raw command box. Auto-connect at 115200 baud, or specify `--port` and `--baud`.
- **Live AP/Station tables** — `scanap` fills the Access Points tab in real-time; APs and stations parsed and de-duplicated straight off the serial stream. Auto-list polls every 3 seconds to keep tables current during scans.
- **Target picker** — check the networks you want, select all, or type indices manually. Builds the right `select -a 0,2,5` from Marauder's real indices.
- **Hover tooltips** — every button, field, and checkbox has a plain-language tooltip explaining what it does. Shared glossary across all UIs.

### Full command coverage

Not just WiFi scanning and deauth — the catalog (`marauder_core/commands.py`) is the single source of truth that drives every front-end, organized into categories:

| Category | What's in it |
|----------|-------------|
| **WiFi · Scan** | AP scan, station scan, scan-all, signal monitor, packet count, MAC track, GPS wardrive |
| **WiFi · Sniff** | Raw, beacon, probe, deauth (detect), ESP, Pwnagotchi, and PMKID/EAPOL capture (SavePCAP to SD) |
| **WiFi · Attack** | Deauth (selected APs / selected clients), beacon spam (list / random / clone), probe flood, rickroll beacon, bad-msg, evil portal, karma |
| **WiFi · Network** | Join a scanned AP, ping scan the local network, TCP port scan (with all-ports option) |
| **Bluetooth** | BLE scan (AirTag / Flipper / Flock filters), BT wardrive, skimmer detection, AirTag spoof, and BLE spam (Sour Apple, AppleJuice, Google, Samsung, Windows/Swiftpair, Flipper, All) |
| **GPS** | Live GPS readout, raw NMEA stream, and per-field queries (fix, sats, lat/lon, altitude, date, accuracy) |
| **Lists & Targets** | Select/clear APs, stations, and SSIDs; list APs/clients/SSIDs/targets; select-by-filter; device info |
| **SSID** | Add a named SSID, generate N random SSIDs, remove by index |
| **Channel** | Show / set the active WiFi channel |
| **Files** | SD-card directory listing, save/load AP and SSID lists to SD |
| **System** | Settings toggles, LED color/rainbow, OTA updates (serial + WiFi), reboot, device help, stopscan |

### Flasher

- **Multi-firmware flasher** — flash [ESP32 Marauder](https://github.com/justcallmekoko/ESP32Marauder) (default), [ESP32-DIV](https://github.com/cifertech/esp32-div), [Bruce](https://github.com/pr3y/Bruce), or any custom local `.bin`. A pluggable `FirmwareProfile` registry drives the detect/release/variant logic per firmware, and the **Firmware** selector switches profiles and UI dynamically.
- **Auto chip detection** — identifies classic ESP32, ESP32-S2, ESP32-S3, ESP32-C2/C3/C5/C6, and ESP32-H2 via esptool, then auto-selects the matching firmware variant.
- **App-only or full flash** — update an existing board (app image only) or flash a blank board from scratch (bootloader + partitions + boot_app0 + app, with the right per-chip offsets).
- **Erase flash** — full chip erase for a clean slate.
- **Suicide build flashing** — one-click flash of pre-provisioned anti-forensic Marauder bundles with SHA256 integrity verification. Flash-only; it never burns eFuses. See [below](#suicide-build).
- **Security hardened** — HTTPS-only firmware fetching with a GitHub host allowlist, path-traversal protection on all downloads, and SSRF/redirect defense (redirects are followed only to allowlisted hosts).

### Logging & data export

- **Raw serial log** — full serial stream to `serial-YYYYMMDD-HHMMSS.log`, `tail -f` friendly.
- **Live JSON snapshot** — `latest.json` updated every ~3.5 seconds with AP/station counts, full arrays, timestamps, and session metadata. Atomic writes so other tools can poll it safely.
- **CSV export** — `aps.csv` (SSID, channel, RSSI, BSSID) and `stations.csv` (MAC, AP BSSID, RSSI) for spreadsheets, scripts, or feeding into other tools.

### Everything else

- **`--mock` mode** — run the full UI without hardware for demo, dev, or testing.
- **Built-in guide** — in-app Guide tab covers attack chaining and feeding data into Wireshark, hashcat, WiGLE, Kismet, etc.
- **Self-update** — Help > Check for Updates pulls the latest code and reinstalls deps (source installs).
- **Installable** — adds to your PATH, app menu (Linux), Start Menu (Windows). Run from anywhere.

---

## Suicide build

The suicide build is an **anti-forensic firmware option for ESP32 Marauder** — a defensive measure that protects the data on your own device if it's lost, stolen, or seized.

### What it means

A "suicide build" is a specially provisioned Marauder firmware image that adds hardware-level protection to your ESP32:

- **Boot password** — the board requires a password before it boots into Marauder. Without the password, the firmware doesn't run.
- **2-fail wipe** — after 2 failed password attempts, the device automatically wipes itself. Flash, NVS, everything — gone.
- **GPIO dead-man switch** — a hardware kill trigger tied to a GPIO pin. Wire a physical button or switch; pull the pin and the board wipes instantly. Useful as a panic button or a tamper-detection trigger (e.g. open-case detection on a cyberdeck).

This is enforced at the bootloader level with eFuse locks and flash encryption — it can't be bypassed by re-flashing or reading the chip externally. Once provisioned, the protections are permanent and hardware-enforced.

### How it works (two-step process)

The suicide build is a **two-repo workflow**:

1. **Provision the bundle** (separate repo) — use the **[Suicide-Marauder](https://github.com/LxveAce/Suicide-Marauder)** provisioner to build a firmware bundle. That tool handles the sensitive parts: password hashing, eFuse configuration, secure boot setup, and flash encryption. It outputs a `bundle.json` manifest + `.bin` image files in a bundle directory.

2. **Flash the bundle** (this app) — in the Headless Marauder flasher:
   - Set the **Firmware** selector to **ESP32 Marauder**
   - Check the **Suicide** checkbox
   - Point it at your bundle directory (the folder with `bundle.json` + the `.bin` files)
   - **Detect chip** → **FLASH**

That's it. The app reads the bundle manifest, verifies the SHA256 hash of every image file against what the provisioner recorded, stages verified copies to a private temp directory (TOCTOU protection), and writes everything in a single esptool call.

### What this app does and doesn't do

**This app ONLY flashes an already-provisioned bundle.** It never burns eFuses, never hashes passwords, never touches secure boot or flash encryption config — all of that happens in the Suicide-Marauder provisioner, never here.

**Integrity is enforced before anything is flashed:**
- Every file in the bundle is SHA256-verified against the manifest
- A missing or empty hash on a suicide bundle is a **hard error** — no flashing without verification
- Path-traversal protection rejects any manifest entry that tries to reference files outside the bundle directory
- Verified files are staged to a private temp directory and re-hashed before flashing (defense against files being swapped between verification and flash)

**Plain Marauder is always the default.** Leave the Suicide checkbox unchecked and the flasher works exactly like a normal firmware update. The suicide path is entirely opt-in.

> **Read the Suicide-Marauder repo's [SAFETY.md](https://github.com/LxveAce/Suicide-Marauder/blob/main/docs/SAFETY.md) before enabling this.** The 2-fail wipe is real. Test in safe mode first. This is a defensive, owner-only measure for protecting your own hardware — not an attack tool.

---

## Install

### Download (easiest)

Grab a pre-built binary from the [latest release](https://github.com/LxveAce/headless-marauder-gui/releases/latest) — no Python or Git needed:

| Platform | File | Notes |
|----------|------|-------|
| Windows x64 | `headless-marauder-vX.X.X-windows-x64.exe` | Double-click to run |
| Linux x64 | `headless-marauder-vX.X.X-linux-x64` | `chmod +x` then run |
| Linux ARM64 | `headless-marauder-vX.X.X-linux-arm64` | Raspberry Pi (64-bit OS), ARM SBCs |
| macOS arm64 | `headless-marauder-vX.X.X-macos-arm64` | Apple Silicon (M-series) |

Everything's bundled — Python, PyQt5, all dependencies. Download, run, plug in your ESP32. (Replace `vX.X.X` with the latest version on the Releases page.)

> The standalone builds include the Qt GUI only. For the TUI, browser UI, or dev work, install from source. Updates require downloading the new release (no in-app updater in standalone mode).
>
> **Pi users:** ARM64 build needs a 64-bit OS (Pi OS 64-bit, Kali ARM 64-bit, Ubuntu ARM). On 32-bit, install from source instead.

### From source

#### Linux (Kali / Debian / Ubuntu)

```bash
git clone https://github.com/LxveAce/headless-marauder-gui.git
cd headless-marauder-gui
./install.sh
```

Sets up a venv, installs everything, and gives you `headless-marauder` (Qt GUI), `headless-marauder-tui` (terminal), and `headless-marauder-web` (browser) in `~/.local/bin`, plus a menu entry.

Serial access without sudo (re-login after):
```bash
sudo usermod -aG dialout $USER
```

#### Windows

You'll need [Python 3.9+](https://python.org) (check "Add Python to PATH") and [Git](https://git-scm.com/downloads).

```
git clone https://github.com/LxveAce/headless-marauder-gui.git
cd headless-marauder-gui
install.bat
```

Gives you `headless-marauder`, `headless-marauder-tk`, `headless-marauder-tui`, and `headless-marauder-web` commands, plus a Start Menu shortcut.

> Open a new terminal after install so PATH takes effect.

**CH340 driver:** If Windows doesn't see your ESP32, grab the [CH340 driver](https://www.wch-ic.com/downloads/CH341SER_EXE.html). Board shows up as a COM port (e.g. `COM3`).

#### macOS / Other

```bash
git clone https://github.com/LxveAce/headless-marauder-gui.git
cd headless-marauder-gui
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install PyQt5
```

Then run:
```bash
source .venv/bin/activate
python3 gui_qt/app.py           # Qt GUI
python3 gui/app.py              # Tkinter
python3 tui/app.py              # Terminal
```

Add `--mock` to try it without hardware, `--port /dev/tty.usbserial-xxxx` to specify a port.

#### pip install

```bash
pip install git+https://github.com/LxveAce/headless-marauder-gui.git[all]
```

Gets you `headless-marauder-tk`, `headless-marauder-tui`, and `headless-marauder-web`. The Qt GUI needs to be run from a clone (`python -m gui_qt.app`) since Qt entry points can be finicky with pip.

<details>
<summary>Manual / dev run</summary>

```bash
# Linux
sudo apt install -y python3-venv python3-tk python3-pyqt5
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 gui_qt/app.py

# Windows
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install PyQt5
python gui_qt\app.py
```

Flags: `--mock` (no hardware), `--port COM3` or `--port /dev/ttyUSB0` (skip autodetect), `--baud 115200` (custom baud rate), `--no-autoconnect` (don't connect on launch), `--log` (start recording immediately).

For the browser UI: `--host 0.0.0.0` (LAN access), `--web-port 8080` (custom port).
</details>

---

## Updating

`git pull` in the project folder. Settings and logs are untouched.

The easiest way: **Help > Check for Updates** in the app — it pulls and reinstalls deps automatically.

From the terminal:
```bash
cd headless-marauder-gui
git pull
# Linux: re-run ./install.sh if deps changed
# Windows: .venv\Scripts\pip.exe install -q -r requirements.txt
```

---

## Uninstall

**Linux:**
```bash
cd headless-marauder-gui
./uninstall.sh          # removes launchers + menu entry
rm -rf ../headless-marauder-gui
```

**Windows:**
```
cd headless-marauder-gui
uninstall.bat           # removes launchers + Start Menu shortcut
```
Then delete the `headless-marauder-gui` folder.

---

## Using it

1. **Connect** — auto-detects the board (115200 baud). Top bar turns green.
2. **Scan APs** — with auto-list on (default), the Access Points tab fills while scanning.
3. **STOP** when you've seen enough.
4. **Select APs** — tick networks in the picker, it sends `select -a ...`.
5. Run an action — e.g. Deauth (selected APs).

### Browser UI

Run `headless-marauder-web` (or `python web/app.py`) and open **http://localhost:5000**. Same features as the desktop GUIs — command sidebar, live console, AP/Station tables, parameter forms, auto-list, logging, the firmware flash panel (multi-firmware + Suicide build), and keyboard shortcuts (`Ctrl+L` clear, `Ctrl+K` command box, `Ctrl+.` STOP). Raw input supports arrow-key history.

Binds to localhost only by default. Pass `--host 0.0.0.0` to open it up to your LAN (no auth — anyone on the network can control the board).

### Keyboard shortcuts (Qt GUI)

| Shortcut | Action |
|----------|--------|
| `Ctrl+L` | Clear console |
| `F5` | Refresh ports |
| `Ctrl+K` | Focus command box |
| `Ctrl+.` | STOP |
| `Ctrl+U` | Check for updates |
| `Ctrl+Q` | Quit |
| `F1` | Open Guide |

### Flashing firmware

1. Click **Flash Firmware**
2. Pick the **Firmware** — ESP32 Marauder (default), ESP32-DIV, Bruce, or Custom
3. **Detect chip** — figures out if it's a classic ESP32, S3, etc.
4. **Load release list** — pulls from the firmware's official GitHub (or choose your local `.bin` for Custom)
5. Pick a variant (auto-selected based on your chip)
6. **Update app only** (existing board) or **Full flash** (blank board)
7. **FLASH** — progress streams in real-time

For suicide builds, see the [Suicide build](#suicide-build) section above.

### Logging

Toggle **Log** in the toolbar (or File > Set Log Folder, or `--log` at launch). Default: `~/marauder-logs`.

| File | What's in it |
|------|-------------|
| `serial-YYYYMMDD-HHMMSS.log` | Raw serial stream (`tail -f` friendly) |
| `latest.json` | Live snapshot (~3.5s intervals): AP/station counts, full arrays, timestamps. Atomic writes so other tools can poll safely. |
| `aps.csv` | Parsed APs (SSID, channel, RSSI, BSSID) |
| `stations.csv` | Parsed stations (MAC, AP BSSID, RSSI) |

All outputs are designed for piping into other tools — Wireshark, hashcat, WiGLE, Kismet, custom scripts. See the in-app Guide for chaining examples.

---

## Troubleshooting

**Linux:**
- **No `/dev/ttyUSB0`** — The Gold uses a CH340. On Kali, `brltty` likes to steal it: `sudo apt remove brltty`, replug. Make sure you're in `dialout`.
- **In a VM** — Pass the USB device through (VirtualBox: Devices > USB; VMware: VM > Removable Devices).
- **Qt GUI won't start** — PyQt5 missing. `sudo apt install -y python3-pyqt5` (venv needs `--system-site-packages`), or just use the TUI.

**Windows:**
- **No COM port** — Install the [CH340 driver](https://www.wch-ic.com/downloads/CH341SER_EXE.html). Check Device Manager > Ports.
- **`headless-marauder` not recognized** — Open a new terminal (PATH was just updated).
- **Permission denied on COM port** — Close any other serial monitor (Arduino IDE, PuTTY, etc.).

**General:**
- **Board boot-loops / `scanap` does nothing** — Check the console output:
  - `invalid header: 0xffffffff` — flash is blank, use Full flash.
  - `Detected size(4096k) smaller than ... header(16384k)` — wrong flash size header. The flasher fixes this with `--flash_size detect`; erase and re-flash.
- **Deauth "does nothing"** — Marauder prints the start message once then runs silently. If a device doesn't drop, it's usually 802.11w/PMF (modern routers ignore deauth), a 5GHz target (classic ESP32 is 2.4GHz only), or no clients connected.

---

## Architecture

```
marauder_core/   controller.py  parsing.py  commands.py  flasher.py  capture.py  updater.py  uihelp.py
gui_qt/app.py    PyQt5 GUI (live tables, picker, flasher, logging)
gui/app.py       Tkinter GUI (simple, stdlib)
tui/app.py       Textual terminal UI
web/app.py       Browser UI (Flask + SocketIO at localhost:5000)
build.py         PyInstaller build script for standalone exes
install.sh       Linux installer (app menu + PATH + venv)
install.bat      Windows installer (Start Menu + PATH + venv)
```

One command catalog and one parser feed all four front-ends. The serial layer streams to the UI, the parser, and the logger at the same time. The `FirmwareProfile` registry in `flasher.py` keeps the Marauder and suicide flows byte-for-byte intact while adding the ESP32-DIV, Bruce, and custom profiles on top.

---

## Universal Flasher

This tool's pluggable `FirmwareProfile` architecture was expanded into the **[Universal Flasher](https://github.com/LxveAce/universal-flasher)** — a multi-firmware flasher and device manager supporting 14+ firmware types across 4 flash backends:

| Flash Backend | Devices |
|---------------|---------|
| **esptool** | Marauder, GhostESP, Bruce, HaleHound, ESP32-DIV, Meshtastic, Flock-You, OUI-Spy, Sky-Spy, AirTag Scanner, CYT-NG |
| **SD image writer** | Pwnagotchi, RaspyJack, Kali ARM |
| **ADB** | RayHunter (Orbic RC400L) |
| **qFlipper** | Flipper Zero (Momentum, Unleashed) |

Also includes batch flash, firmware backup/restore, device auto-detection, offline cache, flash history, update checker, health check, and a plugin system. **[github.com/LxveAce/universal-flasher](https://github.com/LxveAce/universal-flasher)**

---

## Legal

**For authorized security testing only.** Use on networks and devices you own or have written permission to test. WiFi deauth, evil portals, BLE spam — these can be illegal against other people's stuff (CFAA, FCC rules, etc.). You are responsible for how you use this tool.

The **ESP32-DIV** and **Bruce** firmwares (optional flash targets) include **RF features that may be illegal to operate** in your jurisdiction. This app only flashes the official images byte-for-byte — it adds, enables, and controls no extra functionality. What the firmware does once it's on the board is on you.

The **suicide build** is an owner-only, **defensive** measure for protecting the data on your own device — not an attack tool. Provision and use it only on hardware you own, and read the Suicide-Marauder repo's **[SAFETY.md](https://github.com/LxveAce/Suicide-Marauder/blob/main/docs/SAFETY.md)** before enabling it.

Provided "as is" with no warranty. See [DISCLAIMER.md](DISCLAIMER.md) for the full notice.

Found a vulnerability? Don't open a public issue — see [SECURITY.md](SECURITY.md).

PRs and bug reports welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).

## Credits

- Firmware: [ESP32 Marauder](https://github.com/justcallmekoko/ESP32Marauder) by justcallmekoko (GPL) — this app talks to it over serial.
- Optional flash targets: [ESP32-DIV](https://github.com/cifertech/esp32-div) by cifertech, [Bruce](https://github.com/pr3y/Bruce) by pr3y — this app only flashes official images.
- Built with [pyserial](https://pyserial.readthedocs.io/), [PyQt5](https://www.riverbankcomputing.com/software/pyqt/), [Textual](https://textual.textualize.io/), [Flask](https://flask.palletsprojects.com/), and [esptool](https://github.com/espressif/esptool).

[MIT License](LICENSE) | [Changelog](CHANGELOG.md)

## Connect

- **Discord:** [discord.gg/lxveace](https://discord.gg/lxveace) — questions, help, or to talk through this project
- **GitHub:** [@LxveAce](https://github.com/LxveAce)
- **Website:** [lxveace.com](https://lxveace.com)
- **Project site:** [esp32marauder.com](https://esp32marauder.com)