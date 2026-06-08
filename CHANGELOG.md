# Changelog

All notable changes to Headless Marauder are documented here.

## [1.2.0] — 2026-06-08

### Added
- **Browser UI** — Flask + SocketIO web interface at `localhost:5000`
  - Full command sidebar (70+ commands, grouped by category)
  - Live serial console via WebSocket (real-time, no polling)
  - Auto-populating Access Points and Stations tables
  - Parameter modals with validation
  - Raw command input with up/down arrow history
  - Auto-list, logging toggle, STOP button
  - Keyboard shortcuts (Ctrl+L, Ctrl+K, Ctrl+.)
  - Dark neon-green theme matching the desktop GUIs
  - `--mock` mode for exploring without hardware
  - `--host 0.0.0.0` option for LAN access
- `headless-marauder-web` launcher (Linux + Windows installers)
- `run-web.sh` / `run-web.bat` dev launchers
- `SECURITY.md` — vulnerability reporting policy
- `DISCLAIMER.md` — legal disclaimer and liability notice
- `CONTRIBUTING.md` — contribution guidelines
- `CHANGELOG.md` — version history

### Changed
- Updated `requirements.txt` with Flask and Flask-SocketIO
- Updated `pyproject.toml` with `[web]` optional dependency group
- Updated installers to include web UI launcher
- Updated `README.md` with Browser UI documentation

## [1.1.0] — 2026-06-08

### Added
- **Windows support** — `install.bat` with venv, PATH, and Start Menu integration
- **Cross-platform pip install** — `pip install git+....[all]`
- `pyproject.toml` with optional dependency groups (`[qt]`, `[tui]`, `[all]`)
- `install.bat` / `uninstall.bat` for Windows
- Comprehensive README with install/update/uninstall for Linux, Windows, macOS, pip

### Changed
- `install.sh` / `uninstall.sh` updated with TUI launcher

## [1.0.1] — 2026-06-08

### Added
- In-app **Guide tab** with full tool reference
- `GUIDE.md` — attack chaining tutorial and other-software integration guide
- Hover tooltips on all command buttons

## [1.0.0] — 2026-06-08

### Added
- Initial release
- **PyQt5 GUI** — live AP/Station tables, target picker, firmware flasher, logging
- **Tkinter GUI** — lightweight alternative
- **Textual TUI** — terminal UI for SSH/headless use
- `marauder_core` shared library — serial controller, 70+ command catalog, stream parser,
  firmware flasher (classic ESP32 + S3), capture logger, self-updater
- Linux installer (`install.sh`) with app menu entry and PATH launchers
- Auto-detect serial port (115200 baud)
- `--mock` mode for development without hardware
- MIT License

[1.2.0]: https://github.com/LxveAce/headless-marauder-gui/releases/tag/v1.2.0
[1.1.0]: https://github.com/LxveAce/headless-marauder-gui/releases/tag/v1.1.0
[1.0.1]: https://github.com/LxveAce/headless-marauder-gui/releases/tag/v1.0.1
[1.0.0]: https://github.com/LxveAce/headless-marauder-gui/releases/tag/v1.0.0
