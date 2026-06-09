"""
Headless Marauder — Browser UI (localhost Flask + SocketIO).

Same core, same features, but served as a local web page at http://localhost:5000.
Reuses marauder_core (controller, commands, parsing, capture) identically to the
desktop and terminal UIs.
"""

import argparse
import json
import os
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit

from marauder_core import MarauderController, MarauderParser, CaptureLogger, __version__
from marauder_core import commands, flasher

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(24)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

ctrl = None
parser = MarauderParser()
logger = CaptureLogger()
_autolist_timer = None
_autolist_active = False
_snapshot_counter = 0

# ── helpers ─────────────────────────────────────────────────────────────── #

def _on_line(line: str):
    global _snapshot_counter
    parser.feed(line)
    if logger.enabled:
        logger.write_serial(line)
        _snapshot_counter += 1
        if _snapshot_counter >= 5:
            logger.write_snapshot(parser.ap_rows(), parser.station_rows())
            _snapshot_counter = 0
    socketio.emit("serial", {"line": line})


def _push_tables():
    aps = [{"index": a.index, "ssid": a.ssid, "channel": a.channel,
            "rssi": a.rssi, "bssid": a.bssid} for a in parser.ap_rows()]
    stas = [{"index": s.index, "mac": s.mac, "ap_bssid": s.ap_bssid,
             "rssi": s.rssi} for s in parser.station_rows()]
    socketio.emit("tables", {"aps": aps, "stations": stas})


def _cancel_autolist_timer():
    global _autolist_timer
    if _autolist_timer is not None:
        _autolist_timer.cancel()
        _autolist_timer = None


def _autolist_tick():
    global _autolist_timer
    if _autolist_active and ctrl and ctrl.connected:
        ctrl.send("list -a")
    if _autolist_active:
        _autolist_timer = threading.Timer(3.0, _autolist_tick)
        _autolist_timer.daemon = True
        _autolist_timer.start()


# ── routes ──────────────────────────────────────────────────────────────── #

@app.route("/")
def index():
    return render_template("index.html", version=__version__)


@app.route("/api/commands")
def api_commands():
    return jsonify(commands.to_dict())


@app.route("/api/ports")
def api_ports():
    ports = MarauderController.list_ports()
    return jsonify([{"device": d, "description": desc} for d, desc in ports])


@app.route("/api/status")
def api_status():
    return jsonify({
        "connected": ctrl.connected if ctrl else False,
        "port": ctrl.port if ctrl else None,
        "logging": logger.enabled,
        "log_dir": logger.dir,
        "version": __version__,
    })


# ── socket events ───────────────────────────────────────────────────────── #

@socketio.on("connect_serial")
def on_connect_serial(data):
    global ctrl
    port = data.get("port") or None
    mock = data.get("mock", False)
    try:
        if ctrl and ctrl.connected:
            ctrl.disconnect()
        ctrl = MarauderController(port=port, mock=mock)
        ctrl.subscribe(_on_line)
        connected_port = ctrl.connect()
        emit("status", {"connected": True, "port": connected_port})
    except Exception as e:
        emit("status", {"connected": False, "error": str(e)})


@socketio.on("disconnect_serial")
def on_disconnect_serial():
    global ctrl, _autolist_active
    _autolist_active = False
    _cancel_autolist_timer()
    if ctrl:
        ctrl.disconnect()
    emit("status", {"connected": False, "port": None})


@socketio.on("send_command")
def on_send(data):
    if not ctrl or not ctrl.connected:
        emit("serial", {"line": "[error] not connected"})
        return
    raw = data.get("raw", "").strip()
    cmd_id = data.get("cmd_id")
    values = data.get("values", {})

    if raw:
        ctrl.send(raw)
    elif cmd_id:
        cmd = commands.get(cmd_id)
        if cmd:
            built = commands.build(cmd, values)
            ctrl.send(built)
        else:
            emit("serial", {"line": f"[error] unknown command: {cmd_id}"})


@socketio.on("stop")
def on_stop():
    if ctrl and ctrl.connected:
        ctrl.stop()
    global _autolist_active
    _autolist_active = False
    _cancel_autolist_timer()


@socketio.on("autolist")
def on_autolist(data):
    global _autolist_active
    _cancel_autolist_timer()
    _autolist_active = data.get("enabled", False)
    if _autolist_active:
        _autolist_tick()


@socketio.on("get_tables")
def on_get_tables():
    _push_tables()


@socketio.on("clear_tables")
def on_clear_tables():
    parser.clear()
    _push_tables()


@socketio.on("toggle_log")
def on_toggle_log(data):
    if data.get("enabled"):
        log_dir = data.get("dir") or logger.dir
        logger.set_dir(log_dir)
        path = logger.start()
        emit("log_status", {"enabled": True, "path": path})
    else:
        logger.stop()
        emit("log_status", {"enabled": False})


@socketio.on("flash_detect")
def on_flash_detect(data):
    port = data.get("port", "")
    if not port:
        emit("flash_status", {"error": "No port specified"})
        return
    try:
        def _flash_line(line):
            socketio.emit("serial", {"line": line})
        chip = flasher.detect_chip(port, _flash_line)
        emit("flash_status", {"chip": chip})
    except Exception as e:
        emit("flash_status", {"error": str(e)})


@socketio.on("flash_releases")
def on_flash_releases():
    try:
        tag, assets = flasher.latest_release()
        emit("flash_status", {"tag": tag, "assets": [a["name"] for a in assets]})
    except Exception as e:
        emit("flash_status", {"error": str(e)})


# ── periodic table push ─────────────────────────────────────────────────── #

def _table_pusher():
    while True:
        socketio.sleep(0.7)
        if parser.dirty:
            parser.dirty = False
            _push_tables()

socketio.start_background_task(_table_pusher)


# ── main ────────────────────────────────────────────────────────────────── #

def main():
    ap = argparse.ArgumentParser(description="Headless Marauder — Browser UI")
    ap.add_argument("--port", default=None, help="Serial port (auto-detect if omitted)")
    ap.add_argument("--mock", action="store_true", help="Mock mode (no hardware)")
    ap.add_argument("--host", default="127.0.0.1", help="Bind address (default: localhost only)")
    ap.add_argument("--web-port", type=int, default=5000, help="HTTP port (default: 5000)")
    ap.add_argument("--log", nargs="?", const="", default=None, help="Start logging (optionally set dir)")
    args = ap.parse_args()

    if args.log is not None:
        if args.log:
            logger.set_dir(args.log)
        logger.start()

    if args.port or args.mock:
        global ctrl
        ctrl = MarauderController(port=args.port, mock=args.mock)
        ctrl.subscribe(_on_line)
        try:
            ctrl.connect()
            print(f"[+] Connected to {ctrl.port}")
        except Exception as e:
            print(f"[!] Auto-connect failed: {e}")

    print(f"\n  Headless Marauder v{__version__} — Browser UI")
    print(f"  Open http://{args.host}:{args.web_port} in your browser\n")

    socketio.run(app, host=args.host, port=args.web_port, debug=False,
                 allow_unsafe_werkzeug=True)


if __name__ == "__main__":
    main()
