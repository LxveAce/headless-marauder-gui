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
