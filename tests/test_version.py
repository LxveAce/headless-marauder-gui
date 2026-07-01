"""Version single-source guard.

marauder_core/__init__.py falls back to a hardcoded version string when no installed-dist
metadata is present (PyInstaller-frozen binaries and bare source runs). If that fallback
drifts from pyproject.toml, every frozen binary reports the wrong version. Lock them together.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _pyproject_version() -> str:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    m = re.search(r'(?m)^version\s*=\s*"([^"]+)"', text)
    assert m, "no version field found in pyproject.toml"
    return m.group(1)


def _init_fallback_versions() -> list:
    text = (ROOT / "marauder_core" / "__init__.py").read_text(encoding="utf-8")
    return re.findall(r'__version__\s*=\s*"([^"]+)"', text)


def test_fallback_matches_pyproject():
    proj = _pyproject_version()
    fallbacks = _init_fallback_versions()
    assert fallbacks, "no hardcoded __version__ fallback found in marauder_core/__init__.py"
    for fb in fallbacks:
        assert fb == proj, (
            f"frozen-binary version fallback {fb!r} != pyproject version {proj!r}; "
            "bump both together"
        )
