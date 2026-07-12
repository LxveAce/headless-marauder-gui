"""Tests for the serial-stream parser (marauder_core/parsing.py).

Feeds representative Marauder output lines and checks the AP/Station records that drive the
live tables and the target picker.
"""

import sys
import threading

from marauder_core.parsing import AP, MarauderParser, Station


def test_scanap_stream_line():
    p = MarauderParser()
    kind, rec = p.feed(
        "RSSI: -57 Ch: 3 BSSID: 50:ff:20:84:d6:0f ESSID: Octoglass Beacon: 100"
    )
    assert kind == "ap"
    assert rec.ssid == "Octoglass"
    assert rec.channel == "3"
    assert rec.rssi == "-57"
    assert rec.bssid == "50:ff:20:84:d6:0f"


def test_list_ap_dump_indexes():
    p = MarauderParser()
    p.feed(">> list -a")
    kind, rec = p.feed("[0][CH:5] SpectrumSetup-B566 -54")
    assert kind == "ap"
    assert rec.index == 0
    assert rec.ssid == "SpectrumSetup-B566"
    assert rec.channel == "5"
    assert rec.rssi == "-54"
    assert p.indexed_aps()[0].ssid == "SpectrumSetup-B566"


def test_list_command_routes_stations():
    p = MarauderParser()
    p.feed(">> list -c")   # switch the active list kind to stations
    kind, rec = p.feed("[0][CH:6] aa:bb:cc:dd:ee:ff -40")
    assert kind == "sta"
    assert rec.index == 0
    assert rec.mac == "aa:bb:cc:dd:ee:ff"
    assert p.aps == {}          # nothing leaked into the AP table


def test_ssid_list_not_tabled():
    p = MarauderParser()
    p.feed(">> list -s")
    result = p.feed("[0][CH:1] MySSID -10")
    assert result == (None, None)


def test_tag_lines_ignored():
    p = MarauderParser()
    assert p.feed(">> some echo") == (None, None)
    assert p.feed("$ prompt") == (None, None)
    assert p.feed("") == (None, None)


def test_index_zero_resets_ap_table():
    p = MarauderParser()
    p.feed(">> list -a")
    p.feed("[0][CH:1] First -50")
    p.feed("[1][CH:2] Second -60")
    assert len(p.aps) == 2
    # a fresh dump starting at index 0 clears the stale table
    p.feed("[0][CH:3] Fresh -55")
    assert len(p.aps) == 1
    assert p.aps[0].ssid == "Fresh"


def test_hidden_ssid_placeholder():
    p = MarauderParser()
    p.feed(">> list -a")
    _, rec = p.feed("[0][CH:5]  -54")
    assert rec.ssid == "<hidden>"


# ── indexed accessors keep index order after the values()-snapshot change ─────
def test_indexed_aps_ordered_by_index():
    p = MarauderParser()
    p.feed(">> list -a")
    p.feed("[0][CH:1] First -50")       # idx 0 resets the (empty) table first
    p.feed("[2][CH:1] Third -70")       # then insert out of index order
    p.feed("[1][CH:1] Second -60")
    assert list(p.aps) == [0, 2, 1]                    # dict insertion order is NOT sorted
    assert [a.ssid for a in p.indexed_aps()] == ["First", "Second", "Third"]


# ── the accessors must not race the reader thread (web front-end) ─────────────
def test_indexed_accessors_survive_concurrent_reader_mutation():
    """Regression: indexed_aps/indexed_stations used key-then-index (`[self.aps[i] for i in
    sorted(self.aps)]`), which raises KeyError when the controller reader thread clears/repopulates
    the dict mid-iteration — in the web front-end feed() runs on the reader thread while the
    _table_pusher thread reads the accessors, so a transient KeyError silently killed the live-table
    loop. The values()-snapshot form must never raise under the same race."""
    p = MarauderParser()
    errors: list = []
    stop = threading.Event()

    def writer():
        i = 0
        while not stop.is_set():
            if i % 8 == 0:                 # mimic the idx==0 table reset on every fresh dump
                p.aps.clear()
                p.stations.clear()
            k = i % 8
            p.aps[k] = AP(index=k, ssid="x", channel="1", rssi="-50")
            p.stations[k] = Station(index=k, mac="aa:bb:cc:dd:ee:ff", rssi="-50")
            i += 1

    old_interval = sys.getswitchinterval()
    sys.setswitchinterval(1e-6)            # force frequent thread switches to expose the race
    t = threading.Thread(target=writer, daemon=True)
    t.start()
    try:
        for _ in range(20000):
            try:
                p.indexed_aps()
                p.indexed_stations()
                p.ap_rows()
                p.station_rows()
            except Exception as exc:       # the bug surfaced as KeyError here
                errors.append(exc)
                break
    finally:
        stop.set()
        t.join(timeout=2)
        sys.setswitchinterval(old_interval)

    assert not errors, f"indexed accessor raced the reader thread: {errors[:3]!r}"
