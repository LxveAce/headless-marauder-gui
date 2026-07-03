"""HMG-B3: commands.build() validates int / choices / required (defense for the untrusted web path).

The GUIs pre-validate in their param dialogs; the web front-end passes client values straight into
build(), so build() must refuse a non-integer int, an out-of-catalog choice, or a missing required
param instead of emitting an incomplete/garbage command. The happy path must be byte-identical.
"""

import pytest

from marauder_core import commands
from marauder_core.commands import Command, Param, build


# ── invalid input is rejected ─────────────────────────────────────────────
def test_int_param_rejects_non_integer():
    cmd = Command("t", "t", "channel -s", params=[Param("channel", "", "int", required=True)])
    with pytest.raises(ValueError):
        build(cmd, {"channel": "abc"})


def test_choice_param_rejects_value_not_in_choices():
    cmd = Command("t", "t", "gps -g",
                  params=[Param("field", "", "select", required=True, choices=["fix", "sat", "lat"])])
    with pytest.raises(ValueError):
        build(cmd, {"field": "rm -rf"})


def test_missing_required_param_raises():
    cmd = Command("t", "t", "join", params=[Param("index", "-a", "int", required=True)])
    with pytest.raises(ValueError):
        build(cmd, {})               # required index absent -> refuse, don't emit "join"


# ── valid input still builds exactly as before ────────────────────────────
def test_valid_int_and_choice_build_unchanged():
    cmd = Command("t", "t", "gps -g",
                  params=[Param("field", "", "select", required=True, choices=["fix", "sat"])])
    assert build(cmd, {"field": "fix"}) == "gps -g fix"

    cmd2 = Command("t", "t", "channel -s", params=[Param("channel", "", "int", required=True)])
    assert build(cmd2, {"channel": "6"}) == "channel -s 6"
    assert build(cmd2, {"channel": 6}) == "channel -s 6"   # already-int (from a GUI spinbox) is fine


def test_optional_missing_is_still_skipped():
    # a NON-required param left blank is dropped, exactly as before (no raise)
    cmd = commands.get("info")            # info has an optional -a index
    assert cmd is not None
    assert build(cmd, {}) == "info"


def test_bool_and_text_params_unaffected():
    cmd = Command("t", "t", "wardrive", params=[Param("silent", "-s", "bool")])
    assert build(cmd, {"silent": True}) == "wardrive -s"
    assert build(cmd, {"silent": False}) == "wardrive"
    cmd2 = Command("t", "t", "ssid -a -n", params=[Param("name", "", "text", required=True)])
    assert build(cmd2, {"name": "Free_WiFi"}) == "ssid -a -n Free_WiFi"
