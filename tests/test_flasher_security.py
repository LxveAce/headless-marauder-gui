"""Tests for the hardware-free security guards in marauder_core/flasher.py.

These cover the SSRF/redirect allowlist and the path-traversal sinks that protect the
firmware download + suicide-bundle flash paths, plus the pure chip/variant mapping helpers.
No serial port or board is required.
"""

import os

import pytest

from marauder_core import flasher


# --------------------------------------------------------------------------- #
# SSRF allowlist: _host_allowed / _require_allowed_url
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("host", [
    "api.github.com",
    "github.com",
    "raw.githubusercontent.com",
    "objects.githubusercontent.com",
    "objects-origin.githubusercontent.com",   # *.githubusercontent.com suffix
    "GitHub.com",                              # case-insensitive
    "github.com:443",                          # port stripped
])
def test_host_allowed_accepts_github(host):
    assert flasher._host_allowed(host) is True


@pytest.mark.parametrize("host", [
    None,
    "",
    "evil.com",
    "169.254.169.254",
    "localhost",
    "githubXusercontent.com",
    "raw.githubusercontent.com.evil.com",
    "user@evil.com",                           # userinfo must not smuggle a host
])
def test_host_allowed_rejects_others(host):
    assert flasher._host_allowed(host) is False


@pytest.mark.parametrize("url", [
    "https://api.github.com/repos/x/y/releases/latest",
    "https://raw.githubusercontent.com/a/b/master/FlashFiles/x.bin",
    "https://objects.githubusercontent.com/some/asset",
])
def test_require_allowed_url_accepts(url):
    assert flasher._require_allowed_url(url) == url


@pytest.mark.parametrize("url", [
    "",
    "http://github.com/x",                     # non-https
    "ftp://github.com/x",
    "https://evil.com/x",
    "https://169.254.169.254/latest/meta-data",
    "https://raw.githubusercontent.com.evil.com/x",
])
def test_require_allowed_url_rejects(url):
    with pytest.raises(ValueError):
        flasher._require_allowed_url(url)


# --------------------------------------------------------------------------- #
# Path-traversal sinks: _safe_cache_name / _safe_bundle_join
# --------------------------------------------------------------------------- #

def test_safe_cache_name_accepts_basename():
    assert flasher._safe_cache_name("esp32_marauder_v8.bin") == "esp32_marauder_v8.bin"


@pytest.mark.parametrize("name", [
    "", ".", "..",
    "a/b.bin",
    "../evil.bin",
    "..\\..\\evil.bin",
    "/abs/evil.bin",
    "C:\\evil.bin",
    "sub/dir/x.bin",
])
def test_safe_cache_name_rejects_traversal(name):
    with pytest.raises(ValueError):
        flasher._safe_cache_name(name)


def test_safe_bundle_join_inside_dir(tmp_path):
    joined = flasher._safe_bundle_join(str(tmp_path), "app.bin")
    assert joined == os.path.join(str(tmp_path), "app.bin")


@pytest.mark.parametrize("name", [
    "../escape.bin",
    "..\\escape.bin",
    "/etc/passwd",
    "nested/app.bin",
])
def test_safe_bundle_join_rejects_escape(tmp_path, name):
    with pytest.raises(ValueError):
        flasher._safe_bundle_join(str(tmp_path), name)


# --------------------------------------------------------------------------- #
# Pure chip/variant mapping helpers
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("variant,chip", [
    ("esp32_marauder_multiboardS3", "esp32s3"),
    ("esp32_marauder_flipper", "esp32s2"),
    ("esp32_marauder_rev_feather", "esp32s2"),
    ("esp32_marauder_mini_v3", "esp32c5"),
    ("esp32c5devkitc1", "esp32c5"),
    ("esp32_marauder_old_hardware", "esp32"),
    ("esp32_marauder_v8", "esp32"),
])
def test_chip_of_variant(variant, chip):
    assert flasher._chip_of_variant(variant) == chip


def test_variant_label_longest_match_wins():
    # "esp32c5devkitc1" must beat the shorter "kit" suffix.
    assert flasher._variant_label("esp32c5devkitc1") == "ESP32-C5 DevKitC-1"
    # "mini_v3" must beat "mini".
    assert flasher._variant_label("esp32_marauder_mini_v3") == "Marauder Mini v3 (ESP32-C5)"


def test_variant_label_unknown_passthrough():
    assert flasher._variant_label("totally_unknown_board") == "totally_unknown_board"


@pytest.mark.parametrize("env,family", [
    ("cyd_2432s028", "esp32"),              # no hint -> classic default
    ("m5cardputer", "esp32s3"),             # "cardputer"
    ("esp32-s3-devkitc1", "esp32s3"),       # "-s3"
    ("nm-cyd-c5", "esp32c5"),
    ("nesso-n1", "esp32c6"),
    ("some-board-c6", "esp32c6"),
])
def test_bruce_family(env, family):
    assert flasher._bruce_family(env) == family


def test_esptool_argv_shape():
    argv = flasher.esptool_argv("version")
    assert argv[1:] == ["-m", "esptool", "version"]
