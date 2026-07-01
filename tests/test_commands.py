"""Tests for the shared command catalog (marauder_core/commands.py).

Pure, hardware-free: exercises the command-string builder and the catalog invariants
that every front-end relies on.
"""

from marauder_core import commands


def test_build_base_only():
    cmd = commands.get("scanap")
    assert cmd is not None
    assert commands.build(cmd) == "scanap"


def test_build_appends_value_flag():
    cmd = commands.get("join")  # base "join", -a index, -p password
    out = commands.build(cmd, {"index": 0, "password": "hunter2"})
    assert out == "join -a 0 -p hunter2"


def test_build_skips_blank_values():
    cmd = commands.get("join")
    # password omitted -> only the AP index is appended
    assert commands.build(cmd, {"index": 3}) == "join -a 3"


def test_build_bool_flag_only_when_true():
    cmd = commands.get("wardrive")  # has a -s bool "silent"
    assert commands.build(cmd, {"silent": True}) == "wardrive -s"
    assert commands.build(cmd, {"silent": False}) == "wardrive"
    assert commands.build(cmd) == "wardrive"


def test_build_positional_value_no_flag():
    cmd = commands.get("select_ap")  # base "select -a", positional index
    assert commands.build(cmd, {"index": "0,2,5"}) == "select -a 0,2,5"


def test_catalog_has_seventy_commands():
    # The README and docs advertise the exact count; lock it so drift is caught.
    assert len(commands.COMMANDS) == 70


def test_command_ids_are_unique():
    ids = [c.id for c in commands.COMMANDS]
    assert len(ids) == len(set(ids))


def test_categories_present_and_ordered():
    cats = commands.categories()
    # Channel was historically missing from the README table; keep it pinned.
    assert "Channel" in cats
    assert len(cats) == 11
    # first-seen order is preserved
    assert cats[0] == "WiFi · Scan"


def test_to_dict_covers_every_command():
    grouped = commands.to_dict()
    total = sum(len(group["commands"]) for group in grouped)
    assert total == len(commands.COMMANDS)
    assert {g["category"] for g in grouped} == set(commands.categories())
