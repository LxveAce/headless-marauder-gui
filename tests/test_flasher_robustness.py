"""Robustness tests for marauder_core/flasher.py:
  * _run_stream kills+reaps the child on a KeyboardInterrupt (BaseException) mid-stream;
  * _run_stream's optional timeout watchdog kills a wedged child.

These mirror the equivalent guards in the sibling universal-flasher / cyber-controller flash engines.
Neither touches the esptool argv assembly or the flash paths' return-code propagation.
"""

import threading

import pytest

flasher = pytest.importorskip("marauder_core.flasher")


def test_run_stream_kills_child_on_keyboard_interrupt(monkeypatch):
    state = {"killed": 0, "closed": False}

    class _Stdout:
        def __iter__(self):
            raise KeyboardInterrupt  # Ctrl-C aborting a slow flash while streaming output
        def close(self):
            state["closed"] = True

    class _Proc:
        returncode = None
        stdout = _Stdout()
        def poll(self):
            return None if state["killed"] == 0 else self.returncode
        def kill(self):
            state["killed"] += 1
            self.returncode = -9
        def wait(self, timeout=None):
            return self.returncode

    monkeypatch.setattr(flasher.subprocess, "Popen", lambda *a, **k: _Proc())
    with pytest.raises(KeyboardInterrupt):
        flasher._run_stream(["dummy", "run"], lambda _s: None)
    assert state["killed"] == 1     # child reaped on the interrupt (the `except Exception` alone would miss it)
    assert state["closed"]


def test_run_stream_timeout_kills_hung_child(monkeypatch):
    state = {"killed": 0}
    released = threading.Event()

    class _Stdout:
        def __iter__(self):
            released.wait(5)   # a wedged child holding the pipe until it's killed
            return iter(())
        def close(self):
            pass

    class _Proc:
        returncode = None
        stdout = _Stdout()
        def poll(self):
            return None if state["killed"] == 0 else self.returncode
        def kill(self):
            state["killed"] += 1
            self.returncode = -9
            released.set()
        def wait(self, timeout=None):
            released.set()
            return self.returncode

    monkeypatch.setattr(flasher.subprocess, "Popen", lambda *a, **k: _Proc())
    rc = flasher._run_stream(["dummy", "run"], lambda _s: None, timeout=0.3)
    assert state["killed"] >= 1     # watchdog fired and killed the wedged child
    assert rc != 0
