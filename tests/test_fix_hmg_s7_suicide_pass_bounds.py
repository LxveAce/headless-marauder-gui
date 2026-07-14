"""S7 (LOW) — bound suicide sd_passes / flash_passes to the NVS u8 range in validate_args.

`validate_args` bounded arm_pin / max_att to the guardcfg u8 (63d3b78) but left the overwrite-pass
counts sd_passes / flash_passes unbounded — the SAME `_u8` storage class. The CLI coerces them via
the `_u8` argparse type, but the GUI / programmatic callers (web, tk, tui, Qt, cyber-controller) reach
validate_args through `suicide.build_bundle`, which constructs the Namespace directly and bypasses
that coercion. An out-of-range sd_passes / flash_passes then flowed into the u8 NVS row
(`str(args.sd_passes)`) -> a corrupt nvs-gen / a wipe-pass count the firmware can't hold. Bounded to
[0, 255] in validate_args (0 stays valid = skip that overwrite stage). Kept in parity with the
universal-flasher sibling.

Discriminating (fail on buggy HEAD, pass on the fix):
  - test_sd_passes_over_u8_rejected / test_flash_passes_over_u8_rejected / test_passes_negative_rejected
Guards (pass on both HEAD and the fix):
  - test_passes_boundary_and_zero_accepted (0 = skip stage; 255 = top of u8 range)
  - test_valid_passes_still_accepted
"""
import argparse

import pytest

import suicide

prov = suicide._get_provisioner()
ProvisionError = prov.ProvisionError


def _va(**over):
    """A validate_args-shaped Namespace with a sane, in-range baseline (fail-safe arm pair)."""
    ns = dict(kdf_iter=10000, armed=0, arm_pin=27, arm_level=1, arm_pull=2, deadman=1,
              max_att=2, chip="esp32", partitions="x", out="x", variant="fork",
              build_dir=None, nvs_gen_dir=None, no_confirm=True,
              wipe_ota=1, wipe_nvs=1, wipe_spiffs=1, wipe_sd=1, brick=0,
              sd_passes=1, flash_passes=1, fast_wipe=0)
    ns.update(over)
    return argparse.Namespace(**ns)


# ── discriminating ─────────────────────────────────────────────────────────────────────────────
def test_sd_passes_over_u8_rejected():
    with pytest.raises(ProvisionError):
        prov.validate_args(_va(sd_passes=300))


def test_flash_passes_over_u8_rejected():
    with pytest.raises(ProvisionError):
        prov.validate_args(_va(flash_passes=300))


def test_passes_negative_rejected():
    with pytest.raises(ProvisionError):
        prov.validate_args(_va(sd_passes=-1))


# ── guards (unchanged on both HEAD and fix) ──────────────────────────────────────────────────────
def test_passes_boundary_and_zero_accepted():
    # 0 = skip that overwrite stage (valid); 255 = top of the u8 range (in bounds). Neither raises.
    assert prov.validate_args(_va(sd_passes=0, flash_passes=255)) is None


def test_valid_passes_still_accepted():
    assert prov.validate_args(_va()) is None


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
