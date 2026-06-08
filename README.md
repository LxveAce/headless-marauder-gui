# Headless Marauder

**Native control + firmware flasher for a headless [ESP32 Marauder](https://github.com/justcallmekoko/ESP32Marauder).**
No browser, no Web Serial, no cloud — a real application that talks straight to the
board over USB serial, shows live Access-Point / Station tables, picks targets with checkboxes,
logs everything to disk, and flashes firmware itself.

> Built for a headless Marauder (e.g. a Lonely Binary "Gold" ESP32 with an external antenna and
> no screen) driven from a Raspberry Pi / laptop — including as the brain of a cyberdeck. Works
> with any ESP32 running Marauder firmware.

**Platforms:** Linux (Kali, Debian, Ubuntu, Arch, Fedora), Windows 10/11, macOS, WSL2

---

## Why

The browser UIs for Marauder rely on the **Web Serial API**, which only exists in Chromium — so
on Kali (Firefox by default) they simply don't work, and they're thin on options. This is a
**native app**: it owns the serial port directly, exposes the *full* Marauder command set, and runs
in any environment (and can auto-start headless on a deck).

## Features

- **Three front-ends, one core** — a polished **PyQt5 GUI** (recommended), a simple **Tkinter GUI**, and a **Textual TUI** for the terminal/SSH.
- **Every Marauder command** (70+) as buttons/tree entries, with parameter forms, plus a raw command box for anything.
- **Live tables** — `scanap` auto-fills the **Access Points** tab (and the TUI table); APs/Stations parsed straight off the serial stream and de-duplicated.
- **Target picker** — click *Select APs* and check the networks you want; it builds the correct `select -a 0,2,5` from Marauder's real indices (manual entry still available).
- **Built-in firmware flasher** — detects the chip (classic ESP32 vs S3), pulls the right firmware variant from the official GitHub release, and flashes at the correct offsets with `--flash_size detect`. App-only update *or* full blank-board flash. Wraps `esptool`.
- **Data logging** — capture the raw serial stream + a live `latest.json` snapshot + `aps.csv`/`stations.csv` to a folder you choose; `tail -f`-friendly for other tools/devices.
- **Built-in help** — hover any command for a description; an in-app **Guide** tab (the full [GUIDE.md](GUIDE.md)) explains every tool and how to **chain scanning + attacks** and feed the results into other software (Wireshark, hashcat, WiGLE, Kismet...).
- **Self-update** — *Help > Check for Updates* runs `git pull` + reinstall from this repo.
- **Installable** — runs from anywhere after install (no need to `cd` into the project). Adds to your system PATH, application menu (Linux), and Start Menu (Windows).
- **Updatable** — `git pull` in the project folder pulls the latest code. Dependencies auto-update with the in-app updater.

---

## Install

### Linux (Kali / Debian / Ubuntu)

```bash
git clone https://github.com/LxveAce/headless-marauder-gui.git
cd headless-marauder-gui
./install.sh
```

This creates a venv, installs all dependencies (PyQt5, esptool, textual), and adds:
- `headless-marauder` command (Qt GUI) and `headless-marauder-tui` (terminal UI) to `~/.local/bin`
- A **"Headless Marauder"** entry in your application menu

Give yourself serial access without `sudo` (once, then re-login):
```bash
sudo usermod -aG dialout $USER
```

### Windows

**Prerequisites:** [Python 3.9+](https://python.org) (check "Add Python to PATH" during install) and [Git](https://git-scm.com/downloads).

```
git clone https://github.com/LxveAce/headless-marauder-gui.git
cd headless-marauder-gui
install.bat
```

This creates a venv, installs all dependencies (PyQt5, esptool), and adds:
- `headless-marauder`, `headless-marauder-tk`, and `headless-marauder-tui` commands to your PATH
- A **Start Menu shortcut**

> **Open a new terminal** after install for the PATH to take effect.

**CH340 driver:** If Windows doesn't detect your ESP32, install the [CH340 driver](https://www.wch-ic.com/downloads/CH341SER_EXE.html). Your board will appear as a COM port (e.g. `COM3`).

### macOS / Other

```bash
git clone https://github.com/LxveAce/headless-marauder-gui.git
cd headless-marauder-gui
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install PyQt5                # for the Qt GUI
```

Run with:
```bash
source .venv/bin/activate
python3 gui_qt/app.py           # Qt GUI
python3 gui/app.py              # Tkinter GUI
python3 tui/app.py              # Terminal UI
```

Add `--mock` to explore without hardware, `--port /dev/tty.usbserial-xxxx` to specify a port.

### pip install (cross-platform, advanced)

```bash
pip install git+https://github.com/LxveAce/headless-marauder-gui.git[all]
```

This installs `headless-marauder-tk` and `headless-marauder-tui` as commands. The PyQt5 GUI requires running `python -m gui_qt.app` from the cloned repo (Qt entry points don't play well with all pip environments).

<details>
<summary>Manual / dev run (no installer)</summary>

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

Add `--mock` to explore with no board, `--port COM3` or `--port /dev/ttyUSB0` to skip auto-detect, `--log` to start recording immediately.
</details>

---

## Update

Headless Marauder updates via `git pull` — your settings and logs are untouched.

### From the app (easiest)

**Help > Check for Updates** — pulls the latest code and reinstalls dependencies automatically.

### From the terminal

```bash
cd headless-marauder-gui
git pull
```

On Linux, re-run the installer if dependencies changed:
```bash
./install.sh
```

On Windows:
```
.venv\Scripts\pip.exe install -q -r requirements.txt
```

### What updates touch

| Updated | Not touched |
|---------|-------------|
| All Python source code | Your `.venv` (deps reinstalled on top) |
| GUIDE.md, README.md | Your log files (`~/marauder-logs`) |
| Command catalog (new commands appear in UI) | Your serial port settings |
| Flasher logic (new chip support) | Any local config you've made |

---

## Uninstall

### Linux
```bash
cd headless-marauder-gui
./uninstall.sh          # removes launchers + menu entry
rm -rf ../headless-marauder-gui   # remove the repo + venv
```

### Windows
```
cd headless-marauder-gui
uninstall.bat           # removes launchers + Start Menu shortcut
```
Then delete the `headless-marauder-gui` folder manually.

---

## Using it

1. **Connect** — it auto-detects the board (115200 baud); the top bar turns green.
2. **Scan APs** — with **Auto-list** on (default), the **Access Points** tab fills itself while it scans.
3. **STOP** when you've seen enough.
4. **Select APs** — tick the network(s) in the picker > it sends `select -a ...`.
5. Run an action — e.g. **Deauth (selected APs)** (leave `src`/`dst` blank for a normal broadcast deauth).

### Keyboard shortcuts (Qt GUI)

| Shortcut | Action |
|----------|--------|
| `Ctrl+L` | Clear console |
| `F5` | Refresh serial ports |
| `Ctrl+K` | Focus raw command box |
| `Ctrl+.` | STOP (stop all scans/attacks) |
| `Ctrl+U` | Check for updates |
| `Ctrl+Q` | Quit |
| `F1` | Open Guide tab |

### Flashing firmware

1. Click **Flash Firmware**
2. **Detect chip** — identifies classic ESP32 vs S3
3. **Load release list** — fetches from the official Marauder GitHub
4. Pick a variant (auto-selected based on your chip)
5. Choose **Update app only** (existing board) or **Full flash** (blank board)
6. Click **FLASH** — progress streams in real-time

### Logging

Toggle **Log** in the toolbar (or *File > Set Log Folder*). Default: `~/marauder-logs`.

| File | Contents |
|------|----------|
| `serial-YYYYMMDD-HHMMSS.log` | Raw serial stream (`tail -f` friendly) |
| `latest.json` | Live snapshot: AP count, station count, full arrays |
| `aps.csv` | Parsed access points (SSID, channel, RSSI, BSSID) |
| `stations.csv` | Parsed stations (MAC, AP BSSID, RSSI) |

---

## Troubleshooting

### Linux

- **No `/dev/ttyUSB0`** — the Gold uses a CH340. On Kali, `brltty` often steals it: `sudo apt remove brltty`, replug. Also ensure you're in `dialout`.
- **In a VM** — pass the USB device through to the guest (VirtualBox: Devices > USB; VMware: VM > Removable Devices).
- **Qt GUI won't start** — PyQt5 missing: `sudo apt install -y python3-pyqt5` (venv must use `--system-site-packages`), or use `headless-marauder-tui`.

### Windows

- **No COM port** — install the [CH340 driver](https://www.wch-ic.com/downloads/CH341SER_EXE.html). Check Device Manager > Ports.
- **`headless-marauder` not recognized** — open a **new** terminal after install (PATH was updated for the current user). Or run `%USERPROFILE%\.local\bin\headless-marauder.bat` directly.
- **Permission denied on COM port** — close any other serial monitor (Arduino IDE, PuTTY, etc.) that has the port open.

### General

- **Board boot-loops / `scanap` does nothing** — check the Console:
  - `invalid header: 0xffffffff` — flash is **blank** — use flasher **Full flash**.
  - `Detected size(4096k) smaller than ... header(16384k)` — wrong flash-size header — the flasher fixes this with `--flash_size detect`; **Erase**, then re-flash.
- **Deauth "does nothing"** — Marauder prints `Starting Deauthentication attack` once, then runs silently. If a device doesn't drop, it's almost always **802.11w/PMF** (modern routers ignore deauth), a **5GHz** target (classic ESP32 is 2.4GHz only), or **no clients** connected.

---

## Architecture

```
marauder_core/   controller.py  parsing.py  commands.py  flasher.py  capture.py  updater.py
gui_qt/app.py    PyQt5 GUI (live tables, picker, flasher, logging)   <-- recommended
gui/app.py       Tkinter GUI (simple, stdlib)
tui/app.py       Textual terminal UI
install.sh       Linux installer (app menu + PATH launchers + venv)
install.bat      Windows installer (Start Menu + PATH launchers + venv)
```

One command catalog and one parser feed all three front-ends; the serial layer streams to the UI, the parser, and the logger together.

---

## Legal

For **authorized security testing only** — use against networks and devices you own or have
explicit written permission to test. WiFi deauthentication, evil-portal, and BLE-spam features can
be illegal to use against others (e.g. US CFAA, FCC rules). You are responsible for how you use this.

## Credits & License

- Firmware: **[ESP32 Marauder](https://github.com/justcallmekoko/ESP32Marauder)** by justcallmekoko (GPL) — this app only talks to it over serial.
- Built on [pyserial](https://pyserial.readthedocs.io/), [PyQt5](https://www.riverbankcomputing.com/software/pyqt/), [Textual](https://textual.textualize.io/), and [esptool](https://github.com/espressif/esptool).
- Part of the [Cyberdeck project](https://github.com/LxveAce/Projects/tree/main/projects/14-cyberdeck).

Licensed under the **[MIT License](LICENSE)**.
