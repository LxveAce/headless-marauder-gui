"""Regression: gui_qt/app.py must import every QtWidgets class it instantiates.

The flasher panel's __init__ builds QSpinBox() controls (the suicide arm-GPIO / max-attempts fields), but
QSpinBox was missing from the `from PyQt5.QtWidgets import (...)` block — so constructing that panel raised
NameError: name 'QSpinBox' is not defined. No test constructed the Qt widget and ruff's F821 wasn't gating CI,
so it went unnoticed. Guard the specific name here (importing the module is enough — it resolves the name).
"""

import pytest

app = pytest.importorskip("gui_qt.app")


def test_qspinbox_name_is_resolvable():
    # QSpinBox is instantiated in the flasher panel; it must be a bound name in the module namespace.
    assert hasattr(app, "QSpinBox")


# _refresh_tables renders through _cap_table_rows so the AP/Station QTableWidgets can't grow without
# bound — the parser keeps every distinct BSSID, so a dense/flooded scan (or a hostile device streaming
# unique BSSIDs) would otherwise rebuild an ever-larger table every 700ms. (Tested at the pure-helper
# layer, not by constructing a live window — PyQt5 + the pytest-qt/PySide binding can't share a process.)
def test_cap_table_rows_bounds_render():
    assert app._cap_table_rows(list(range(10))) == list(range(10))     # within cap: unchanged
    big = list(range(app._MAX_TABLE_ROWS + 250))
    capped = app._cap_table_rows(big)
    assert len(capped) == app._MAX_TABLE_ROWS                          # over cap: bounded
    assert capped == big[:app._MAX_TABLE_ROWS]                         # keeps the first N, in order


def test_cap_table_rows_at_exact_boundary():
    exact = list(range(app._MAX_TABLE_ROWS))
    assert app._cap_table_rows(exact) is exact                        # == cap: returned as-is (no copy)
