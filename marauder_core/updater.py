"""
Self-update from the git repo: `git pull --ff-only` + reinstall deps.

Only works when the app was installed via `git clone` (the package's parent dir is a git
checkout). The installer does exactly that, so the in-app "Check for Updates" works for the
shipped product. Streams output through an on_line callback like the flasher.
"""

import os
import subprocess
import sys
import threading
from typing import Callable

Line = Callable[[str], None]


def repo_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def is_git_checkout() -> bool:
    return os.path.isdir(os.path.join(repo_root(), ".git"))


def current_revision() -> str:
    try:
        r = subprocess.run(["git", "-C", repo_root(), "rev-parse", "--short", "HEAD"],
                           capture_output=True, text=True, timeout=10)
        return r.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def _git_env() -> dict:
    # never block on a credential or SSH host-key prompt (the GUI has no terminal)
    env = dict(os.environ)
    env["GIT_TERMINAL_PROMPT"] = "0"
    env.setdefault("GIT_SSH_COMMAND", "ssh -oBatchMode=yes -oStrictHostKeyChecking=accept-new")
    return env


def _run(argv, on_line: Line, env=None, timeout=180) -> int:
    on_line("$ " + " ".join(argv))
    try:
        p = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             stdin=subprocess.DEVNULL, text=True, bufsize=1, env=env)
    except FileNotFoundError as e:
        on_line(f"[error] {e}")
        return 127
    # `for ln in p.stdout` blocks until EOF, so the p.wait(timeout) below is only reached AFTER the
    # child closes stdout. A TCP-stalled `git pull` that hangs with the socket open never closes
    # stdout, so without this watchdog the read (and the update thread) would block forever and the
    # timeout would never fire. A daemon Timer kills the child on expiry, which ends the read loop.
    timed_out = {"v": False}

    def _kill_on_timeout():
        timed_out["v"] = True
        try:
            if p.poll() is None:
                p.kill()
        except Exception:
            pass

    watchdog = threading.Timer(timeout, _kill_on_timeout)
    watchdog.daemon = True
    watchdog.start()
    try:
        for ln in p.stdout:                   # type: ignore[union-attr]
            on_line(ln.rstrip("\n"))
        p.wait(timeout=5)                     # stdout hit EOF; the child should exit promptly now
    except Exception as e:
        on_line(f"[error] {e}")
        try:
            if p.poll() is None:
                p.kill(); p.wait(timeout=5)
        except Exception:
            pass
        return -1
    finally:
        watchdog.cancel()
        try:
            if p.stdout:
                p.stdout.close()
        except Exception:
            pass
    if timed_out["v"]:
        on_line("[error] timed out — killed")
        return -1
    return p.returncode


def _safe_directory_present(root: str) -> bool:
    """True if `root` (or the catch-all `*`) is already a global git safe.directory. Used so
    update() can skip a redundant `--add`: `git config --add` appends unconditionally, so a blind
    add on every update() accumulates duplicate safe.directory lines in the user's global gitconfig."""
    try:
        r = subprocess.run(["git", "config", "--global", "--get-all", "safe.directory"],
                           capture_output=True, text=True, timeout=10)
    except Exception:
        return False
    entries = {ln.strip() for ln in r.stdout.splitlines() if ln.strip()}
    return root in entries or "*" in entries


def update(on_line: Line) -> bool:
    """Pull latest + reinstall requirements. Returns True on success."""
    root = repo_root()
    if not is_git_checkout():
        on_line("[update] not a git checkout — install via `git clone` to enable updates.")
        return False
    # tolerate root-owned clones run by a normal user (Kali sudo-install flow). Only ADD the entry
    # if it isn't already present — a blind `--add` on every update() piles up duplicate lines.
    if not _safe_directory_present(root):
        _run(["git", "config", "--global", "--add", "safe.directory", root], on_line)
    on_line(f"[update] current revision: {current_revision()}")
    if _run(["git", "-C", root, "pull", "--ff-only"], on_line, env=_git_env()) != 0:
        on_line("[update] git pull failed (local changes, auth, or no network?). Aborted.")
        return False
    req = os.path.join(root, "requirements.txt")
    if os.path.exists(req):
        rc = _run([sys.executable, "-m", "pip", "install", "-q", "-r", req], on_line, timeout=600)
        if rc != 0:
            on_line("[update] code updated, but dependency install FAILED — fix deps before restarting.")
            return False
    on_line(f"[update] now at {current_revision()} — restart the app to apply.")
    return True
