"""Regression: the suicide.build_bundle wrapper must pass flash_passes + fast_wipe.

build_nvs_rows (provision.py) reads args.flash_passes and args.fast_wipe with bare attribute
access, but the programmatic build_bundle wrapper's argparse.Namespace used to OMIT both — so
every GUI "Provision new bundle" attempt (Tk gui/flasher_window.py + Qt gui_qt/app.py) died with
`AttributeError: 'Namespace' object has no attribute 'flash_passes'`, swallowed into
"[error] provisioning failed: ...". The CLI path was unaffected (build_arg_parser defines
--flash-passes/--fast-wipe with defaults 1/0), only the wrapper drifted.

These tests are hardware-free: build_bundle's only esptool/subprocess dependency is
generate_nvs_bin, which is neutralised so the real wrapper runs end-to-end through the manifest.
"""

import argparse
import inspect

import pytest

import suicide


# ── the wrapper exposes the two knobs with the CLI-matching defaults ───────────────────────────
def test_build_bundle_signature_carries_flash_passes_and_fast_wipe():
    params = inspect.signature(suicide.build_bundle).parameters
    assert "flash_passes" in params
    assert "fast_wipe" in params
    assert params["flash_passes"].default == 1   # mirrors provision.py --flash-passes default
    assert params["fast_wipe"].default == 0      # mirrors provision.py --fast-wipe default


# ── build_nvs_rows genuinely consumes them (the params are not cosmetic) ───────────────────────
def _base_namespace(**over):
    ns = dict(kdf_iter=10000, armed=0, arm_pin=27, arm_level=1, arm_pull=2, deadman=1,
              max_att=2, wipe_ota=1, wipe_nvs=1, wipe_spiffs=1, wipe_sd=1, brick=0,
              sd_passes=1, flash_passes=1, fast_wipe=0)
    ns.update(over)
    return argparse.Namespace(**ns)


def test_build_nvs_rows_emits_flash_passes_and_fast_wipe():
    prov = suicide._get_provisioner()
    rows = prov.build_nvs_rows(_base_namespace(), b"\x00" * prov.SALT_LEN, b"\x11" * 32)
    keys = {r[0] for r in rows}
    assert "flash_passes" in keys
    assert "fast_wipe" in keys


def test_build_nvs_rows_without_the_attrs_still_raises():
    # Proves the wrapper MUST supply them — a Namespace missing them is the original crash.
    prov = suicide._get_provisioner()
    ns = _base_namespace()
    del ns.flash_passes
    del ns.fast_wipe
    with pytest.raises(AttributeError):
        prov.build_nvs_rows(ns, b"\x00" * prov.SALT_LEN, b"\x11" * 32)


# ── end-to-end: the real build_bundle Namespace reaches build_nvs_rows intact ───────────────────
def test_build_bundle_wires_flash_passes_and_fast_wipe_into_the_namespace(tmp_path, monkeypatch):
    real_get = suicide._get_provisioner
    captured = {}

    def spy_get():
        prov = real_get()
        real_rows = prov.build_nvs_rows

        def wrapped_rows(args, salt, pwhash):
            captured["args"] = args
            return real_rows(args, salt, pwhash)

        prov.build_nvs_rows = wrapped_rows
        prov.generate_nvs_bin = lambda *a, **k: None  # the only esptool/subprocess dependency
        return prov

    monkeypatch.setattr(suicide, "_get_provisioner", spy_get)

    # No build_dir -> the manifest just warns about missing firmware bins; provisioning still runs.
    suicide.build_bundle(password="regression-pw", out_dir=str(tmp_path), fast_wipe=1, flash_passes=3)

    args = captured["args"]
    assert args.flash_passes == 3   # passthrough, not the default
    assert args.fast_wipe == 1
