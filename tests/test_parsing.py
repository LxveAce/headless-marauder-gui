"""Tests for the serial-stream parser (marauder_core/parsing.py).

Feeds representative Marauder output lines and checks the AP/Station records that drive the
live tables and the target picker.
"""

from marauder_core.parsing import MarauderParser


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
