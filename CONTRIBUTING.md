# Contributing to Headless Marauder

Contributions are welcome — bug reports, feature requests, code, documentation, and testing.

## Getting Started

1. Fork the repo and clone your fork
2. Create a venv and install dev dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate        # Linux/macOS
   # .venv\Scripts\activate         # Windows
   pip install -r requirements.txt
   pip install PyQt5
   ```
3. Run with `--mock` to develop without hardware:
   ```bash
   python gui_qt/app.py --mock
   python tui/app.py --mock
   python web/app.py --mock
   ```

## Reporting Bugs

Open a [GitHub issue](https://github.com/LxveAce/headless-marauder-gui/issues) with:

- OS and Python version
- Steps to reproduce
- Expected vs actual behavior
- Console output / tracebacks if applicable
- Board type (classic ESP32, S3, etc.) if hardware-related

## Submitting Changes

1. Create a feature branch from `main`
2. Keep commits focused — one logical change per commit
3. Test all four UIs if your change touches `marauder_core/` (Qt, Tkinter, TUI, Web)
4. Update `GUIDE.md` if you add or change commands
5. Open a PR against `main` with a clear description of what and why

## Code Style

- Python 3.9+ compatible
- No type stubs required, but type hints are welcome
- Follow existing patterns — the codebase is intentionally straightforward
- No unnecessary abstractions or over-engineering
- Keep dependencies minimal — don't add a package for something the stdlib handles

## Adding Commands

New Marauder commands go in `marauder_core/commands.py`. Add a `Command(...)` entry to
the appropriate category in `build()`. All four UIs pick it up automatically — the
command catalog is the single source of truth.

## Architecture

```
marauder_core/     Shared library — controller, parser, commands, flasher, capture, updater
gui_qt/            PyQt5 GUI (recommended desktop UI)
gui/               Tkinter GUI (lightweight alternative)
tui/               Textual terminal UI
web/               Flask + SocketIO browser UI
```

All four front-ends import from `marauder_core` and follow the same pattern: connect,
subscribe to serial events, render output, send commands. If you're adding a feature
to the core, it should work across all UIs. If it's UI-specific, keep it in that UI's
directory.

## Security Vulnerabilities

Do **not** open a public issue for security vulnerabilities. See [SECURITY.md](SECURITY.md)
for responsible disclosure instructions.

## License

By contributing, you agree that your contributions will be licensed under the
[MIT License](LICENSE).
