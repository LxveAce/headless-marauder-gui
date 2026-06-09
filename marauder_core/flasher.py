"""
Flasher — flash ESP32 firmware from inside the app.

Wraps `esptool` (subprocess, streamed) and pulls firmware straight from the official
GitHub release + the repo's FlashFiles/ tree, so you can flash a brand-new board or
update an existing one without leaving the GUI/TUI.

Key facts baked in (verified against the v1.12.1 release):
  * Releases ship ONLY app .bins (board-specific). There is no generic "esp32" build —
    classic ESP32 dev boards use `_old_hardware` / `_lddb` / etc., S3 uses `_multiboardS3`.
  * bootloader / partitions / boot_app0 are NOT in the release — they live in FlashFiles/:
        MarauderV4/                 classic-ESP32 bootloader+partitions
        FlipperZeroMultiBoardS3/    S3 bootloader+partitions + the shared boot_app0.bin
        FlipperZeroDevBoard/        S2 bootloader+partitions
  * Flash offsets: partitions 0x8000, boot_app0 0xE000, app 0x10000 always.
    bootloader 0x1000 on classic ESP32 / S2, but 0x0 on S3 / C-series.

Suicide-bundle note (flash_suicide / read_bundle_manifest): this module only FLASHES a
bundle that the Suicide-Marauder repo's provisioner already built (bundle.json + .bins). It
does NOT burn eFuses and does NOT do any T2/secure-boot provisioning or password hashing —
that all happens in the Suicide-Marauder host provisioner, never here.

----------------------------------------------------------------------------------------
FIRMWARE-PROFILE REGISTRY (additive — does NOT change the Marauder or suicide flow)
----------------------------------------------------------------------------------------
On top of the original Marauder flasher, this module now exposes an extensible registry of
FirmwareProfile objects so the same esptool plumbing can flash other ESP32 firmwares:

  * 'marauder'  — ESP32Marauder (the original behavior, byte-for-byte; supports_suicide=True).
  * 'esp32-div' — cifertech/ESP32-DIV (ESP32-S3, multi-file image; app@0x10000 + boot chain).
  * 'bruce'     — pr3y/Bruce (per-board MERGED single .bin, flashed at 0x0; auto board->chip map).
  * 'custom'    — flash ANY local .bin(s) you provide, with chip-appropriate default offsets.

The original MODULE-LEVEL functions (latest_release, variants_for_chip, default_variant,
support_files, detect_chip, flash, erase, flash_suicide, cache_dir, download_to,
read_bundle_manifest) are preserved as BACK-COMPAT wrappers that delegate to the marauder
profile, so the existing GUI/TUI keep working unchanged.

NOTE on ESP32-DIV / Bruce: these are pen-test/RF firmwares that include RF-jamming features
which are ILLEGAL to operate. This module only FLASHES the stock images byte-for-byte; it
adds NO jamming functionality and enables nothing — it is plain firmware flashing.
"""

import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
from typing import Callable, Dict, List, Optional, Tuple

LATEST_API = "https://api.github.com/repos/justcallmekoko/ESP32Marauder/releases/latest"
RAW_BRANCHES = ("master", "main")
RAW_TMPL = "https://raw.githubusercontent.com/justcallmekoko/ESP32Marauder/{branch}/FlashFiles/{path}"
_UA = {"User-Agent": "headless-marauder-gui"}

Line = Callable[[str], None]

# image-model markers
IMAGE_MERGED = "merged-single-bin"      # one .bin holds bootloader+partitions+app, flash at its offset
IMAGE_MULTI = "multi-file-offsets"      # app .bin only; needs separate bootloader/partitions/boot_app0

# bootloader sits at 0x0 on S3 and the RISC-V parts, 0x1000 on classic ESP32 / S2
_BOOTLOADER_0 = {"esp32s3", "esp32c2", "esp32c3", "esp32c6", "esp32c5", "esp32h2"}

# FlashFiles dir that holds bootloader+partitions for each chip family
_SUPPORT_DIR = {
    "esp32": "MarauderV4",
    "esp32s2": "FlipperZeroDevBoard",
    "esp32s3": "FlipperZeroMultiBoardS3",
}
_BOOT_APP0_PATH = "FlipperZeroMultiBoardS3/boot_app0.bin"
_BOOTLOADER_NAME = "esp32_marauder.ino.bootloader.bin"
_PARTITIONS_NAME = "esp32_marauder.ino.partitions.bin"

