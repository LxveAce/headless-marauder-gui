"""Guard: ESP32-C5's 2nd-stage bootloader offset must be 0x2000, never 0x0 (a brick).

Mirrors the fix verified against esptool's BOOTLOADER_FLASH_OFFSET (c5/p4/h4=0x2000; s3 + other RISC-V
parts=0x0; classic esp32/s2=0x1000)."""
from __future__ import annotations

from marauder_core.flasher import _bootloader_offset


def test_c5_bootloader_is_0x2000_not_0x0():
    assert _bootloader_offset("esp32c5") == "0x2000"


def test_classic_and_s3_offsets_unchanged():
    assert _bootloader_offset("esp32") == "0x1000"
    assert _bootloader_offset("esp32s2") == "0x1000"
    assert _bootloader_offset("esp32s3") == "0x0"
    assert _bootloader_offset("esp32c3") == "0x0"
    assert _bootloader_offset("esp32c6") == "0x0"
