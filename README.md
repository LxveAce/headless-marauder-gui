# Headless Marauder

**Native control for a headless [ESP32 Marauder](https://github.com/justcallmekoko/ESP32Marauder) + a multi-firmware ESP32 flasher.**
No browser, no Web Serial, no cloud — a real Linux/Kali application that talks straight to the
board over USB serial, shows live Access-Point / Station tables, picks targets with checkboxes,
logs everything to disk, and flashes firmware itself — Marauder by default, with a **Firmware**
selector for [ESP32-DIV](https://github.com/cifertech/esp32-div) (flash-only) and any custom local `.bin`.

> Built for a headless Marauder (e.g. a Lonely Binary "Gold" ESP32 with an external antenna and
> no screen) driven from a Raspberry Pi / laptop. Works with any ESP32 running Marauder firmware.
Control and flash a headless [ESP32 Marauder](https://github.com/justcallmekoko/ESP32Marauder) from your computer — no browser, no Web Serial, no cloud. A real app that talks to the board over USB serial, shows live AP/Station tables, lets you pick targets with checkboxes, logs everything to disk, and flashes firmware itself.

> Built for a headless Marauder (like a Lonely Binary "Gold" ESP32 with an antenna and no screen) driven from a Raspberry Pi or laptop — works great as the brain of a cyberdeck. Compatible with any ESP32 running Marauder firmware.

**Runs on:** Linux (Kali, Debian, Ubuntu, Arch, Fedora), Windows 10/11, macOS, WSL2

---

## Why this exists

The browser UIs for Marauder rely on the Web Serial API, which only works in Chromium. On Kali (Firefox by default) they just don't work, and they're pretty limited anyway. This is a native app — it owns the serial port directly, exposes the full Marauder command set, and runs anywhere (including headless on a deck at boot).

## What it does

- **Four front-ends, one core** — a PyQt5 desktop GUI (recommended), a Tkinter GUI, a Textual TUI for terminal/SSH, and a browser UI (Flask + WebSocket at localhost:5000).
- **Every Marauder command** (70+) as buttons and tree entries, with parameter forms, plus a raw command box.
- **Live tables** — `scanap` fills the Access Points tab automatically; APs and stations parsed straight off the serial stream.
- **Target picker** — check the networks you want, it builds the right `select -a 0,2,5` from Marauder's indices.
- **Built-in flasher** — detects the chip (ESP32 vs S3), pulls firmware from GitHub, flashes at the right offsets with `--flash_size detect`. App-only or full blank-board flash.
- **Data logging** — raw serial log, live `latest.json` snapshot, `aps.csv` / `stations.csv` to a folder you pick. Other tools can `tail -f` or poll these while the app runs.
- **Built-in help** — tooltips on every command; an in-app Guide tab covers attack chaining and feeding data into Wireshark, hashcat, WiGLE, Kismet, etc.
- **Self-update** — Help > Check for Updates pulls the latest code and reinstalls deps.
- **Installable** — adds to your PATH, app menu (Linux), Start Menu (Windows). Run from anywhere after install.

---

## Install

### Download (easiest)

The browser UIs for Marauder rely on the **Web Serial API**, which only exists in Chromium — so
on Kali (Firefox by default) they simply don't work, and they're thin on options. This is a
**native app**: it owns `/dev/ttyUSB0` directly, exposes the *full* Marauder command set, and runs
in any environment (and can auto-start headless).
Grab a pre-built binary from the [Releases page](https://github.com/LxveAce/headless-marauder-gui/releases/latest) — no Python or Git needed:

| Platform | File | Notes |
|----------|------|-------|
| Windows x64 | `headless-marauder-vX.X.X-windows-x64.exe` | Double-click to run |
| Linux x64 | `headless-marauder-vX.X.X-linux-x64` | `chmod +x` then run |
| Linux ARM64 | `headless-marauder-vX.X.X-linux-arm64` | Raspberry Pi (64-bit OS), ARM SBCs |

- **Three front-ends, one core** — a polished **PyQt5 GUI** (recommended), a simple **Tkinter GUI**, and a **Textual TUI** for the terminal/SSH.
- **Every Marauder command** (70+) as buttons/tree entries, with parameter forms, plus a raw command box for anything.
- **Live tables** — `scanap` auto-fills the **Access Points** tab (and the TUI table); APs/Stations parsed straight off the serial stream and de-duplicated.
- **Target picker** — click *Select APs* and check the networks you want; it builds the correct `select -a 0,2,5` from Marauder's real indices (manual entry still available).
- **Built-in firmware flasher** — detects the chip (classic ESP32 vs S3), pulls the right firmware variant from the official GitHub release, and flashes at the correct offsets with `--flash_size detect`. App-only update *or* full blank-board flash. Wraps `esptool`.
- **Multiple firmware types (Firmware selector)** — the flasher has a **Firmware** dropdown so the same esptool plumbing can flash more than just Marauder:
  - **ESP32 Marauder** *(default)* — the full native control app this tool is built around (live tables, target picker, every command). The flasher pulls variants from the official Marauder GitHub release. **This is the only firmware the Suicide build applies to.**
  - **ESP32-DIV** ([cifertech/esp32-div](https://github.com/cifertech/esp32-div)) — **flash-only.** This tool only flashes the official ESP32-DIV image byte-for-byte; it adds and enables **no** extra functionality. ESP32-DIV ships RF-**jamming** features that are **illegal to operate** — those are **not part of this tool** and are not controlled or driven from here. After flashing, ESP32-DIV runs as its own standalone firmware on the board (no native control panel here).
  - **Custom / local `.bin`** — point the flasher at any local `.bin` you provide and flash it with chip-appropriate default offsets, for any other ESP32 firmware. Flash-only, you-supply-the-image; nothing is downloaded.
- **Suicide build (anti-forensic), opt-in — Marauder only** — with the **Firmware** selector on **ESP32 Marauder**, a single **Suicide** checkbox in the flasher points at a pre-built **bundle** directory and flashes a provisioned anti-forensic image (boot password + 2-fail wipe + GPIO dead-man) instead of a plain release. The bundle is **built and provisioned in the separate private repo [LxveAce/Suicide-Marauder](https://github.com/LxveAce/Suicide-Marauder)** (it does the password hashing / eFuse + flash-encryption work); this app only flashes the already-provisioned `bundle.json` + `.bin` images. The Suicide build **applies to Marauder only** — it has no meaning for ESP32-DIV or Custom firmware. **Plain Marauder stays the default** — leave the box unchecked and nothing changes.
- **Hover tooltips** — hover any control (buttons, flasher fields, the Suicide checkbox) for a one-line tooltip explaining what it does.
- **Data logging** — capture the raw serial stream + a live `latest.json` snapshot + `aps.csv`/`stations.csv` to a folder you choose; `tail -f`-friendly for other tools/devices.
- **Built-in help** — hover any command for a description; an in-app **Guide** tab (the full [GUIDE.md](GUIDE.md)) explains every tool and how to **chain scanning + attacks** and feed the results into other software (Wireshark, hashcat, WiGLE, Kismet…).
- **Self-update** — *Help → Check for Updates* runs `git pull` + reinstall from this repo.
- **Installable** — `./install.sh` adds it to your application menu and a `headless-marauder` command. Touch-aware, but optimized for keyboard + mouse (shortcuts below).
Everything's bundled — Python, PyQt5, all dependencies. Download, run, plug in your ESP32.

> The standalone builds only include the Qt GUI. For the TUI, browser UI, or dev work, install from source. Updates require downloading the new release (no in-app updater in standalone mode).
>
> **Pi users:** ARM64 build needs a 64-bit OS (Pi OS 64-bit, Kali ARM 64-bit, Ubuntu ARM). On 32-bit, install from source instead.

---

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

Gets you `headless-marauder-tk` and `headless-marauder-tui`. The Qt GUI needs to be run from a clone (`python -m gui_qt.app`) since Qt entry points can be finicky with pip.

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

Flags: `--mock` (no hardware), `--port COM3` or `--port /dev/ttyUSB0` (skip autodetect), `--log` (start recording).
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

Updates touch source code, docs, the command catalog, and flasher logic. They don't touch your venv (deps install on top), log files, serial settings, or any local config.

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

Run `headless-marauder-web` (or `python web/app.py`) and open **http://localhost:5000**. Same features as the desktop GUIs — command sidebar, live console, AP/Station tables, parameter forms, auto-list, logging, keyboard shortcuts (`Ctrl+L` clear, `Ctrl+K` command box, `Ctrl+.` STOP). Raw input supports arrow-key history.

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
2. **Detect chip** — figures out if it's a classic ESP32 or S3
3. **Load release list** — pulls from the official Marauder GitHub
4. Pick a variant (auto-selected based on your chip)
5. **Update app only** (existing board) or **Full flash** (blank board)
6. **FLASH** — progress streams in real-time

**Flashing:** *⚡ Flash Firmware* → pick the **Firmware** (ESP32 Marauder by default; or ESP32-DIV / Custom) → **Detect chip** → **Load release list** (or, for Custom, choose your local `.bin`) → pick a variant → **Update app only** (existing board) or **Full flash** (blank board) → **FLASH**. ESP32-DIV is flash-only (official image, no jamming features); Custom flashes any `.bin` you supply.

**Suicide build (anti-forensic, opt-in — Marauder only):** with the **Firmware** selector on **ESP32 Marauder**, build + provision the bundle first in the separate **[LxveAce/Suicide-Marauder](https://github.com/LxveAce/Suicide-Marauder)** repo, then in the flasher tick the **Suicide** checkbox and point it at that bundle directory (the one holding `bundle.json` + the `.bin` images) → **Detect chip** → **FLASH**. This flashes the provisioned anti-forensic image (boot password + 2-fail wipe + GPIO dead-man); the app never burns eFuses or hashes passwords — that all happens during provisioning in the Suicide-Marauder repo. Unchecked, flashing is plain Marauder as above. Read that repo's **SAFETY.md** and test in safe mode first (see [GUIDE.md](GUIDE.md)).
### Logging

Toggle **Log** in the toolbar (or File > Set Log Folder). Default: `~/marauder-logs`.

| File | What's in it |
|------|-------------|
| `serial-YYYYMMDD-HHMMSS.log` | Raw serial stream (`tail -f` it) |
| `latest.json` | Live snapshot: AP/station counts + full arrays |
| `aps.csv` | Parsed APs (SSID, channel, RSSI, BSSID) |
| `stations.csv` | Parsed stations (MAC, AP BSSID, RSSI) |

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
marauder_core/   controller.py  parsing.py  commands.py  flasher.py  capture.py  updater.py
gui_qt/app.py    PyQt5 GUI (live tables, picker, flasher, logging)
gui/app.py       Tkinter GUI (simple, stdlib)
tui/app.py       Textual terminal UI
web/app.py       Browser UI (Flask + SocketIO at localhost:5000)
install.sh       Linux installer (app menu + PATH + venv)
install.bat      Windows installer (Start Menu + PATH + venv)
```

One command catalog and one parser feed all four front-ends. The serial layer streams to the UI, the parser, and the logger at the same time.

---

## Legal

**For authorized security testing only.** Use on networks and devices you own or have written permission to test. WiFi deauth, evil portals, BLE spam — these can be illegal against other people's stuff (CFAA, FCC rules, etc.). You are responsible for how you use this tool.

Provided "as is" with no warranty. See [DISCLAIMER.md](DISCLAIMER.md) for the full notice.

Found a vulnerability? Don't open a public issue — see [SECURITY.md](SECURITY.md).

PRs and bug reports welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).

---

The **ESP32-DIV** firmware (an optional flash target) includes **RF-jamming** features that are
**illegal to operate** in most jurisdictions (e.g. FCC rules). Those features are **not part of
this tool** — this app only *flashes* the official ESP32-DIV image byte-for-byte and neither
enables, controls, nor exposes any jamming functionality. What the firmware does once it's on the
board is entirely on you.

The optional **suicide build** is an owner-only, **defensive** measure for protecting the data on *your own* device under duress, loss, or seizure — not an attack tool. Provision and use it only on hardware you own, and read the Suicide-Marauder repo's **[SAFETY.md](https://github.com/LxveAce/Suicide-Marauder/blob/main/SAFETY.md)** before enabling it.

## Credits & License

- Firmware: **[ESP32 Marauder](https://github.com/justcallmekoko/ESP32Marauder)** by justcallmekoko (GPL) — this app only talks to it over serial.
- Optional flash target: **[ESP32-DIV](https://github.com/cifertech/esp32-div)** by cifertech — this app only **flashes** the official image; it does not bundle, modify, or operate any ESP32-DIV feature.
- Built on [pyserial](https://pyserial.readthedocs.io/), [PyQt5](https://www.riverbankcomputing.com/software/pyqt/), [Textual](https://textual.textualize.io/), and [esptool](https://github.com/espressif/esptool).
## Credits

- Firmware: [ESP32 Marauder](https://github.com/justcallmekoko/ESP32Marauder) by justcallmekoko (GPL) — this app just talks to it over serial.
- Built with [pyserial](https://pyserial.readthedocs.io/), [PyQt5](https://www.riverbankcomputing.com/software/pyqt/), [Textual](https://textual.textualize.io/), [Flask](https://flask.palletsprojects.com/), and [esptool](https://github.com/espressif/esptool).
- Part of the [cyberdeck project](https://github.com/LxveAce/Projects/tree/main/projects/14-cyberdeck).

[MIT License](LICENSE) | [Changelog](CHANGELOG.md)
