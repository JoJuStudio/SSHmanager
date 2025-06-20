from __future__ import annotations

from ctypes import CDLL, c_void_p, c_char_p, c_int
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import QWidget
from PyQt6 import sip


_lib: Optional[CDLL] = None


def _load_lib() -> CDLL:
    global _lib
    if _lib is None:
        lib_path = Path(__file__).resolve().parent.parent / "libkonsole_embed.so"
        _lib = CDLL(str(lib_path))
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
        return None
    return sip.wrapinstance(ptr, QWidget)
