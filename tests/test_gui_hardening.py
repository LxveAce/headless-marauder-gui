"""Batch HMG-3 GUI-hardening regressions (from an adversarial audit):

 * flasher.esptool_available is memoised — it was a fresh ~1-3s subprocess spawn on *every* flasher
   open (both GUIs + the TUI call it), needlessly re-probing.
 * The Qt flasher probes esptool OFF the GUI thread — the blocking subprocess used to run in
   FlasherDialog.__init__, freezing the whole app while the dialog opened.
 * The Qt main console is bounded (maximumBlockCount) — it was unbounded while the AP/Station tables
   were already capped, so a device streaming lines without limit grew it forever.

The Tk surface gets the same three fixes plus a mid-flash close-guard; those are verified by
inspection (mirroring the Qt code) since the repo doesn't spin a Tk root in CI.
"""

import os
import threading

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

from marauder_core import flasher


# ── flasher.esptool_available is memoised ──────────────────────────────────────────────────────
def test_esptool_available_is_memoised(monkeypatch):
    calls = {"n": 0}

    class _R:
        returncode = 0

    def fake_run(*a, **k):
        calls["n"] += 1
        return _R()

    flasher.esptool_available.cache_clear()
    monkeypatch.setattr(flasher.subprocess, "run", fake_run)
    try:
        assert flasher.esptool_available() is True
        assert flasher.esptool_available() is True
        assert calls["n"] == 1              # the subprocess probe ran exactly once, not per-call
    finally:
        flasher.esptool_available.cache_clear()   # leave a clean cache for other tests


# ── Qt widget-level regressions (offscreen) ────────────────────────────────────────────────────
pytest.importorskip("PyQt5.QtWidgets")


@pytest.fixture(scope="module")
def qapp():
    from PyQt5.QtWidgets import QApplication
    return QApplication.instance() or QApplication([])


def _mock_controller():
    from marauder_core.controller import MarauderController
    return MarauderController(mock=True)


def test_qt_console_is_bounded(qapp):
    from gui_qt.app import MainWindow

    w = MainWindow(_mock_controller())
    assert w.console.maximumBlockCount() == 5000   # was 0 (QPlainTextEdit default = unlimited)


def test_qt_flasher_probes_esptool_off_the_gui_thread(qapp, monkeypatch):
    from gui_qt.app import FlasherDialog, MainWindow

    main_ident = threading.get_ident()
    seen = {}
    done = threading.Event()

    def spy():
        seen["ident"] = threading.get_ident()
        done.set()
        return True

    flasher.esptool_available.cache_clear()
    monkeypatch.setattr(flasher, "esptool_available", spy)

    w = MainWindow(_mock_controller())
    FlasherDialog(w, _mock_controller())           # __init__ must return without blocking on the probe
    assert done.wait(5), "the esptool probe never ran"
    assert seen["ident"] != main_ident             # it ran on a worker thread, not the GUI thread
