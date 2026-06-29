"""Shared core for the Headless Marauder apps: serial controller, command catalog,
parser, flasher, capture logger, and self-updater."""

# Single source of truth: report the installed distribution version so this can't drift
# from pyproject again. Falls back to the latest released version for source / frozen runs
# where no dist metadata is present (e.g. PyInstaller bundles).
try:
    from importlib.metadata import version as _pkg_version, PackageNotFoundError
    try:
        __version__ = _pkg_version("headless-marauder")
    except PackageNotFoundError:
        __version__ = "1.3.2"
    del _pkg_version, PackageNotFoundError
except ImportError:  # pragma: no cover - importlib.metadata is stdlib on py>=3.9
    __version__ = "1.3.2"

from .controller import MarauderController
from .parsing import MarauderParser, AP, Station
from .capture import CaptureLogger, default_log_dir
from . import commands
from . import flasher
from . import updater

__all__ = [
    "MarauderController", "MarauderParser", "AP", "Station",
    "CaptureLogger", "default_log_dir",
    "commands", "flasher", "updater", "__version__",
]
