# Changelog

## [1.2.0] — 2026-06-08

Added a browser-based UI, standalone executables, and project policies.

**New stuff:**
- Browser UI — Flask + SocketIO at `localhost:5000`. Full command sidebar, live console over WebSocket, AP/Station tables, parameter forms, raw command input with history, auto-list, logging, keyboard shortcuts (Ctrl+L/K/.), dark theme, `--mock` and `--host 0.0.0.0` support.
- `headless-marauder-web` launcher for Linux and Windows
- `run-web.sh` / `run-web.bat` dev scripts
- SECURITY.md, DISCLAIMER.md, CONTRIBUTING.md, this changelog
- Standalone executables (Windows .exe, Linux x64/ARM64 binaries) on the Releases page — no Python needed
- `build.py` for local PyInstaller builds
- GitHub Actions CI to auto-build on each release

**Fixed:**
- Web UI: `flasher.detect_chip()` crash from missing callback argument
- Web UI: XSS through malicious SSIDs in the AP/Station tables
- Web UI: autolist timer stacking when toggled rapidly
- Web UI: keyboard shortcuts not working when the command input was focused

**Changed:**
- requirements.txt and pyproject.toml updated for Flask/SocketIO deps
- Installers now include the web UI launcher
- README updated with browser UI docs

## [1.1.0] — 2026-06-08

Cross-platform release — Windows support, pip install.

- Windows installer (`install.bat`) with venv, PATH, Start Menu shortcut
- `pip install git+....[all]` for cross-platform installs
- `pyproject.toml` with optional dep groups (`[qt]`, `[tui]`, `[all]`)
- Updated `install.sh` / `uninstall.sh` with TUI launcher

## [1.0.1] — 2026-06-08

- In-app Guide tab with full tool reference
- `GUIDE.md` — attack chaining walkthrough and integration guide for other tools
- Hover tooltips on all command buttons

## [1.0.0] — 2026-06-08

Initial release.

- PyQt5 GUI with live AP/Station tables, target picker, firmware flasher, logging
- Tkinter GUI (lightweight alternative)
- Textual TUI for terminal/SSH use
- `marauder_core` shared library — serial controller, 70+ command catalog, stream parser, firmware flasher (ESP32 + S3), capture logger, self-updater
- Linux installer with app menu entry and PATH launchers
- Auto-detect serial port at 115200 baud
- `--mock` mode for dev/demo without hardware
- MIT License

[1.2.0]: https://github.com/LxveAce/headless-marauder-gui/releases/tag/v1.2.0
[1.1.0]: https://github.com/LxveAce/headless-marauder-gui/releases/tag/v1.1.0
[1.0.1]: https://github.com/LxveAce/headless-marauder-gui/releases/tag/v1.0.1
[1.0.0]: https://github.com/LxveAce/headless-marauder-gui/releases/tag/v1.0.0