# Friendly labels for the release app variants (suffix -> description)
_VARIANT_LABELS = {
    "old_hardware": "Generic ESP32 / original v4 hardware (ILI9341)",
    "lddb": "Generic ESP32 dev board, no display (LDDB/NodeMCU/Wemos)",
    "v6": "Official Marauder v6", "v6_1": "Official Marauder v6.1",
    "v7": "Official Marauder v7", "v8": "Official Marauder v8",
    "kit": "Marauder Kit (Huzzah32)", "mini": "Marauder Mini",
    "mini_v3": "Marauder Mini v3 (ESP32-C5)",
    "marauder_dev_board_pro": "Dev Board Pro / BFFB (serial)",
    "multiboardS3": "Flipper MultiBoard / ESP32-S3",
    "flipper": "Flipper Zero WiFi Dev Board (ESP32-S2)",
    "rev_feather": "Rev Feather (ESP32-S2)",
    "m5cardputer": "M5Cardputer (ESP32-S3)", "m5cardputer_adv": "M5Cardputer Adv (ESP32-S3)",
    "m5stickc_plus": "M5StickC Plus", "m5stickc_plus2": "M5StickC Plus 2",
    "cyd_2432S028": "CYD 2.8\"", "cyd_2432S028_2usb": "CYD 2.8\" (2-USB)",
    "cyd_2432S024_guition": "CYD 2.4\" Guition", "cyd_3_5_inch": "CYD 3.5\"",
    "esp32c5devkitc1": "ESP32-C5 DevKitC-1",
}


def _chip_of_variant(name: str) -> str:
    n = name.lower()
    if "multiboards3" in n or "m5cardputer" in n:
        return "esp32s3"
    if "_flipper" in n or "rev_feather" in n:
        return "esp32s2"
    if "mini_v3" in n or "esp32c5devkitc1" in n:
        return "esp32c5"
    return "esp32"  # everything else (old_hardware, v6/7/8, kit, mini, lddb, cyd_*, m5stick...)


def _variant_label(name: str) -> str:
    # Match the most specific (longest) suffix so e.g. "esp32c5devkitc1" doesn't match "kit",
    # and "mini_v3" doesn't match "mini".
    best = ""
    for suffix in _VARIANT_LABELS:
        if suffix in name and len(suffix) > len(best):
            best = suffix
    return _VARIANT_LABELS[best] if best else name


# --------------------------------------------------------------------------- #
# esptool plumbing  (shared by every profile)
# --------------------------------------------------------------------------- #

def esptool_argv(*args: str) -> List[str]:
    return [sys.executable, "-m", "esptool", *args]


def esptool_available() -> bool:
    try:
        return subprocess.run(esptool_argv("version"), capture_output=True, timeout=20).returncode == 0
    except Exception:
        return False


def _run_stream(argv: List[str], on_line: Line) -> int:
    """Run a command, stream combined stdout/stderr line-by-line, return exit code.

    On any exception mid-stream (e.g. the UI callback raises because a dialog closed), the
    child is killed and reaped so it can't keep holding the serial port — otherwise the next
    flash fails with 'port busy'.
    """
    on_line("$ " + " ".join(argv))
    try:
        proc = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                stdin=subprocess.DEVNULL, text=True, bufsize=1)
    except FileNotFoundError as e:
        on_line(f"[error] {e}")
        return 127
    try:
        for line in proc.stdout:                   # type: ignore[union-attr]
            on_line(line.rstrip("\n"))
        proc.wait()
    except Exception as e:
        on_line(f"[error] {e}")
        try:
            proc.kill()
            proc.wait(timeout=5)
        except Exception:
            pass
        return -1
    finally:
        try:
            if proc.stdout:
                proc.stdout.close()
        except Exception:
            pass
    on_line(f"[exit {proc.returncode}]")
    return proc.returncode


def _detect_chip(port: str, on_line: Line) -> Optional[str]:
    """Return an esptool chip id ('esp32', 'esp32s3', ...) or None. (chip detection is
    firmware-agnostic, so every profile shares this implementation.)"""
    argv = esptool_argv("--port", port, "chip_id")
    out_lines: List[str] = []

    def cap(s: str):
        out_lines.append(s)
        on_line(s)

    _run_stream(argv, cap)
    text = "\n".join(out_lines)
    for token, chip in (("ESP32-S3", "esp32s3"), ("ESP32-S2", "esp32s2"),
                        ("ESP32-C6", "esp32c6"), ("ESP32-C5", "esp32c5"),
                        ("ESP32-C3", "esp32c3"), ("ESP32-C2", "esp32c2"),
                        ("ESP32-H2", "esp32h2")):
        if token in text:
            return chip
    if re.search(r"\bESP32\b", text):
        return "esp32"
    return None


