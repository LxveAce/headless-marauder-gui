"""Regression guards for the hmg-deep-audit-1 SHIP-2 leads (2026-07-14).

Two of the ledgered survivors that are fixable at the source/build layer (no UI-framework wiring),
so they can be tested discriminatingly:

#6 (MED) suicide.provision.validate_args — bounded max_att>=1 and the fail-safe arm pairs but never
   bounded arm_pin / max_att to the NVS u8 the guardcfg field stores. Both GUIs (tui #6, tk #12) and
   the CLI reach validate_args via suicide.build_bundle, so a fat-fingered arm_pin=300 (or a negative
   from a UI that skipped range-checking) was baked into an ARMED board's dead-man config -> an
   unusable/corrupt pin the owner can never trigger to disarm. Fix: reject arm_pin outside [0,255]
   and max_att>255 up front (per-chip GPIO validity beyond the u8 range stays advisory by design).
#9 (MED) build.py — HIDDEN_IMPORTS omitted `suicide` and DATA_FILES bundled nothing under suicide/,
   so the frozen binary's "Provision new bundle" path failed (provision.py is exec'd by file path +
   partition CSVs are read from the package dir at runtime). Fix: hidden-import `suicide` + ship the
   whole suicide/ tree as DATA.

Hardware-free: pure validator + build-spec constants; no device/network/subprocess/PyInstaller run.
"""
import argparse
import importlib.util
import os

import pytest

import suicide


def _va_namespace(**over):
    """A validate_args-shaped Namespace with a sane, in-range baseline (fail-safe arm pair)."""
    ns = dict(kdf_iter=10000, armed=0, arm_pin=27, arm_level=1, arm_pull=2, deadman=1,
              max_att=2, chip="esp32", partitions="x", out="x", variant="fork",
              build_dir=None, nvs_gen_dir=None, no_confirm=True,
              wipe_ota=1, wipe_nvs=1, wipe_spiffs=1, wipe_sd=1, brick=0,
              sd_passes=1, flash_passes=1, fast_wipe=0)
    ns.update(over)
    return argparse.Namespace(**ns)


# ── #6: validate_args enforces the u8 storage bound on arm_pin / max_att ──

def test_validate_args_rejects_out_of_range_arm_pin():
    prov = suicide._get_provisioner()
    with pytest.raises(prov.ProvisionError):
        prov.validate_args(_va_namespace(arm_pin=300))


def test_validate_args_rejects_negative_arm_pin():
    prov = suicide._get_provisioner()
    with pytest.raises(prov.ProvisionError):
        prov.validate_args(_va_namespace(arm_pin=-1))


def test_validate_args_rejects_max_att_over_u8():
    prov = suicide._get_provisioner()
    with pytest.raises(prov.ProvisionError):
        prov.validate_args(_va_namespace(max_att=1000))


def test_validate_args_accepts_a_valid_in_range_config():
    prov = suicide._get_provisioner()
    # a sane in-range config (fail-safe arm pair, valid pin, small max_att) must still pass —
    # guard against over-rejection of legitimate dead-man configs.
    assert prov.validate_args(_va_namespace(arm_pin=27, max_att=3)) is None


# ── #9: the PyInstaller build bundles the suicide package (import + runtime data) ──

def _load_build_module():
    """Load the repo's build.py by path (avoid colliding with the PyPI `build` package)."""
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    spec = importlib.util.spec_from_file_location("hmg_build", os.path.join(here, "build.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_build_hidden_imports_include_suicide():
    build = _load_build_module()
    assert "suicide" in build.HIDDEN_IMPORTS


def test_build_data_files_ship_the_suicide_tree():
    build = _load_build_module()
    # provision.py is exec'd by file path + partition CSVs are read from the package dir at runtime,
    # so the whole suicide/ tree must ship as DATA (a hidden-import alone leaves those file reads out).
    dsts = {dst for _src, dst in build.DATA_FILES}
    srcs = {os.path.basename(str(src).rstrip("/\\")) for src, _dst in build.DATA_FILES}
    assert "suicide" in dsts or "suicide" in srcs
