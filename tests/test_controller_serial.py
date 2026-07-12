"""Serial-layer robustness tests for marauder_core/controller.py (HMG-SERIAL beat):
  * send() surfaces a write timeout instead of hanging the caller thread (HMG-C1);
  * connect() tears down a prior connection first, so it can't leak a handle / double the reader (HMG-C2);
  * the reader buffer is capped so a newline-less stream can't exhaust memory (HMG-B2).
"""

import pytest

serial = pytest.importorskip("serial")

from marauder_core.controller import MarauderController  # noqa: E402
import marauder_core.controller as ctrl_mod  # noqa: E402


# ── HMG-C1: a blocked write is reported, not hung ──────────────────────────
def test_send_reports_write_timeout(monkeypatch):
    ctrl = MarauderController(port="COMX", mock=False)
    lines = []
    ctrl.subscribe(lines.append)

    class _FakeSer:
        def write(self, _b):
            raise serial.SerialTimeoutException("write timed out")

    ctrl.ser = _FakeSer()
    ctrl.send("scanap")   # must return promptly with an error, not block forever
    assert any("timed out" in ln for ln in lines)


# ── send() survives a concurrent disconnect closing/nulling the port ───────
def test_send_survives_port_closed_by_concurrent_disconnect():
    """A disconnect() on another thread can close the port between send()'s check and its write. send()
    must surface that as an error, never let a SerialException escape uncaught onto the send thread."""
    ctrl = MarauderController(port="COMX", mock=False)
    lines = []
    ctrl.subscribe(lines.append)

    class _ClosedSer:
        def write(self, _b):
            raise serial.SerialException("Attempting to use a port that is not open")

    ctrl.ser = _ClosedSer()
    ctrl.send("scanap")   # before the fix, SerialException (not a Timeout) escaped uncaught
    assert any("write failed" in ln for ln in lines)


def test_send_when_port_nulled_is_clean():
    """self.ser nulled by a concurrent disconnect → a clean 'not connected', never None.write."""
    ctrl = MarauderController(port="COMX", mock=False)
    lines = []
    ctrl.subscribe(lines.append)
    ctrl.ser = None
    ctrl.send("scanap")
    assert any("not connected" in ln for ln in lines)


# ── HMG-C2: connect() while connected tears down the old session first ─────
def test_connect_while_connected_disconnects_first(monkeypatch):
    ctrl = MarauderController(mock=True)
    ctrl.connect()                      # mock connect → _running=True
    assert ctrl._running

    calls = {"n": 0}
    real_disconnect = ctrl.disconnect

    def spy():
        calls["n"] += 1
        real_disconnect()

    monkeypatch.setattr(ctrl, "disconnect", spy)
    ctrl.connect()                      # the guard must tear the old one down first
    assert calls["n"] == 1
    ctrl.disconnect()


# ── HMG-B2: a newline-less flood is flushed, not accumulated forever ───────
def test_read_loop_caps_unbounded_buffer():
    ctrl = MarauderController(mock=False)
    emitted = []
    ctrl.subscribe(emitted.append)

    state = {"served": False}

    class _FakeSer:
        def read(self, _n):
            if not state["served"]:
                state["served"] = True
                return b"A" * (70 * 1024)   # > _MAX_LINE_BYTES, no newline
            ctrl._running = False           # stop the loop on the next pass
            return b""

    ctrl.ser = _FakeSer()
    ctrl._running = True
    ctrl._read_loop()                       # runs synchronously here until _running is cleared

    # the oversized partial line was flushed once (buffer reset), not grown without bound
    assert any(len(e) >= ctrl_mod._MAX_LINE_BYTES for e in emitted)


# ── the reader thread dying (board unplugged) must stop reporting 'connected' ──
def test_reader_death_clears_connected():
    """When _read_loop breaks on a serial read error (board yanked mid-session), it must clear
    _running so `connected` reports False. Before the fix it stayed True with the dead handle, so
    every front-end showed 'connected: COMx' while no serial input was ever processed again."""
    ctrl = MarauderController(port="COMX", mock=False)
    emitted = []
    ctrl.subscribe(emitted.append)

    class _DyingSer:
        def read(self, _n):
            raise serial.SerialException("device reports readiness to read but returned no data")

    ctrl.ser = _DyingSer()
    ctrl._running = True
    assert ctrl.connected is True
    ctrl._read_loop()                 # runs synchronously; the read raises → loop exits
    assert ctrl._running is False
    assert ctrl.connected is False    # the crux: no longer lies 'connected' after the reader dies
    assert any("serial error" in ln for ln in emitted)
