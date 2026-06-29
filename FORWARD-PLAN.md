# headless-marauder-gui - Forward Plan

> Status: production-stable, public, shipping. Health: GREEN. Latest release v1.3.2 (2026-06-11); main is 7 commits ahead. All Python modules compile; no open issues. | Date: ____________

> **CONTEXT (2026-06-29):** the flasher line is consolidating onto ONE shared flashing engine (extracted
> from Cyber Controller's flash core into the universal-flasher repo; Cyber Controller consumes it as a
> dependency). HMG is the lineage ancestor of that engine — the dig-deeper "diff `marauder_core/flasher.py`
> vs cc flash_core" / "diff `marauder_core/` vs `uf_core/`" items below are informational input to that
> consolidation, not standalone work. HMG itself stays as the Marauder-only standalone app.

## Where this stands

**What it is.** headless-marauder-gui (HMG, owner LxveAce, MIT) is the original/foundational Python app of the Lxve ESP32 security toolchain: a native controller + multi-firmware flasher for headless ESP32 Marauder boards. A shared core (`marauder_core/`: serial controller, ~70-command catalog, parser, flasher, capture logger, self-updater) drives **four front-ends**: PyQt5 desktop (`gui_qt/app.py`, the primary + PyInstaller build entry), Tkinter (`gui/app.py`), Textual TUI (`tui/app.py`), and Flask+SocketIO web UI (`web/app.py`, binds 127.0.0.1:5000). A `suicide/` package provides the Suicide-Marauder bundle provisioner plus vendored firmware/docs.

**Build / run.**
- Deps: `requirements.txt` + `pyproject.toml` (setuptools). Runtime: pyserial, esptool (pinned `>=4.7,<6`). Extras: `qt`, `tui`, `web`, `all`.
- Console scripts: `headless-marauder-tk`, `-tui`, `-web` (NO Qt entry; README says run Qt via `python -m gui_qt.app` from a clone).
- Standalone binaries: `build.py` (PyInstaller, entry `gui_qt/app.py`); `.github/workflows/build-release.yml` builds Windows / Linux-x64 / Linux-arm64 / macOS-arm64 on each published release and uploads assets.
- Self-update: `git pull --ff-only` when installed from a clone.

**Current state.** Development Status :: 5 - Production/Stable. 5 releases (v1.1.0 .. v1.3.2). All 14 Python modules compile cleanly; no open GitHub issues; no TODO/FIXME markers. v1.3.2's 4 release assets are verified-present (PE/ELF magic + sha256, state=uploaded). The live site esp32marauder.com is up and fetches the latest release dynamically. The issues below are version/packaging/docs hygiene, not verified functional breakage.

## P0 - do first

