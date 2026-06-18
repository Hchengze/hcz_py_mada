"""Array-operation wrappers for optional C++ kernels."""

from __future__ import annotations

import importlib
import os
from types import ModuleType
from typing import Any

import numpy as np


_DISABLE_VALUES = {"1", "true", "yes", "y", "on"}
_CORE: ModuleType | None = None
_CORE_IMPORT_ERROR: Exception | None = None
_LAST_BACKEND = "numpy"


def _cpp_disabled() -> bool:
    return os.environ.get("PYMADAGASCAR_DISABLE_CPP", "").strip().lower() in _DISABLE_VALUES


def _load_core() -> ModuleType | None:
    global _CORE, _CORE_IMPORT_ERROR
    if _cpp_disabled():
        _CORE = None
        return None
    if _CORE is not None:
        return _CORE
    try:
        _CORE = importlib.import_module("pymadagascar._core")
    except Exception as exc:  # pragma: no cover - exact build failures vary by platform.
        _CORE_IMPORT_ERROR = exc
        _CORE = None
    return _CORE


def cpp_available() -> bool:
    """Return True when the optional C++ extension is importable and enabled."""

    return _load_core() is not None


def backend_name() -> str:
    """Return the backend that would be used for the next call."""

    return "cpp" if cpp_available() else "numpy"


def last_backend() -> str:
    """Return the backend used by the most recent wrapper call."""

    return _LAST_BACKEND


def add_arrays_cpp(a: Any, b: Any) -> np.ndarray:
    """Add two arrays with C++ when available, otherwise NumPy."""

    global _LAST_BACKEND
    a_array = np.asarray(a)
    b_array = np.asarray(b)
    core = _load_core()
    if core is not None:
        _LAST_BACKEND = "cpp"
        return np.asarray(core.add_arrays_cpp(a_array, b_array))
    _LAST_BACKEND = "numpy"
    return np.add(a_array, b_array)


def scale_array_cpp(a: Any, scale: float) -> np.ndarray:
    """Scale an array with C++ when available, otherwise NumPy."""

    global _LAST_BACKEND
    a_array = np.asarray(a)
    core = _load_core()
    if core is not None:
        _LAST_BACKEND = "cpp"
        return np.asarray(core.scale_array_cpp(a_array, float(scale)))
    _LAST_BACKEND = "numpy"
    return np.multiply(a_array, float(scale))


def _reset_core_for_tests() -> None:
    global _CORE, _CORE_IMPORT_ERROR, _LAST_BACKEND
    _CORE = None
    _CORE_IMPORT_ERROR = None
    _LAST_BACKEND = "numpy"

