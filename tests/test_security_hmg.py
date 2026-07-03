"""Security regression tests for the HMG-WEB-SECURITY beat:
  * serial-command injection is neutralized in commands.build() + refused in controller.send() (HMG-B1);
  * the web Socket.IO CORS allowlist is pinned to same-origin, not "*" (HMG-D1).
"""

import pytest

from marauder_core import commands


# ── HMG-B1: CR/LF / control-char injection is neutralized ──────────────────
def test_sanitize_value_replaces_control_chars_with_space():
    assert commands._sanitize_value("Free_WiFi\nreboot") == "Free_WiFi reboot"
    assert commands._sanitize_value("a\rb\tc") == "a b c"
    assert "\n" not in commands._sanitize_value("x\ny")
    assert "\r" not in commands._sanitize_value("x\r\ny")
    assert commands._sanitize_value("café-über") == "café-über"  # non-ASCII preserved


def test_build_neutralizes_newline_injection():
    # A password value carrying a newline must NOT split into a second device command.
    out = commands.build(commands.get("join"), {"index": 0, "password": "hunter2\nreboot"})
    assert "\n" not in out and "\r" not in out
    # the whole thing stays on one line — "reboot" can only be an argument, never its own command
    assert out.count("\n") == 0
    assert out.startswith("join")


def test_controller_send_refuses_embedded_newline():
    from marauder_core.controller import MarauderController
    ctrl = MarauderController(port="COMX", mock=True)
    lines = []
    ctrl.subscribe(lines.append)
    ctrl.send("ssid -a -n Free\nreboot")
    assert any("refusing" in ln.lower() for ln in lines)          # rejected
    assert not any(ln.startswith(">>") for ln in lines)           # and never forwarded to the device


# ── HMG-D1: CORS allowlist is pinned (no "*") ──────────────────────────────
def test_web_cors_allowlist_is_not_wildcard():
    webapp = pytest.importorskip("web.app")
    origins = webapp._allowed_origins("127.0.0.1", 5000)
    assert "*" not in origins
    assert "http://127.0.0.1:5000" in origins
    assert "http://localhost:5000" in origins


def test_web_cors_allowlist_tracks_custom_host_port():
    webapp = pytest.importorskip("web.app")
    origins = webapp._allowed_origins("192.168.1.50", 8080)
    assert "http://192.168.1.50:8080" in origins
    assert all(o != "*" for o in origins)
