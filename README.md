# Headless Marauder

**Native control for a headless [ESP32 Marauder](https://github.com/justcallmekoko/ESP32Marauder) + a multi-firmware ESP32 flasher.**
No browser, no Web Serial, no cloud — a real Linux/Kali application that talks straight to the
board over USB serial, shows live Access-Point / Station tables, picks targets with checkboxes,
logs everything to disk, and flashes firmware itself — Marauder by default, with a **Firmware**
selector for [ESP32-DIV](https://github.com/cifertech/esp32-div) (flash-only) and any custom local `.bin`.

> Built for a headless Marauder (e.g. a Lonely Binary "Gold" ESP32 with an external antenna and
> no screen) driven from a Raspberry Pi / laptop. Works with any ESP32 running Marauder firmware.

---

## Why

The browser UIs for Marauder rely on the **Web Serial API**, which only exists in Chromium — so
on Kali (Firefox by default) they simply don't work, and they're thin on options. This is a
**native app**: it owns `/dev/ttyUSB0` directly, exposes the *full* Marauder command set, and runs
in any environment (and can auto-start headless).

## Features

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

---

## Install (Kali / Debian)

```bash
git clone https://github.com/LxveAce/headless-marauder-gui.git
cd headless-marauder-gui
./install.sh
```

That sets up a venv, installs dependencies (incl. PyQt5 and `esptool`), and adds:
- a menu entry **“Headless Marauder”**,
- a `headless-marauder` command (Qt GUI) and `headless-marauder-tui` (terminal UI).

Give yourself serial access without `sudo` (once, then re-login):
```bash
sudo usermod -aG dialout $USER
```

<details>
<summary>Manual / dev run (no installer)</summary>

```bash
sudo apt install -y python3-venv python3-tk python3-pyqt5
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install -r requirements.txt        # pyserial + textual + esptool
python3 gui_qt/app.py                   # or: gui/app.py  /  tui/app.py
# add --mock to explore with no board, --port /dev/ttyUSB0 to skip auto-detect, --log to record
```
</details>

---

## Using it

1. **Connect** — it auto-detects the board (115200 baud); the top bar turns green.
2. **Scan APs** — with **Auto-list** on (default), the **Access Points** tab fills itself while it scans.
3. **STOP** when you've seen enough.
4. **Select APs** — tick the network(s) in the picker → it sends `select -a …`.
5. Run an action — e.g. **Deauth (selected APs)** (leave `src`/`dst` blank for a normal broadcast deauth).

**Keyboard shortcuts (Qt):** `Ctrl+L` clear · `F5` refresh ports · `Ctrl+K` focus command box · `Ctrl+.` STOP · `Ctrl+U` check for updates · `Ctrl+Q` quit.

**Flashing:** *⚡ Flash Firmware* → pick the **Firmware** (ESP32 Marauder by default; or ESP32-DIV / Custom) → **Detect chip** → **Load release list** (or, for Custom, choose your local `.bin`) → pick a variant → **Update app only** (existing board) or **Full flash** (blank board) → **FLASH**. ESP32-DIV is flash-only (official image, no jamming features); Custom flashes any `.bin` you supply.

**Suicide build (anti-forensic, opt-in — Marauder only):** with the **Firmware** selector on **ESP32 Marauder**, build + provision the bundle first in the separate **[LxveAce/Suicide-Marauder](https://github.com/LxveAce/Suicide-Marauder)** repo, then in the flasher tick the **Suicide** checkbox and point it at that bundle directory (the one holding `bundle.json` + the `.bin` images) → **Detect chip** → **FLASH**. This flashes the provisioned anti-forensic image (boot password + 2-fail wipe + GPIO dead-man); the app never burns eFuses or hashes passwords — that all happens during provisioning in the Suicide-Marauder repo. Unchecked, flashing is plain Marauder as above. Read that repo's **SAFETY.md** and test in safe mode first (see [GUIDE.md](GUIDE.md)).

**Logging:** toggle **● Log** (or *File → Set Log Folder*). Writes to `~/marauder-logs` by default — `serial-*.log`, `latest.json`, `aps.csv`, `stations.csv`, all live-readable.

---

## Troubleshooting

- **No `/dev/ttyUSB0`** — the Gold uses a CH340. On Kali, `brltty` often steals it: `sudo apt remove brltty`, replug. Also ensure you're in `dialout`. In a VM, pass the USB device through.
- **Board boot-loops / `scanap` does nothing** — check the Console:
  - `invalid header: 0xffffffff` → flash is **blank** → flasher **Full flash**.
  - `Detected size(4096k) smaller than ... header(16384k)` → wrong flash-size header → the flasher fixes this with `--flash_size detect`; **Erase**, then re-flash.
- **Deauth "does nothing"** — Marauder prints `Starting Deauthentication attack` once, then runs silently. If a device doesn't drop, it's almost always **802.11w/PMF** (modern routers ignore deauth), a **5GHz** target (classic ESP32 is 2.4GHz only), or **no clients** connected.
- **Qt GUI won't start** — PyQt5 missing: `sudo apt install -y python3-pyqt5` (and make the venv with `--system-site-packages`), or use `headless-marauder-tui`.

---

## Architecture

```
marauder_core/   controller.py · parsing.py · commands.py · flasher.py · capture.py · updater.py
gui_qt/app.py    PyQt5 GUI (live tables, picker, flasher, logging)   ← recommended
gui/app.py       Tkinter GUI (simple, stdlib)
tui/app.py       Textual terminal UI
install.sh       app-menu install + launchers + self-update enablement
```
One command catalog and one parser feed all three front-ends; the serial layer streams to the UI, the parser, and the logger together.

---

## Legal

For **authorized security testing only** — use against networks and devices you own or have
explicit written permission to test. WiFi deauthentication, evil-portal, and BLE-spam features can
be illegal to use against others (e.g. US CFAA, FCC rules). You are responsible for how you use this.

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

Licensed under the **[MIT License](LICENSE)**.
