"""Frozen-binary esptool trampoline (marauder_core/flasher.py).

In a PyInstaller build `sys.executable` is the app exe, so `python -m esptool` re-launches the GUI and
esptool never runs — breaking every flash/erase/detect path in the shipped binary. esptool_argv() re-execs
the exe with a sentinel that run_esptool_entrypoint() intercepts at startup. These tests cover both without
needing a frozen build or hardware.
"""

import sys

import pytest

from marauder_core import flasher


def test_esptool_argv_normal_uses_python_m_esptool(monkeypatch):
    monkeypatch.delattr(sys, "frozen", raising=False)   # a normal (non-frozen) interpreter
    assert flasher.esptool_argv("version") == [sys.executable, "-m", "esptool", "version"]


def test_esptool_argv_frozen_uses_sentinel(monkeypatch):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    assert flasher.esptool_argv("write-flash", "0x0", "fw.bin") == [
        sys.executable, flasher._ESPTOOL_SENTINEL, "write-flash", "0x0", "fw.bin",
    ]


def test_run_esptool_entrypoint_noop_without_sentinel():
    # A normal launch (no sentinel as argv[1]) must be a no-op so the app proceeds to start the GUI.
    assert flasher.run_esptool_entrypoint(["hmg.exe", "--port", "COM3"]) is False
    assert flasher.run_esptool_entrypoint(["hmg.exe"]) is False


def test_run_esptool_entrypoint_dispatches_on_sentinel(monkeypatch):
    # With the sentinel present it must hand the remaining args to esptool's CLI and exit with its status,
    # presenting esptool a clean argv (program name + args, sentinel dropped).
    import esptool
    called = {}

    def fake_main():
        called["argv"] = list(sys.argv)
        return 0

    monkeypatch.setattr(esptool, "_main", fake_main, raising=False)
    saved_argv = sys.argv[:]
    try:
        with pytest.raises(SystemExit) as ei:
            flasher.run_esptool_entrypoint(["hmg.exe", flasher._ESPTOOL_SENTINEL, "version"])
        assert ei.value.code == 0
        assert called.get("argv") == ["hmg.exe", "version"]   # sentinel stripped, real esptool argv
    finally:
        sys.argv = saved_argv
