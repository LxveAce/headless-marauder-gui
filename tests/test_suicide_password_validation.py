"""Regression: the suicide.build_bundle wrapper must enforce validate_password parity + a fresh out_dir.

Two audit findings (portfolio-audit, 2026-07-13):
  * HIGH — the vendored wrapper hashed the password WITHOUT calling provision.validate_password (which
    the canonical provision.build_bundle DOES call). So an over-long (>63 UTF-8 bytes), whitespace-
    wrapped, or `unlock `-prefixed passphrase silently produced a bundle whose bytes the firmware
    clamps/strips differently before hashing — the on-device hash would then never match, and on an
    ARMED board the CORRECT password is counted as a failed attempt and triggers the full-flash
    wipe/brick after max_att. The wrapper now validates the password up front and raises.
  * LOW — build_bundle's default out_dir was a single FIXED reused temp path, so stale .bin artifacts
    from a prior provisioning could be re-hashed into a new manifest. It now mints a unique dir/call.

Hardware-free: generate_nvs_bin (the only esptool/subprocess dependency) is neutralised so the real
wrapper runs end-to-end through the manifest; the bad-password cases raise before it reaches that.
"""
import os

import pytest

import suicide


def _neutralised_get(monkeypatch):
    """Make suicide._get_provisioner() return a provisioner whose only subprocess dependency
    (generate_nvs_bin) is a no-op, so build_bundle runs end-to-end without esptool/hardware."""
    real_get = suicide._get_provisioner

    def spy_get():
        prov = real_get()
        prov.generate_nvs_bin = lambda *a, **k: None
        return prov

    monkeypatch.setattr(suicide, "_get_provisioner", spy_get)


@pytest.mark.parametrize("bad_pw, needle", [
    ("x" * 64, "utf-8 bytes"),          # > 63 bytes -> firmware char[64] clamp
    (" leading-space", "whitespace"),   # leading ASCII space stripped by the serial adapter
    ("trailing-space ", "whitespace"),  # trailing ASCII space
    ("unlock hunter2", "unlock"),       # reserved `unlock ` serial keyword
])
def test_build_bundle_rejects_a_password_the_firmware_would_hash_differently(
        bad_pw, needle, tmp_path, monkeypatch):
    _neutralised_get(monkeypatch)
    with pytest.raises(Exception) as ei:  # noqa: PT011 - ProvisionError class differs per module reload
        suicide.build_bundle(password=bad_pw, out_dir=str(tmp_path))
    # The failure must be the validate_password parity guard, not an unrelated error.
    assert needle in str(ei.value).lower()


def test_build_bundle_accepts_a_valid_password(tmp_path, monkeypatch):
    _neutralised_get(monkeypatch)
    out = suicide.build_bundle(password="reliability-over-power", out_dir=str(tmp_path))
    assert os.path.isfile(os.path.join(out, "bundle.json"))


def test_build_bundle_default_out_dir_is_unique_per_call(monkeypatch):
    _neutralised_get(monkeypatch)
    a = suicide.build_bundle(password="valid-pass-one")
    b = suicide.build_bundle(password="valid-pass-two")
    assert a != b   # a fresh unique dir each call, not one fixed reused path
    assert os.path.isdir(a) and os.path.isdir(b)
