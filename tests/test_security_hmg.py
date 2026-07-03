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


# ── HMG-D4: a non-localhost bind is flagged so the operator consents to LAN exposure ──
def test_web_is_public_bind_flags_only_non_loopback():
    webapp = pytest.importorskip("web.app")
    for loopback in ("127.0.0.1", "localhost", "::1", "", "  LOCALHOST  "):
        assert webapp._is_public_bind(loopback) is False
    for public in ("0.0.0.0", "192.168.1.50", "10.0.0.2", "example.local", "::"):
        assert webapp._is_public_bind(public) is True


# ── HMG-D5: the web toggle_log dir is confined under the user's home ──
def test_web_toggle_log_rejects_dir_outside_home(monkeypatch, tmp_path):
    """`dir` is client-supplied and logger.start() does makedirs+open on it — a dir that escapes the
    user's home must be refused BEFORE the logger touches the filesystem."""
    webapp = pytest.importorskip("web.app")
    events = []
    monkeypatch.setattr(webapp, "emit", lambda *a, **k: events.append(a))
    monkeypatch.setattr(webapp.os.path, "expanduser", lambda _p: str(tmp_path / "home"))
    touched = {"set_dir": False, "start": False}
    monkeypatch.setattr(webapp.logger, "set_dir", lambda *_a: touched.__setitem__("set_dir", True))
    monkeypatch.setattr(webapp.logger, "start", lambda *_a, **_k: touched.__setitem__("start", True))

    webapp.on_toggle_log({"enabled": True, "dir": str(tmp_path / "elsewhere" / "logs")})

    assert touched["set_dir"] is False and touched["start"] is False   # never opened the log
    assert any(a[0] == "log_status" and a[1].get("enabled") is False
               and "home" in str(a[1].get("error", "")) for a in events)


def test_web_toggle_log_accepts_dir_under_home(monkeypatch, tmp_path):
    webapp = pytest.importorskip("web.app")
    events = []
    monkeypatch.setattr(webapp, "emit", lambda *a, **k: events.append(a))
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(webapp.os.path, "expanduser", lambda _p: str(home))
    monkeypatch.setattr(webapp.logger, "set_dir", lambda *_a: None)
    monkeypatch.setattr(webapp.logger, "start", lambda *_a, **_k: "ok")

    webapp.on_toggle_log({"enabled": True, "dir": str(home / "marauder-logs")})

    assert any(a[0] == "log_status" and a[1].get("enabled") is True for a in events)


# ── HMG-D3: the esptool busy claim is atomic (fixes the check-then-set race) ──
def test_web_acquire_flash_is_exclusive():
    """detect/flash/suicide/erase share one serial port; the claim must be mutually exclusive so two
    tabs firing at once can't both pass a check-then-set and drive two esptools onto the same port."""
    webapp = pytest.importorskip("web.app")
    webapp._flash_busy = False
    try:
        assert webapp._acquire_flash() is True
        assert webapp._acquire_flash() is False      # already claimed — a 2nd tab can't also pass
        webapp._release_flash()
        assert webapp._acquire_flash() is True        # released → claimable again
    finally:
        webapp._release_flash()
