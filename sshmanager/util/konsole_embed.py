from __future__ import annotations

from ctypes import CDLL, c_void_p, c_char_p, c_int
from pathlib import Path
from typing import Optional

from PyQt5.QtWidgets import QWidget
from PyQt5 import sip


_lib: Optional[CDLL] = None
# Store the last error so the UI can display a helpful message
_last_error: Optional[str] = None


def _load_lib() -> Optional[CDLL]:
    """Load the helper library, printing errors when it fails."""
    global _lib, _last_error
    if _lib is None:
        lib_path = Path(__file__).resolve().parent.parent / "libkonsole_embed.so"
        try:
            _lib = CDLL(str(lib_path))
        except OSError as exc:
            _last_error = (
                f"Failed to load {lib_path}: {exc}\n"
                "Run setup.sh to build libkonsole_embed.so and ensure KDE libraries are installed."
            )
            print(_last_error)
            return None
        _lib.createKonsoleSshWidget.argtypes = [
            c_char_p,
            c_char_p,
            c_int,
            c_char_p,
            c_char_p,
            c_void_p,
        ]
        _lib.createKonsoleSshWidget.restype = c_void_p
    return _lib


def create_konsole_widget(
    user: str,
    host: str,
    port: int = 22,
    key: str | None = None,
    initial_cmd: str | None = None,
    parent: Optional[QWidget] = None,
) -> Optional[QWidget]:
    """Create a Konsole widget running ssh via embedded KPart."""
    lib = _load_lib()
    if lib is None:
        return None
    parent_ptr = sip.unwrapinstance(parent) if parent else None
    ptr = lib.createKonsoleSshWidget(
        user.encode(),
        host.encode(),
        port,
        key.encode() if key else None,
        initial_cmd.encode() if initial_cmd else None,
        parent_ptr,
    )
    if not ptr:
        _last_error = (
            "Could not start Konsole. Ensure the 'konsole' and 'konsole-kpart' packages are installed."
        )
        return None
    return sip.wrapinstance(ptr, QWidget)


def get_last_error() -> Optional[str]:
    """Return the most recent error from library loading or widget creation."""
    return _last_error