1. **Sync version strings + adopt one source of truth.** `marauder_core/__init__.py:4` is `1.2.0`, `pyproject.toml:7` is `1.3.1`, latest release is `v1.3.2` — three different values, and the stale one renders in the Qt status bar/About dialog and the web UI. Bump both to the next tag, and ideally derive `__version__` from `importlib.metadata` so this cannot drift again.
2. **Fix the broken pip install command** at `README.md:197`. `pip install git+https://...git[all]` silently drops the `[all]` extras (pip treats them as part of the URL; pypa/pip #8576, #6598). Replace with the PEP 508 form: `pip install "headless-marauder[all] @ git+https://github.com/LxveAce/headless-marauder-gui.git"`.
3. **Cut a new release (v1.3.3+).** main is 7 commits ahead of v1.3.2 (compare ahead 7 / behind 0; main HEAD `f921ca5`, 2026-06-17), so shipping binaries miss the suicide/forensic-wipe build fixes, 4MB guardcfg NVS fix, CYD touch build define fix, and PII scrub. CI auto-builds the 4 platforms on publish. (Do P0-1 first so the new tag ships correct version strings.)

> Note: there is no separate `.exe`/installer breakage to fix here — HMG's binaries download and serve correct bytes; the only "stale binary" issue is the unreleased-commits gap above. (The cyber-controller installer concern in the section template does not apply to this repo.)

## Surface bugs found

| Title | Location | Severity | Note |
|---|---|---|---|
| Stale `__version__` (1.2.0) user-visible, lags pyproject (1.3.1) & release (v1.3.2) | `marauder_core/__init__.py:4` (shown at `gui_qt/app.py:1142,1158`; `web/app.py:80,101,494`) | P2 | Wrong version in status bar, About dialog, web UI |
| Documented pip install command malformed — `[all]` extras silently dropped | `README.md:197` | P2 | Users get base package, no error; use PEP 508 form |
| Latest release (v1.3.2) lags main by 7 commits | compare `v1.3.2...main` (ahead 7); main HEAD `f921ca5` 2026-06-17 | P3 | Binaries predate recent fixes; fixed by cutting a release |
| CHANGELOG missing 1.3.1 & 1.3.2 entries | `CHANGELOG.md` (top entry `[1.3.0]`) | P3 | Stale by two releases (three after next tag) |
| No `[project.scripts]` entry for PyQt5 GUI | `pyproject.toml:47-50`; `gui_qt/app.py:1235` `main()` | P3 | README:200 documents `python -m gui_qt.app` instead; decide add-entry vs keep-docs |
| `esp-idf-nvs-partition-gen` in requirements.txt but not pyproject deps | `requirements.txt:11` vs `pyproject.toml:31-40` | P3 | `pip install` skips the suicide provisioner dep; runtime fallback in `provision.py:351-376` |
| PyQt5 imported with no guard in primary GUI | `gui_qt/app.py:23-25` (cf. guarded pyserial `controller.py:14-19`) | P3 | Missing dep → raw traceback instead of friendly install hint |

## Features to add

- **User directives:** none were provided for this plan — nothing to record verbatim.
- **PyQt5 GUI launch entry.** Add a `[project.scripts]` entry (e.g. `headless-marauder = gui_qt.app:main`) so pip users can launch the recommended front-end, while respecting README:200's note that Qt entry points are finicky with pip. If keeping the module-run path, make sure docs stay accurate.
- **Declare the suicide dependency.** Add a `[project.optional-dependencies]` `suicide` group with `esp-idf-nvs-partition-gen==0.2.0`.
- **Single-source versioning.** Derive `__version__` from `importlib.metadata` (folds into P0-1).
- **Reconcile suicide vs Dead Man's Switch.** HMG's README + `suicide/` still target Suicide-Marauder, which is officially succeeded by `deadmans-switch` (firmware-agnostic; Guardian/Fork variants; `SM_*` serial commands). Decide whether HMG's flash path should track `deadmans-switch` or stay pinned to the vendored bundle.

## Red-team / hardening

- **Preserve flasher SSRF posture** (`flasher.py:57-120`: https-only + GitHub host allowlist + redirect-blocking opener). Re-verify the redirect block after any download-path edits; do not loosen the allowlist.
- **Keep web UI bound to 127.0.0.1** (`web/app.py:474`). Any LAN-exposed mode must be opt-in behind an explicit flag + warning, never default.
- **Preserve updater safety** (`updater.py`: `GIT_TERMINAL_PROMPT=0`, BatchMode ssh, `git pull --ff-only`).
- **Back-port the cyber-controller flasher audit checklist.** cyber-controller's `src/core/flash_core.py` documents fixes HMG may lack: per-chip bootloader offsets incl. the **ESP32-C5 0x2000** gotcha, chip auto-detect via `esptool chip_id` (never hardcoded), and suicide `bundle.json` SHA256 + TOCTOU-safe staging. cyber-controller closed a 10-finding audit (v1.1.0, 2026-06-12) — treat it as HMG's hardening checklist. (PUBLIC repo: track as hardening tasks, no exploit detail.)
- **Guard the PyQt5 import** (`gui_qt/app.py:23-25`) for clean failure UX (minor).

## Dig deeper (next dedicated session)

1. **Diff `marauder_core/flasher.py` vs cyber-controller `src/core/flash_core.py`** to determine exactly which hardening fixes HMG already has vs lacks (C-5 offset, chip auto-detect, SHA256/TOCTOU). Highest-value deep dive — recon read CC's header but did not diff.
2. **Diff HMG `marauder_core/` vs universal-flasher `uf_core/`** to see if the cores are in deliberate sync or have silently diverged.
3. **Runtime verification.** Nothing was executed in recon. Run each front-end with `--mock`, exercise the flasher download path against the allowlist, and smoke-test a PyInstaller build from `build.py`.
4. **Audit the under-inspected modules:** `tui/app.py`, `gui/app.py`, `web/templates/index.html`, and the `suicide/` firmware C++/docs — recon focused on entry points/manifests/CI/core.
5. **Verify the "70 commands" claim** against `marauder_core/commands.py` by counting; reconcile mismatches.
6. **Confirm the cyberdeck-kit mirror policy.** HMG is mirrored byte-for-byte at `Projects/projects/14-cyberdeck/integrations/01-esp32-marauder/headless-marauder-gui/`. Decide whether every HMG change must be re-mirrored, or retire the mirror in favor of consuming published releases.
7. **Check for existing migration PRs** (not just issues) before doing deadmans-switch branding work.

## Dependencies & cross-repo context

- **Runtime (pyproject):** pyserial>=3.5, esptool>=4.7,<6 (deliberate `<6` pin — v6 removes aliases the app uses). Extras: qt / tui / web / all.
- **Gap:** `esp-idf-nvs-partition-gen==0.2.0` is in `requirements.txt:11` only — add it to a pyproject `suicide` extra.
- **CI:** `build-release.yml` builds 4 platforms on release publish; v1.3.2 shipped 4 verified assets.
- **Self-update:** `updater.py` pulls `--ff-only` from the authoritative GitHub repo.
- **Lineage (verified):** HMG is the ORIGINAL repo. Downstream: `universal-flasher` (`uf_core`, "built on the HMG scaffold"), `universal-flasher-ui` (frozen snapshot), and **`cyber-controller`** — the "flagship convergence" successor (HMG + universal-flasher + universal-flasher-ui + Dead Man's Switch; 21 firmware profiles / 5 backends / 9 protocol parsers; re-architected into `src/core` + `src/protocols`, did NOT vendor `marauder_core`). **Before adding multi-firmware/multi-device features to HMG, check whether the successor repos already solved it** to avoid duplicated effort.
- **Branding chain:** `suicide/` provisioner → Suicide-Marauder repo → SUCCEEDED by `deadmans-switch` (firmware-agnostic; embedded as a cyber-controller git submodule).
- **Distribution:** esp32marauder.com is up and fetches the latest release dynamically (no hardcoded version → won't go stale).
- **Path note:** authoritative working clones are under `<HOME>/repos` and `<HOME>/Projects`; `CLAUDE-TRANSFER.md` still references an older machine path (`<HOME>/...`).

## Open questions

- Does HMG's `flasher.py` already contain the cyber-controller hardening (ESP32-C5 0x2000, chip auto-detect, SHA256/TOCTOU), or does it lag? Not diffed.
- Are `marauder_core` and `uf_core` kept in deliberate sync, or have they diverged? Not diffed cross-repo.
- Do the published binaries actually launch/run? Only PE/ELF magic + byte transfer verified, not execution.
- Should HMG's flash path migrate to `deadmans-switch` or stay pinned to the vendored Suicide-Marauder bundle? Product decision.
- Is the byte-identical cyberdeck-kit mirror still an active must-re-mirror policy, or can it be retired?
- Does the README "70 commands" claim match `commands.py` exactly? Not counted.
- Exact pip-extras-drop behavior varies by pip version (silently ignored on modern pip per cited issues) — not tested live across versions.
- Any open PRs proposing the deadmans-switch migration / downstream back-ports? Issues were empty; PRs not enumerated.