def _http_get(url: str) -> bytes:
    req = urllib.request.Request(url, headers=_UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def download_to(url: str, dest: str, on_line: Line) -> str:
    on_line(f"[download] {os.path.basename(dest)}")
    data = _http_get(url)
    with open(dest, "wb") as f:
        f.write(data)
    on_line(f"[download] {len(data)} bytes -> {dest}")
    return dest


def cache_dir() -> str:
    d = os.path.join(tempfile.gettempdir(), "marauder_fw")
    os.makedirs(d, exist_ok=True)
    return d


def erase(port: str, chip: str, on_line: Line) -> int:
    return _run_stream(esptool_argv("--chip", chip, "--port", port, "erase_flash"), on_line)


def _github_latest(api_url: str) -> Tuple[str, List[Dict]]:
    """GET a GitHub /releases/latest API URL and return (tag, raw_assets_list)."""
    data = json.loads(_http_get(api_url).decode("utf-8"))
    tag = data.get("tag_name", "latest")
    return tag, data.get("assets", [])


# --------------------------------------------------------------------------- #
# FirmwareProfile abstraction
# --------------------------------------------------------------------------- #

class FirmwareProfile:
    """Base class for a flashable firmware.

    Subclasses describe WHERE the firmware comes from and HOW its image is laid out; the
    actual esptool invocation is shared (see `flash_assets`). An asset dict is
    {name, url, chip, label} and may additionally carry {offset, merged:bool} when a profile
    needs to pin an explicit flash offset (e.g. a merged image at 0x0, or an app-only image
    at 0x10000).

    Attributes
    ----------
    id              short stable id used by get_profile() / list_profiles()
    label           human-friendly name
    repo            "owner/name" GitHub repo, or None for local-only profiles
    supports_suicide whether the Suicide-Marauder bundle flow applies (marauder only)
    image_model     IMAGE_MERGED or IMAGE_MULTI — whether the release is a single merged bin
    """

    id: str = "base"
    label: str = "Firmware"
    repo: Optional[str] = None
    supports_suicide: bool = False
    image_model: str = IMAGE_MULTI

    # ---- release / variant discovery ----
    def latest_release(self) -> Tuple[str, List[Dict]]:
        """Return (tag, [ {name, url, chip, label[, offset, merged]} ... ])."""
        raise NotImplementedError

    def variants_for_chip(self, assets: List[Dict], chip: str) -> List[Dict]:
        return [a for a in assets if a.get("chip") == chip]

    def default_variant(self, assets: List[Dict], chip: str) -> Optional[Dict]:
        cands = self.variants_for_chip(assets, chip)
        return cands[0] if cands else None

    # ---- support files (None when the release is a merged single image) ----
    def support_files(self, chip: str, cache: str, on_line: Line) -> Optional[Dict[str, str]]:
        """Return offset->path for bootloader/partitions/boot_app0, or None when the
        firmware ships a merged single image (nothing extra to fetch)."""
        return None

    # ---- the app-image offset for this profile/chip ----
    def app_offset(self, chip: str) -> str:
        """Where the app/merged image is written. Merged images go to 0x0; app-only at
        0x10000."""
        return "0x0" if self.image_model == IMAGE_MERGED else "0x10000"

    # ---- flashing (shared esptool invocation) ----
    def flash_assets(self, port: str, chip: str, app_path: str, on_line: Line,
                     mode: str = "app", baud: int = 921600,
                     support: Optional[Dict[str, str]] = None,
                     app_offset: Optional[str] = None,
                     flash_freq: Optional[str] = None) -> int:
        """Write `support` (offset->path) plus the app image with esptool.

        mode 'app'  -> write only the application image (re-flash / update existing board)
        mode 'full' -> also write support files first (blank board); needs `support`
                       (a merged-single-bin profile never needs `support`).
        """
        files: List[str] = []
        if mode == "full":
            if support:
                for off, path in support.items():
                    files += [off, path]
            elif self.image_model != IMAGE_MERGED:
                on_line("[error] full flash needs bootloader/partitions/boot_app0 (none provided)")
                return 2
        off = app_offset or self.app_offset(chip)
        files += [off, app_path]

        # --flash_size detect: auto-detect the chip's real flash size and patch the image
        # header. Without it esptool keeps the binary's header value (often 16MB), which
        # boot-loops a 4MB board with "Detected size(4096k) smaller than ... header(16384k)."
        extra: List[str] = []
        if flash_freq:
            extra += ["--flash_freq", flash_freq]
        argv = esptool_argv("--chip", chip, "--port", port, "--baud", str(baud),
                            "--before", "default_reset", "--after", "hard_reset",
                            "write_flash", "-z", "--flash_size", "detect", *extra, *files)
        return _run_stream(argv, on_line)


# --------------------------------------------------------------------------- #
# Marauder profile  (REPRODUCES the original module behavior EXACTLY)
# --------------------------------------------------------------------------- #

class MarauderProfile(FirmwareProfile):
    id = "marauder"
    label = "ESP32 Marauder (justcallmekoko)"
    repo = "justcallmekoko/ESP32Marauder"
    supports_suicide = True
    image_model = IMAGE_MULTI

    def latest_release(self) -> Tuple[str, List[Dict]]:
        """Return (tag, [ {name, url, chip, label} ... ]) for app .bin assets."""
        tag, raw = _github_latest(LATEST_API)
        assets = []
        for a in raw:
            name = a.get("name", "")
            if not name.endswith(".bin"):
                continue
            assets.append({
                "name": name,
                "url": a.get("browser_download_url"),
                "chip": _chip_of_variant(name),
                "label": _variant_label(name),
            })
        return tag, assets

    def default_variant(self, assets: List[Dict], chip: str) -> Optional[Dict]:
        pref = {"esp32": "old_hardware", "esp32s3": "multiboardS3",
                "esp32s2": "flipper", "esp32c5": "esp32c5devkitc1"}.get(chip)
        cands = self.variants_for_chip(assets, chip)
        if pref:
            for a in cands:
                if pref in a["name"]:
                    return a
        return cands[0] if cands else None

    def support_files(self, chip: str, cache: str, on_line: Line) -> Optional[Dict[str, str]]:
        """Download bootloader/partitions/boot_app0 for a full flash. Returns offset->path."""
        sdir = _SUPPORT_DIR.get(chip)
        if not sdir:
            raise RuntimeError(f"No auto support-file mapping for {chip}; use local files for a full flash.")
        boot = _fetch_flashfile(f"{sdir}/{_BOOTLOADER_NAME}", os.path.join(cache, f"{chip}_bootloader.bin"), on_line)
        part = _fetch_flashfile(f"{sdir}/{_PARTITIONS_NAME}", os.path.join(cache, f"{chip}_partitions.bin"), on_line)
        bapp = _fetch_flashfile(_BOOT_APP0_PATH, os.path.join(cache, "boot_app0.bin"), on_line)
        bl_off = "0x0" if chip in _BOOTLOADER_0 else "0x1000"
        return {bl_off: boot, "0x8000": part, "0xe000": bapp}


def _fetch_flashfile(rel_path: str, dest: str, on_line: Line) -> str:
    last = None
    for branch in RAW_BRANCHES:
        url = RAW_TMPL.format(branch=branch, path=rel_path)
        try:
            return download_to(url, dest, on_line)
        except Exception as e:
            last = e
    raise RuntimeError(f"could not fetch {rel_path}: {last}")


# --------------------------------------------------------------------------- #
# ESP32-DIV profile  (cifertech/ESP32-DIV — ESP32-S3, multi-file image)
# --------------------------------------------------------------------------- #
#
# Releases ship ONLY the app image (e.g. ESP32-DIV-v1.6.0.bin, ~1.6 MB) which goes at
# 0x10000 — NOT a merged factory bin, so image_model is multi-file-offsets. The boot chain
# (bootloader / partitions / boot_app0) is NOT attached to releases; it lives in the repo
# tree under tools/esp32s3/ and tools/esp32-div-flasher/bundled/. We fetch those raw.
#
#   ESP32-S3 (DIV v2, current): bootloader@0x0,    partitions@0x8000, boot_app0@0xE000,
#                               app@0x10000, flash_mode dio, flash_freq 80m
#   classic ESP32 (DIV v1):     bootloader@0x1000, partitions@0x8000, boot_app0@0xE000,
#                               app@0x10000, flash_mode dio, flash_freq 40m
#
# This is plain firmware flashing — no jamming functionality is added or enabled.

_DIV_API = "https://api.github.com/repos/cifertech/ESP32-DIV/releases/latest"
_DIV_RAW_TMPL = "https://raw.githubusercontent.com/cifertech/ESP32-DIV/{branch}/{path}"
_DIV_BRANCHES = ("main", "master")
# boot-chain bins live under tools/ in the repo (S3 generation = DIV v2, recommended)
_DIV_BOOTLOADER = "tools/esp32s3/ESP32-DIV.ino.bootloader.bin"
_DIV_PARTITIONS = "tools/esp32s3/ESP32-DIV.ino.partitions.bin"
_DIV_BOOT_APP0 = "tools/esp32-div-flasher/bundled/boot_app0.bin"
_DIV_FLASH_FREQ = {"esp32s3": "80m", "esp32": "40m"}


class Esp32DivProfile(FirmwareProfile):
    id = "esp32-div"
    label = "ESP32-DIV (cifertech)"
    repo = "cifertech/ESP32-DIV"
    supports_suicide = False
    image_model = IMAGE_MULTI

    def latest_release(self) -> Tuple[str, List[Dict]]:
        """Return (tag, assets). Releases bundle the app .bin plus raw Arduino source files
        as separate assets; only the .bin assets are firmware. Each is the APP image
        (-> 0x10000). DIV v2 boards are ESP32-S3."""
        tag, raw = _github_latest(_DIV_API)
        assets = []
        for a in raw:
            name = a.get("name", "")
            if not name.endswith(".bin"):
                continue   # skip .ino/.cpp/.h source assets
            assets.append({
                "name": name,
                "url": a.get("browser_download_url"),
                "chip": "esp32s3",          # current/recommended DIV generation
                "label": f"ESP32-DIV app image ({name})",
                "offset": "0x10000",        # release bin is the app image only
                "merged": False,
            })
        return tag, assets

    def variants_for_chip(self, assets: List[Dict], chip: str) -> List[Dict]:
        # DIV releases are S3 app images; show them for any selected chip rather than hiding
        # everything when detection comes back as classic ESP32 on an older DIV v1 board.
        same = [a for a in assets if a.get("chip") == chip]
        return same if same else list(assets)

    def default_variant(self, assets: List[Dict], chip: str) -> Optional[Dict]:
        cands = self.variants_for_chip(assets, chip)
        return cands[0] if cands else None

    def support_files(self, chip: str, cache: str, on_line: Line) -> Optional[Dict[str, str]]:
        boot = _fetch_div_file(_DIV_BOOTLOADER, os.path.join(cache, f"div_{chip}_bootloader.bin"), on_line)
        part = _fetch_div_file(_DIV_PARTITIONS, os.path.join(cache, f"div_{chip}_partitions.bin"), on_line)
        bapp = _fetch_div_file(_DIV_BOOT_APP0, os.path.join(cache, "div_boot_app0.bin"), on_line)
        bl_off = "0x0" if chip in _BOOTLOADER_0 else "0x1000"
        return {bl_off: boot, "0x8000": part, "0xe000": bapp}

    def app_offset(self, chip: str) -> str:
        return "0x10000"

    def flash_assets(self, port: str, chip: str, app_path: str, on_line: Line,
                     mode: str = "app", baud: int = 921600,
                     support: Optional[Dict[str, str]] = None,
                     app_offset: Optional[str] = None,
                     flash_freq: Optional[str] = None) -> int:
        # DIV uses a chip-specific flash_freq (S3 80m / classic 40m); default it here.
        freq = flash_freq or _DIV_FLASH_FREQ.get(chip)
        return super().flash_assets(port, chip, app_path, on_line, mode=mode, baud=baud,
                                    support=support, app_offset=app_offset, flash_freq=freq)


def _fetch_div_file(rel_path: str, dest: str, on_line: Line) -> str:
    last = None
    for branch in _DIV_BRANCHES:
        url = _DIV_RAW_TMPL.format(branch=branch, path=rel_path)
        try:
            return download_to(url, dest, on_line)
        except Exception as e:
            last = e
    raise RuntimeError(f"could not fetch {rel_path}: {last}")


# --------------------------------------------------------------------------- #
# Bruce profile  (pr3y/Bruce — per-board MERGED single .bin)
# --------------------------------------------------------------------------- #
#
# Bruce auto-maps cleanly: each release ships one MERGED .bin per board, strictly named
# Bruce-<env>.bin (a single esptool merge-bin image with bootloader+partitions+app baked in,
# the chip-specific bootloader offset already inside it). So the flash command is always
# `write_flash 0x0 Bruce-<env>.bin` with --chip <family> for autodetect/verify. The only
# per-board variation is the chip family, which we derive from the env name. A parallel set
# of Bruce-LAUNCHER_<board>.bin assets is a separate loader variant — surfaced as its own
# label so a board picker keeps them distinct. Unknown/new boards fall through to chip
# 'esp32' and can also be flashed via the 'custom' local-bin profile.
#
# This is plain firmware flashing — no jamming functionality is added or enabled.

_BRUCE_API = "https://api.github.com/repos/pr3y/Bruce/releases/latest"
_BRUCE_RE = re.compile(r"^Bruce-(LAUNCHER_)?(.+)\.bin$", re.IGNORECASE)

# env-name fragments -> esptool chip family (derived from the CI build matrix). Order matters:
# the most specific fragments are tried first so e.g. "esp32-s3" wins over "esp32".
_BRUCE_FAMILY_HINTS: Tuple[Tuple[str, str], ...] = (
    ("esp32-s3", "esp32s3"), ("esp32s3", "esp32s3"), ("-s3", "esp32s3"),
    ("cardputer", "esp32s3"), ("sticks3", "esp32s3"), ("cores3", "esp32s3"),
    ("dinmeter", "esp32s3"), ("smoochiee", "esp32s3"), ("reaper", "esp32s3"),
    ("xk404", "esp32s3"), ("es3c28p", "esp32s3"),
    ("t-embed", "esp32s3"), ("t-deck", "esp32s3"), ("t-watch-s3", "esp32s3"),
    ("t-hmi", "esp32s3"), ("t-lora-pager", "esp32s3"), ("t-display-s3", "esp32s3"),
    ("esp32-c5", "esp32c5"), ("esp32c5", "esp32c5"), ("nm-cyd-c5", "esp32c5"),
    ("-c5", "esp32c5"),
    ("esp32-c6", "esp32c6"), ("esp32c6", "esp32c6"), ("nesso-n1", "esp32c6"),
    ("-c6", "esp32c6"),
)


def _bruce_family(env: str) -> str:
    """Map a Bruce env/board name to an esptool chip family. Defaults to classic 'esp32'
    (the largest CI bucket: CYD boards, M5Stack core/stick, Marauder boards, etc.)."""
    e = env.lower()
    for frag, fam in _BRUCE_FAMILY_HINTS:
        if frag in e:
            return fam
    return "esp32"


class BruceProfile(FirmwareProfile):
    id = "bruce"
    label = "Bruce (pr3y)"
    repo = "pr3y/Bruce"
    supports_suicide = False
    image_model = IMAGE_MERGED

    def latest_release(self) -> Tuple[str, List[Dict]]:
        """Return (tag, assets). One MERGED .bin per board, Bruce-<env>.bin (flash @0x0).
        LAUNCHER_* assets are kept as a distinct, separate firmware variant."""
        tag, raw = _github_latest(_BRUCE_API)
        assets = []
        for a in raw:
            name = a.get("name", "")
            m = _BRUCE_RE.match(name)
            if not m:
                continue
            is_launcher = bool(m.group(1))
            env = m.group(2)
            fam = _bruce_family(env)
            label = f"Bruce {env}" + (" [LAUNCHER loader]" if is_launcher else "")
            assets.append({
                "name": name,
                "url": a.get("browser_download_url"),
                "chip": fam,
                "label": label,
                "offset": "0x0",       # merged image always flashes at 0x0
                "merged": True,
                "launcher": is_launcher,
            })
        return tag, assets

    def default_variant(self, assets: List[Dict], chip: str) -> Optional[Dict]:
        # prefer a non-launcher (main app) build for this chip family
        cands = self.variants_for_chip(assets, chip)
        for a in cands:
            if not a.get("launcher"):
                return a
        return cands[0] if cands else None

    # merged single image: nothing extra to fetch
    def support_files(self, chip: str, cache: str, on_line: Line) -> Optional[Dict[str, str]]:
        return None

    def app_offset(self, chip: str) -> str:
        return "0x0"


# --------------------------------------------------------------------------- #
# Custom / local profile  (flash ANY local .bin(s) — the extensibility play)
# --------------------------------------------------------------------------- #
#
# No GitHub repo: the user points at local files. Two ways to use it:
#   * flash a single merged image at 0x0 (image_model treated as merged via default offset),
#   * or pass an explicit `support` map (offset->path) for a full multi-file flash and the
#     app image at its app_offset (default 0x10000 app-only, or 0x0 for a merged blob).
# Bruce-on-a-new-board, or any other ESP32 firmware you have a .bin for, can be flashed here.

class CustomLocalProfile(FirmwareProfile):
    id = "custom"
    label = "Custom / local .bin"
    repo = None
    supports_suicide = False
    image_model = IMAGE_MERGED   # a lone local .bin is treated as a merged image @0x0 by default

    def latest_release(self) -> Tuple[str, List[Dict]]:
        # No remote release for local files.
        return ("local", [])

    def variants_for_chip(self, assets: List[Dict], chip: str) -> List[Dict]:
        return list(assets)

    def default_variant(self, assets: List[Dict], chip: str) -> Optional[Dict]:
        return assets[0] if assets else None

    def support_files(self, chip: str, cache: str, on_line: Line) -> Optional[Dict[str, str]]:
        # The caller supplies its own local support files; nothing to download.
        return None

    @staticmethod
    def local_asset(path: str, chip: Optional[str] = None,
                    offset: str = "0x0", merged: bool = True) -> Dict:
        """Build an asset dict for a local .bin (no download needed; flash_local uses path)."""
        return {
            "name": os.path.basename(path),
            "url": None,
            "path": path,
            "chip": chip or "esp32",
            "label": f"Local: {os.path.basename(path)}",
            "offset": offset,
            "merged": merged,
        }

    def flash_local(self, port: str, chip: str, app_path: str, on_line: Line,
                    app_offset: str = "0x0", baud: int = 921600,
                    support: Optional[Dict[str, str]] = None,
                    flash_freq: Optional[str] = None) -> int:
        """Flash local file(s). `support` (offset->path) is optional for a full flash; the
        app image goes at `app_offset` (0x0 for a merged blob, 0x10000 for app-only)."""
        mode = "full" if support else "app"
        return self.flash_assets(port, chip, app_path, on_line, mode=mode, baud=baud,
                                 support=support, app_offset=app_offset, flash_freq=flash_freq)


# --------------------------------------------------------------------------- #
# Profile registry
# --------------------------------------------------------------------------- #

_MARAUDER = MarauderProfile()

PROFILES: Dict[str, FirmwareProfile] = {
    p.id: p for p in (
        _MARAUDER,
        Esp32DivProfile(),
        BruceProfile(),
        CustomLocalProfile(),
    )
}


def get_profile(profile_id: str) -> FirmwareProfile:
    """Return the FirmwareProfile for an id (raises KeyError on unknown id)."""
    return PROFILES[profile_id]


def list_profiles() -> List[Tuple[str, str]]:
    """Return [(id, label) ...] for every registered profile, in registry order."""
    return [(p.id, p.label) for p in PROFILES.values()]


# --------------------------------------------------------------------------- #
# BACK-COMPAT module-level API  (delegates to the marauder profile so the
# existing GUI/TUI keep working byte-for-byte)
# --------------------------------------------------------------------------- #

def latest_release() -> Tuple[str, List[Dict]]:
    """Marauder release assets (back-compat wrapper)."""
    return _MARAUDER.latest_release()


def variants_for_chip(assets: List[Dict], chip: str) -> List[Dict]:
    return _MARAUDER.variants_for_chip(assets, chip)


def default_variant(assets: List[Dict], chip: str) -> Optional[Dict]:
    return _MARAUDER.default_variant(assets, chip)


def support_files(chip: str, cache: str, on_line: Line) -> Dict[str, str]:
    """Download Marauder bootloader/partitions/boot_app0. Returns offset->path."""
    # marauder always returns a dict (raises if unmapped); keep the original return type.
    result = _MARAUDER.support_files(chip, cache, on_line)
    assert result is not None  # marauder never returns None
    return result


def detect_chip(port: str, on_line: Line) -> Optional[str]:
    """Return an esptool chip id ('esp32', 'esp32s3', ...) or None."""
    return _detect_chip(port, on_line)


def flash(port: str, chip: str, app_path: str, on_line: Line,
          mode: str = "app", baud: int = 921600,
          support: Optional[Dict[str, str]] = None) -> int:
    """
    Flash the Marauder app (back-compat wrapper, identical behavior to the original flash()).

    mode 'app'  -> write only the application at 0x10000 (re-flash / update existing board)
    mode 'full' -> write bootloader+partitions+boot_app0+app (blank board); needs `support`
    """
    return _MARAUDER.flash_assets(port, chip, app_path, on_line,
                                  mode=mode, baud=baud, support=support)


# --------------------------------------------------------------------------- #
# suicide bundle (flash a pre-provisioned Suicide-Marauder bundle)
# --------------------------------------------------------------------------- #

def read_bundle_manifest(bundle_dir: str) -> Dict:
    """Parse <bundle_dir>/bundle.json and return the manifest dict.

    A bundle is produced by the Suicide-Marauder repo's host/provision.py: it's a directory
    holding bundle.json plus the .bin images. The manifest must carry a "files" list whose
    entries each name a file and an offset ("offset_hex" like "0x10000", or an int "offset").

    Raises FileNotFoundError if bundle.json is missing, ValueError if it's malformed.
    eFuse/T2 provisioning is NOT described or performed here — see the module docstring.
    """
    path = os.path.join(bundle_dir, "bundle.json")
    if not os.path.isfile(path):
        raise FileNotFoundError(f"no bundle.json in {bundle_dir} (expected at {path})")
    try:
        with open(path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        raise ValueError(f"could not read bundle.json: {e}")
    if not isinstance(manifest, dict):
        raise ValueError("bundle.json must contain a JSON object")
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise ValueError('bundle.json is missing a non-empty "files" list')
    for i, entry in enumerate(files):
        if not isinstance(entry, dict) or not entry.get("file"):
            raise ValueError(f'bundle.json "files"[{i}] must be an object with a "file" key')
        if entry.get("offset_hex") is None and entry.get("offset") is None:
            raise ValueError(f'bundle.json "files"[{i}] is missing an "offset_hex"/"offset"')
    return manifest


def _bundle_offset(entry: Dict) -> int:
    """Resolve a manifest file entry's flash offset to an int (offset_hex wins, then offset)."""
    if entry.get("offset_hex") is not None:
        return int(str(entry["offset_hex"]), 16)
    return int(entry["offset"])


def flash_suicide(port: str, chip: str, bundle_dir: str, on_line: Line,
                  baud: int = 921600) -> int:
    """Flash a pre-provisioned Suicide-Marauder bundle in ONE esptool write_flash.

    Reads bundle.json, validates every listed .bin exists (lists any that don't), warns if the
    manifest's chip disagrees with `chip`, then writes all offset/path pairs (sorted by offset)
    in a single `write_flash -z --flash_size detect`. Mirrors flash() for reset/size handling.

    This NEVER burns eFuses and does NO T2/secure-boot provisioning — the Suicide-Marauder host
    provisioner does that; here we only flash an already-provisioned bundle. Returns the rc.
    """
    manifest = read_bundle_manifest(bundle_dir)

    man_chip = manifest.get("chip")
    if man_chip and man_chip != chip:
        on_line(f"[WARNING] bundle chip is {man_chip!r} but flashing as {chip!r} "
                f"— flash will likely fail or brick; double-check the selected chip")

    # Resolve every entry to (offset, absolute path); collect any missing files first so we can
    # report them all at once instead of failing on the first one.
    pairs: List[Tuple[int, str]] = []
    missing: List[str] = []
    for entry in manifest["files"]:
        abs_path = os.path.join(bundle_dir, entry["file"])
        if not os.path.isfile(abs_path):
            missing.append(entry["file"])
            continue
        pairs.append((_bundle_offset(entry), abs_path))
    if missing:
        on_line("[error] bundle is missing file(s): " + ", ".join(missing))
        return 2

    pairs.sort(key=lambda p: p[0])
    files: List[str] = []
    for off, path in pairs:
        files += [f"0x{off:x}", path]

    # --flash_size detect mirrors flash(): patch the image header to the board's real size so a
    # 4MB board doesn't boot-loop on an image whose header claims 16MB.
    argv = esptool_argv("--chip", chip, "--port", port, "--baud", str(baud),
                        "--before", "default_reset", "--after", "hard_reset",
                        "write_flash", "-z", "--flash_size", "detect", *files)
    return _run_stream(argv, on_line)
