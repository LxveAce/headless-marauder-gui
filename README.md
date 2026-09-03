> ## ⛔ Retired — see [Cyber Controller](https://github.com/LxveAce/cyber-controller)
> Headless Marauder is retired. Its Marauder control and multi-firmware flashing carried forward into
> **Cyber Controller**, the actively-developed flagship. This repo stays up for reference — no further updates.

<div align="center">

<img src="assets/icon.svg" width="120" alt="Headless Marauder">

# Headless Marauder

### The all-in-one ESP32 Marauder controller and multi-firmware flasher.

Connect, scan, attack, flash. 70 commands and 4 front-ends in one standalone app, with no Python, browser, or cloud.

[![Release](https://img.shields.io/github/v/release/LxveAce/headless-marauder-gui?style=for-the-badge&color=39ff14)](https://github.com/LxveAce/headless-marauder-gui/releases/latest)
[![Commands](https://img.shields.io/badge/commands-70-39ff14?style=for-the-badge)](marauder_core/commands.py)
![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20Windows%20%7C%20macOS%20%7C%20Pi-blue?style=for-the-badge)
[![License](https://img.shields.io/github/license/LxveAce/headless-marauder-gui?style=for-the-badge)](LICENSE)
[![Stars](https://img.shields.io/github/stars/LxveAce/headless-marauder-gui?style=for-the-badge)](https://github.com/LxveAce/headless-marauder-gui/stargazers)

**[Download](#install)** · **[Commands](#what-it-does)** · **[Anti-forensic build](#anti-forensic-suicide-build)** · **[Changelog](CHANGELOG.md)** · **[Discord](https://discord.gg/lxvelabs)**

</div>

> ⚠️ **Authorized, lawful use only.** This is a security-research tool. Use it only on systems you own or have explicit permission to test. Provided as-is, no warranty; you assume all risk. See [DISCLAIMER.md](DISCLAIMER.md).

> **Where this fits.** Headless Marauder is the focused, standalone app for ESP32 Marauder — one download, no Python or browser. If you're running more than Marauder — many firmwares, several boards at once, live control and logging in one place — reach for the flagship **[cyber-controller](https://github.com/LxveAce/cyber-controller)**.

---

Most Marauder UIs are browser-based and lean on the Web Serial API, which is Chromium-only. On Kali that means Firefox can't talk to the board at all, and even in Chrome the feature set is thin. Headless Marauder is a native app instead: a full controller and a firmware flasher in one window, running on Linux, Windows, macOS, or a Raspberry Pi. Download it, plug in an ESP32 running Marauder, and go.

It works with any ESP32 running Marauder firmware: headless boards (a Lonely Binary "Gold" with an antenna and no screen) or screened devices (CYD, M5Stack, Flipper devboards). The "Gold" and most headless dev boards are classic ESP32 (WROOM, CH340 USB-serial), not S3.

**Runs on:** Linux (Kali, Debian, Ubuntu, Arch, Fedora), Windows 10/11, macOS (Apple Silicon), Raspberry Pi (ARM64).

<!-- STATUS-ROADMAP:START -->
## 📦 Latest release

**[v1.3.4](https://github.com/LxveAce/headless-marauder-gui/releases/latest)** fixes the flasher-panel crash and hardens remote web security (HTTPS-only fetch allowlist, web UI bound to localhost by default). Full history and what's next is in [CHANGELOG.md](CHANGELOG.md) · [Releases](https://github.com/LxveAce/headless-marauder-gui/releases).
<!-- STATUS-ROADMAP:END -->

---

## What sets it apart

- **All-in-one.** Controller AND flasher in a single app. Connect, scan, attack, flash firmware, or flash an anti-forensic build without switching tools. No separate esptool workflow, no Arduino IDE, no web flasher.
- **One-click exe.** Standalone binaries for Windows, Linux x64, Linux ARM64, and macOS (Apple Silicon). Python, PyQt5, and every dependency are bundled. Download, double-click, go.
- **Open source.** MIT licensed and fully in the open. Read every line, fork it, contribute back.
- **Anti-forensic build support.** Provision and flash a self-wiping, password-gated Marauder right from the app. Owner-only, off by default. [More below](#anti-forensic-suicide-build).
- **Built for the community.** PRs, ideas, and bug reports welcome.

---

## What it does

### Control

- **Four front-ends, one core.** PyQt5 desktop GUI (recommended), Tkinter GUI, a Textual TUI for terminal/SSH, and a browser UI (Flask + WebSocket at localhost:5000). Dark theme across all of them.
- **The full Marauder command set.** Organized into categories as buttons and tree entries, with parameter forms and a raw command box. Auto-connects at 115200 baud, or set `--port` and `--baud` yourself.
- **Live AP/Station tables.** `scanap` fills the Access Points tab in real time; APs and stations are parsed and de-duplicated straight off the serial stream. Auto-list polls every 3 seconds to keep the tables current during a scan.
- **Target picker.** Check the networks you want, select all, or type indices by hand. Builds the right `select -a 0,2,5` from Marauder's own indices.
- **Hover tooltips.** Every button, field, and checkbox has a plain-language tooltip. Shared glossary across all four UIs.

### Full command coverage

The catalog in `marauder_core/commands.py` is the single source of truth that drives every front-end. Add a command once and it shows up everywhere. It's grouped like this:

| Category | What's in it |
|----------|-------------|
| **WiFi · Scan** | AP scan, station scan, scan-all, signal monitor, packet count, MAC track, GPS wardrive |
| **WiFi · Sniff** | Raw, beacon, probe, deauth (detect), ESP, Pwnagotchi, and PMKID/EAPOL capture (SavePCAP to SD) |
| **WiFi · Attack** | Deauth (selected APs / selected clients), beacon spam (list / random / clone), probe flood, rickroll beacon, bad-msg, evil portal, karma |
| **WiFi · Network** | Join a scanned AP, ping-scan the local network, TCP port scan (with all-ports option) |
| **Bluetooth** | BLE scan (AirTag / Flipper / Flock filters), BT wardrive, skimmer detection, AirTag spoof, and BLE spam (Sour Apple, AppleJuice, Google, Samsung, Windows/Swiftpair, Flipper, All) |
| **GPS** | Live GPS readout, raw NMEA stream, and per-field queries (fix, sats, lat/lon, altitude, date, accuracy) |
| **Lists & Targets** | Select/clear APs, stations, and SSIDs; list APs/clients/SSIDs/targets; select-by-filter; device info |
| **SSID** | Add a named SSID, generate N random SSIDs, remove by index |
| **Channel** | Show / set the active WiFi channel |
| **Files** | SD-card directory listing, save/load AP and SSID lists to SD |
| **System** | Settings toggles, LED color/rainbow, OTA updates (serial + WiFi), reboot, device help, stopscan |

### Flasher

- **Multi-firmware.** Flash [ESP32 Marauder](https://github.com/justcallmekoko/ESP32Marauder) (default), [ESP32-DIV](https://github.com/cifertech/esp32-div), [Bruce](https://github.com/pr3y/Bruce), or any custom local `.bin`. A pluggable `FirmwareProfile` registry drives the detect/release/variant logic per firmware, and the **Firmware** selector switches profiles and UI on the fly.
- **Auto chip detection.** esptool identifies the connected part (classic ESP32, S2, S3, and the RISC-V parts C2, C3, C5, C6, H2), then auto-selects the matching firmware variant and the correct per-chip bootloader offset. That includes the `0x2000` second-stage offset the newest parts (C5/P4/H4) need, so a full flash never lands the bootloader at the wrong address.
- **App-only or full flash.** Update an existing board (app image only) or flash a blank board from scratch (bootloader + partitions + boot_app0 + app, with the correct offsets).
- **Erase flash.** Full chip erase for a clean slate.
- **Anti-forensic build flashing.** Provision and flash a self-wiping Marauder with SHA256 integrity verification. Flash-only; it never burns eFuses. See [below](#anti-forensic-suicide-build).
- **Security hardened.** HTTPS-only firmware fetching with a GitHub host allowlist, path-traversal protection on downloads, and SSRF/redirect defense (redirects followed only to allowlisted hosts).

### Logging & data export

- **Raw serial log.** The full serial stream to `serial-YYYYMMDD-HHMMSS.log`, `tail -f` friendly.
- **Live JSON snapshot.** `latest.json`, refreshed about every 3.5 seconds with AP/station counts, full arrays, timestamps, and session metadata. Atomic writes, so other tools can poll it safely.
- **CSV export.** `aps.csv` (SSID, channel, RSSI, BSSID) and `stations.csv` (MAC, AP BSSID, RSSI) for spreadsheets, scripts, or feeding into other tools.

### Everything else

- **`--mock` mode.** Run the full UI without hardware for demo, dev, or testing.
- **Built-in guide.** An in-app Guide tab covers attack chaining and feeding data into Wireshark, hashcat, WiGLE, Kismet, and friends.
- **Self-update.** Help > Check for Updates pulls the latest code and reinstalls deps (source installs).
- **Installable.** Adds itself to your PATH, app menu (Linux), and Start Menu (Windows). Run it from anywhere.

---

## Anti-forensic (Suicide) build

An owner-only, defensive firmware option for a Marauder *you own*. It protects the data on the board if it's lost, stolen, or taken from you. Same idea as Kali's LUKS Nuke or GrapheneOS's duress PIN, applied to an ESP32. In the flasher it's the **Suicide build** checkbox, off by default.

### What it adds

All of this is opt-in and configured when you provision:

- **Boot password.** The board won't boot into Marauder without the right password. It's hashed locally with PBKDF2-HMAC-SHA256; the plaintext is never stored, logged, or sent anywhere.
- **Wrong-attempt wipe.** After N wrong passwords (default 2) the board wipes itself.
- **GPIO dead-man switch.** Tie a physical wire to a pin; when the board is armed, a cut or disconnected wire triggers a wipe at boot. It's optional: set `deadman=0` and the arming line is ignored entirely.
- **Master arm flag.** Defaults to **DISARMED**. A board can't wipe until you deliberately arm it. "Provisioned *and* armed" is a two-factor safety, so a fresh or bench board is safe.

### Two ways to use it

From the flasher's Suicide panel:

- **Provision new bundle.** Enter a password and config; the app hashes it locally, builds the `guardcfg` bundle, and flashes it.
- **Flash existing bundle.** Point at a folder that already holds a `bundle.json` + `.bin` images (provisioned elsewhere). Every file is SHA256-verified against the manifest before anything is written: a missing or empty hash is a hard error, path-traversal entries are rejected, and verified files are staged to a private temp dir and re-hashed right before flashing (TOCTOU defense).

### What it does NOT do

The app flashes and provisions a re-flashable (T1) build. It never burns eFuses and never enables Secure Boot or Flash Encryption. Without that irreversible hardening (a separate step this app doesn't perform), the gate stops a casual finder, but a determined attacker with the hardware can still pull the chip or re-flash past it. Treat it as theft and coercion deterrence, not a guarantee against a forensics lab.

> **Read [`suicide/docs/SAFETY.md`](suicide/docs/SAFETY.md) before you arm anything.** The wipe is real and there's no undo: recovery from a real wipe is re-flashing a blank board. Always test in `SUICIDE_SAFE_MODE` first. The provisioner and full threat model live in the successor project, [Dead Man's Switch](https://github.com/LxveAce/deadmans-switch) (formerly Suicide-Marauder).

---

## Install

### Download (easiest)

Grab a pre-built binary from the [latest release](https://github.com/LxveAce/headless-marauder-gui/releases/latest), with no Python or Git needed:

| Platform | File | Notes |
|----------|------|-------|
| Windows x64 | `headless-marauder-vX.X.X-windows-x64.exe` | Double-click to run |
| Linux x64 | `headless-marauder-vX.X.X-linux-x64` | `chmod +x` then run |
| Linux ARM64 | `headless-marauder-vX.X.X-linux-arm64` | Raspberry Pi (64-bit OS), ARM SBCs |
| macOS arm64 | `headless-marauder-vX.X.X-macos-arm64` | Apple Silicon (M-series) |

Everything's bundled: Python, PyQt5, all dependencies. Download, run, plug in your ESP32. (Replace `vX.X.X` with the latest version on the Releases page.)

> The standalone builds ship the Qt GUI only. For the TUI, browser UI, or dev work, install from source. Updates mean downloading the new release (no in-app updater in standalone mode).
>
> **Pi users:** the ARM64 build needs a 64-bit OS (Pi OS 64-bit, Kali ARM 64-bit, Ubuntu ARM). On 32-bit, install from source instead.

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

Gives you `headless-marauder`, `headless-marauder-tk`, `headless-marauder-tui`, and `headless-marauder-web`, plus a Start Menu shortcut.

> Open a new terminal after install so PATH takes effect.

**CH340 driver:** if Windows doesn't see your ESP32, grab the [CH340 driver](https://www.wch-ic.com/downloads/CH341SER_EXE.html). The board shows up as a COM port (e.g. `COM3`).

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

Add `--mock` to try it without hardware, `--port /dev/tty.usbserial-xxxx` to pin a port.

#### pip install

```bash
pip install "headless-marauder[all] @ git+https://github.com/LxveAce/headless-marauder-gui.git"
```

Gets you `headless-marauder-tk`, `headless-marauder-tui`, and `headless-marauder-web`. The Qt GUI runs from a clone (`python -m gui_qt.app`) since Qt entry points can be finicky with pip.

To provision anti-forensic bundles, install the `suicide` extra. It adds `esp-idf-nvs-partition-gen`, the NVS image generator the provisioner needs and esptool doesn't bundle. From a clone: `pip install .[suicide]` (quote as `'.[suicide]'` in zsh). The `[all]` install above already includes it.

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

Flags: `--mock` (no hardware), `--port COM3` or `--port /dev/ttyUSB0` (skip autodetect), `--baud 115200` (custom baud), `--no-autoconnect` (don't connect on launch), `--log` (start recording immediately). Browser UI: `--host 0.0.0.0` (LAN access), `--web-port 8080` (custom port).
</details>

---

## Using it

1. **Connect.** Auto-detects the board (115200 baud). The top bar turns green.
2. **Scan APs.** With auto-list on (default), the Access Points tab fills while scanning.
3. **STOP** when you've seen enough.
4. **Select APs.** Tick networks in the picker; it sends `select -a ...`.
5. Run an action, e.g. Deauth (selected APs).

### Browser UI

Run `headless-marauder-web` (or `python web/app.py`) and open http://localhost:5000. It has the same features as the desktop GUIs: command sidebar, live console, AP/Station tables, parameter forms, auto-list, logging, the firmware flash panel (multi-firmware + Suicide build), and keyboard shortcuts (`Ctrl+L` clear, `Ctrl+K` command box, `Ctrl+.` STOP). Raw input supports arrow-key history.

It binds to localhost only by default. Pass `--host 0.0.0.0` to open it to your LAN. There's no auth, so anyone on the network can control the board.

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

1. Click **Flash Firmware**.
2. Pick the **Firmware**: ESP32 Marauder (default), ESP32-DIV, Bruce, or Custom.
3. **Detect chip** figures out if it's a classic ESP32, S3, etc.
4. **Load release list** pulls from the firmware's official GitHub (or choose your local `.bin` for Custom).
5. Pick a variant (auto-selected from your chip).
6. **Update app only** (existing board) or **Full flash** (blank board).
7. **FLASH.** Progress streams in real time.

For anti-forensic builds, see [Anti-forensic (Suicide) build](#anti-forensic-suicide-build) above.

### Logging

Toggle **Log** in the toolbar (or File > Set Log Folder, or `--log` at launch). Default folder: `~/marauder-logs`.

| File | What's in it |
|------|-------------|
| `serial-YYYYMMDD-HHMMSS.log` | Raw serial stream (`tail -f` friendly) |
| `latest.json` | Live snapshot (~3.5s): AP/station counts, full arrays, timestamps. Atomic writes so other tools can poll safely. |
| `aps.csv` | Parsed APs (SSID, channel, RSSI, BSSID) |
| `stations.csv` | Parsed stations (MAC, AP BSSID, RSSI) |

All of it is meant for piping into other tools: Wireshark, hashcat, WiGLE, Kismet, custom scripts. See the in-app Guide for chaining examples.

---

## Updating

`git pull` in the project folder. Settings and logs are untouched. The easiest way is **Help > Check for Updates** in the app; it pulls and reinstalls deps for you.

From the terminal:
```bash
cd headless-marauder-gui
git pull
# Linux: re-run ./install.sh if deps changed
# Windows: .venv\Scripts\pip.exe install -q -r requirements.txt
```

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

## Troubleshooting

**Linux**
- **No `/dev/ttyUSB0`.** The Gold uses a CH340. On Kali, `brltty` likes to steal it: `sudo apt remove brltty`, then replug. Make sure you're in `dialout`.
- **In a VM.** Pass the USB device through (VirtualBox: Devices > USB; VMware: VM > Removable Devices).
- **Qt GUI won't start.** PyQt5 is missing. `sudo apt install -y python3-pyqt5` (venv needs `--system-site-packages`), or just use the TUI.

**Windows**
- **No COM port.** Install the [CH340 driver](https://www.wch-ic.com/downloads/CH341SER_EXE.html). Check Device Manager > Ports.
- **`headless-marauder` not recognized.** Open a new terminal; PATH was just updated.
- **Permission denied on the COM port.** Close any other serial monitor (Arduino IDE, PuTTY, etc.).

**General**
- **Board boot-loops / `scanap` does nothing.** Check the console:
  - `invalid header: 0xffffffff`: flash is blank; use Full flash.
  - `Detected size(4096k) smaller than ... header(16384k)`: wrong flash-size header. The flasher fixes this with `--flash_size detect`; erase and re-flash.
- **Deauth "does nothing."** Marauder prints the start message once, then runs silently. If a device doesn't drop it's usually 802.11w/PMF (modern routers ignore deauth), a 5GHz target (classic ESP32 is 2.4GHz only), or no clients connected.

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

One command catalog and one parser feed all four front-ends. The serial layer streams to the UI, the parser, and the logger at the same time. The `FirmwareProfile` registry in `flasher.py` keeps the Marauder and Suicide flows byte-for-byte intact while layering the ESP32-DIV, Bruce, and custom profiles on top.

---

## Ecosystem

Headless Marauder is one tool in a small family:

| Project | What it is |
|---|---|
| **[LxveFlasher](https://github.com/LxveAce/universal-flasher)** | This app's `FirmwareProfile` flasher grown into a standalone multi-firmware flasher + device manager. Four flash backends: esptool (ESP32), an SD-image writer (Pwnagotchi / RaspyJack / Kali ARM), ADB (RayHunter), and qFlipper (Flipper Zero). Plus batch flash, backup/restore, offline cache, and a JSON plugin system. See its [releases](https://github.com/LxveAce/universal-flasher/releases) for the current firmware list. |
| **[Dead Man's Switch](https://github.com/LxveAce/deadmans-switch)** | The anti-forensic provisioner behind the Suicide-build path (successor to Suicide-Marauder). A firmware-agnostic boot gate + wipe for ESP32 security firmware. |

---

## Security

The Python code here is what gets audited: the flasher's downloads, the serial bridge, and the web UI. Firmware fetching is HTTPS-only against a GitHub host allowlist, downloads are path-traversal checked, and the browser UI binds to `127.0.0.1` with no auth by default (exposing it with `--host 0.0.0.0` is a documented tradeoff, not a bug; put a reverse proxy in front if you need LAN auth).

Found a vulnerability? Don't open a public issue. Report it privately per [SECURITY.md](SECURITY.md) (GitHub Security Advisories, or email `lxveace@proton.me` with `[SECURITY]` in the subject).

---

## Legal

**For authorized security testing only.** Use it on networks and devices you own or have written permission to test. WiFi deauth, evil portals, and BLE spam can be illegal against other people's stuff (CFAA, FCC rules, and their equivalents worldwide). You're responsible for how you use this.

The ESP32-DIV and Bruce firmwares (optional flash targets) include RF features that may be illegal to operate where you are. This app only flashes the official images byte-for-byte; it adds, enables, and controls no extra functionality. What the firmware does once it's on the board is on you.

The Suicide build is an owner-only, defensive measure for protecting the data on your own device, not an attack tool, and never a way to destroy evidence in a lawful investigation. Provision and use it only on hardware you own, and read [`suicide/docs/SAFETY.md`](suicide/docs/SAFETY.md) first.

Provided "as is" with no warranty. See [DISCLAIMER.md](DISCLAIMER.md) for the full notice.

---

## Contributing

PRs and bug reports are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md). The short version: fork, set up a venv, and develop against `--mock` so you don't need hardware. New commands go in `marauder_core/commands.py`; all four UIs pick them up automatically. If you touch the core, test across Qt, Tk, TUI, and Web.

## Credits

- Firmware: [ESP32 Marauder](https://github.com/justcallmekoko/ESP32Marauder) by justcallmekoko (GPL). This app talks to it over serial.
- Optional flash targets: [ESP32-DIV](https://github.com/cifertech/esp32-div) by cifertech and [Bruce](https://github.com/pr3y/Bruce) by pr3y. This app only flashes the official images.
- Built with [pyserial](https://pyserial.readthedocs.io/), [PyQt5](https://www.riverbankcomputing.com/software/pyqt/), [Textual](https://textual.textualize.io/), [Flask](https://flask.palletsprojects.com/), and [esptool](https://github.com/espressif/esptool). Nothing upstream is vendored; the flasher downloads official release binaries at run time.

## License

[MIT](LICENSE) © LxveAce. See [CHANGELOG.md](CHANGELOG.md) for version history.

## 📫 Connect

- **Discord:** [discord.gg/lxvelabs](https://discord.gg/lxvelabs) for questions, help, or to talk through the project
- **GitHub:** [@LxveAce](https://github.com/LxveAce)
- **Email:** LxveLabs@proton.me (business) · lxveace@proton.me (direct)
- **Sites:** [lxvelabs.com](https://lxvelabs.com) · project site [esp32marauder.com](https://esp32marauder.com)

---

Built by **LxveAce** · a **LxveLabs** project. Hardware and security tools.

Hardware supported by [PCBWay](https://www.pcbway.com): LxveLabs is developing a board in collaboration with PCBWay.
