"""Regression guards for the hmg-deep-audit-1 batch (2026-07-14).

First deep multi-agent audit of headless-marauder-gui (10 finders -> 3-lens adversarial verify).
Five confirmed leads, each re-confirmed against the real code and fixed this beat:

#1 (HIGH) parsing.MarauderParser.feed  — `_list_kind_of` ran on EVERY line, so an AP whose SSID
   contains "list -c" flipped AP/station routing for that row + the rest of the dump (index-based
   select/deauth then hits the wrong entity). Fix: detect the list kind only from echoed command
   lines (non-`_LIST_RE` rows). Twin of universal-flasher #5.
#8 (MED)  parsing._SCAN_RE            — the ESSID capture truncated at the FIRST embedded
   " Beacon: <n>". Fix: anchor the trailing-stat strip so the number must be the final token. uf #8.
#4 (MED)  web/app.on_connect_serial    — re-opened the serial port with no `_flash_busy` guard, so a
   2nd tab could collide with an in-progress esptool flash. Fix: refuse while a flash owns the port.
   Twin of uf #4.
#2 (MED, SAFETY) suicide.provision.validate_password — never rejected an embedded NUL byte; the
   firmware stores the secret in a char[64] C-string and truncates at the NUL, so host/device hash
   different bytes -> on an ARMED board the owner's correct password self-wipes the board. Fix: reject
   a NUL byte. Same self-wipe-parity class as uf #2.
#11 (LOW) updater.update               — `git config --global --add safe.directory` ran on EVERY
   update(), and `--add` appends, so duplicate entries piled up in the user's global gitconfig. Fix:
   only add when the entry (or the catch-all `*`) isn't already present.

Hardware-free: pure parser/validator logic + monkeypatched module globals; no device/network/subprocess.
"""
import pytest


# ── #1: list-kind routing is set only by echoed command lines, not attacker data rows ──

def test_list_kind_not_flipped_by_data_row_named_list_c():
    from marauder_core.parsing import MarauderParser

    p = MarauderParser()
    p.feed(">> list -a")                          # echoed command -> route rows to APs
    assert p._list_kind == "ap"
    # a malicious AP whose NAME contains "list -c" arrives as an indexed DATA ROW; it must NOT flip
    # routing to stations (the bug misrouted this row + every subsequent row in the dump).
    kind, _rec = p.feed("[0][CH:6] list -c cafe -55")
    assert p._list_kind == "ap"                   # routing unchanged
    assert kind == "ap"                           # the row itself stored as an AP, not a station


def test_list_kind_still_set_from_echoed_command():
    from marauder_core.parsing import MarauderParser

    p = MarauderParser()
    p.feed("> #list -c")                          # the device's echoed command line
    assert p._list_kind == "sta"


# ── #8: an SSID containing "Beacon: <digit>" mid-string is preserved; a trailing stat is stripped ──

def test_scanap_ssid_with_embedded_beacon_is_not_truncated():
    from marauder_core.parsing import MarauderParser

    p = MarauderParser()
    kind, ap = p.feed("RSSI: -57 Ch: 3 BSSID: 50:ff:20:84:d6:0f ESSID: xfinity Beacon: 5 area")
    assert kind == "ap"
    assert ap.ssid == "xfinity Beacon: 5 area"    # embedded "Beacon: 5" is NOT a trailing stat


def test_scanap_trailing_beacon_stat_is_stripped():
    from marauder_core.parsing import MarauderParser

    p = MarauderParser()
    kind, ap = p.feed("RSSI: -60 Ch: 1 BSSID: aa:bb:cc:dd:ee:ff ESSID: HomeNet Beacon: 42")
    assert ap.ssid == "HomeNet"                   # a genuine trailing "Beacon: <n>" stat IS stripped


# ── #4: connect_serial refuses while a flash/erase owns the shared port ──

def test_connect_serial_refused_while_flash_busy(monkeypatch):
    webapp = pytest.importorskip("web.app")
    events = []
    monkeypatch.setattr(webapp, "emit", lambda *a, **k: events.append(a))
    monkeypatch.setattr(webapp, "ctrl", None)
    made = {"ctrl": False}

    class Boom:
        def __init__(self, *a, **k):
            made["ctrl"] = True

    monkeypatch.setattr(webapp, "MarauderController", Boom)
    webapp._flash_busy = True
    try:
        webapp.on_connect_serial({"port": "COM7"})
    finally:
        webapp._flash_busy = False

    assert made["ctrl"] is False                  # must NOT open a session while a flash owns the port
    assert events and events[-1][0] == "status" and events[-1][1].get("connected") is False


# ── #2: validate_password rejects an embedded NUL byte (firmware C-string truncation) ──

def test_validate_password_rejects_embedded_nul():
    from suicide import provision

    with pytest.raises(provision.ProvisionError):
        provision.validate_password(b"good\x00pass")


def test_validate_password_accepts_clean_password():
    from suicide import provision

    # a clean password must still pass (guard against over-rejection of legitimate secrets)
    assert provision.validate_password(b"goodpass") is None


# ── #11: update() does not append a duplicate safe.directory entry when one already exists ──

def test_safe_directory_present_detects_existing_entry(monkeypatch):
    from marauder_core import updater

    class _R:
        stdout = "/home/u/repo\n/other/path\n"

    monkeypatch.setattr(updater.subprocess, "run", lambda *a, **k: _R())
    assert updater._safe_directory_present("/home/u/repo") is True
    assert updater._safe_directory_present("/not/listed") is False


def test_safe_directory_present_honors_wildcard(monkeypatch):
    from marauder_core import updater

    class _R:
        stdout = "*\n"

    monkeypatch.setattr(updater.subprocess, "run", lambda *a, **k: _R())
    assert updater._safe_directory_present("/any/repo") is True


def test_update_skips_safe_directory_add_when_present(monkeypatch):
    from marauder_core import updater

    calls = []
    monkeypatch.setattr(updater, "is_git_checkout", lambda: True)
    monkeypatch.setattr(updater, "repo_root", lambda: "/home/u/repo")
    monkeypatch.setattr(updater, "current_revision", lambda: "abc123")

    class _R:
        stdout = "/home/u/repo\n"                 # entry already present

    monkeypatch.setattr(updater.subprocess, "run", lambda *a, **k: _R())

    def fake_run(argv, on_line, env=None, timeout=180):
        calls.append(argv)
        return 1                                  # git pull "fails" -> update() aborts after config

    monkeypatch.setattr(updater, "_run", fake_run)
    updater.update(lambda *_a: None)

    add_calls = [c for c in calls if "--add" in c and "safe.directory" in c]
    assert add_calls == []                        # no duplicate add when the entry already exists
