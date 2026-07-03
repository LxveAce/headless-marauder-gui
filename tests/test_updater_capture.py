"""HMG-MISC beat: resource-safety fixes in marauder_core.

  * updater._run enforces a wall-clock timeout even when the child never closes stdout (HMG-C3);
  * capture.CaptureLogger.start() closes an already-open handle instead of leaking it (HMG-C4).
"""

import sys
import time

from marauder_core import updater
from marauder_core.capture import CaptureLogger


# ── HMG-C3: a stalled child is killed by the watchdog, not waited on forever ──
def test_run_times_out_on_stalled_child():
    lines = []
    # A child that sleeps with its stdout pipe open but never writes/EOFs — the `for ln in p.stdout`
    # read would block indefinitely without the watchdog. timeout=1 -> killed in ~1s, returns -1.
    t0 = time.time()
    rc = updater._run([sys.executable, "-c", "import time; time.sleep(30)"], lines.append, timeout=1)
    elapsed = time.time() - t0
    assert rc == -1
    assert any("timed out" in ln for ln in lines)
    assert elapsed < 15   # killed promptly, did not block for the full 30s sleep


def test_run_returns_rc_on_normal_exit():
    lines = []
    rc = updater._run([sys.executable, "-c", "print('hello'); import sys; sys.exit(0)"],
                      lines.append, timeout=10)
    assert rc == 0
    assert any("hello" in ln for ln in lines)


# ── HMG-C4: start() while already running closes the old file handle first ──
def test_capture_start_twice_closes_old_handle(tmp_path):
    cap = CaptureLogger(str(tmp_path))
    cap.start()
    fp1 = cap._fp
    assert fp1 is not None and not fp1.closed

    cap.start()             # must stop() the prior session first, not leak fp1
    assert fp1.closed
    assert cap._fp is not None and not cap._fp.closed and cap._fp is not fp1
    cap.stop()
