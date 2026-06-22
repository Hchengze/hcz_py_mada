"""Acoustic impedance to reflectivity conversion."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from pymadagascar.io.rsf import RSFArray, read_rsf, write_rsf
from pymadagascar.seismic._utils import numpy_axis, validate_rsf_axis


class AI2ReflError(ValueError):
    """Raised when an acoustic-impedance conversion request is invalid."""


def ai2refl(data: Any, *, axis: int = 1, eps: float | None = None) -> np.ndarray:
    """Convert acoustic impedance to reflection coefficients along one RSF axis."""

    array = _real_array(data, name="data")
    if array.ndim < 1:
        raise AI2ReflError("ai2refl requires at least one dimension")
    axis = validate_rsf_axis(axis, array.ndim)
    np_axis = numpy_axis(axis, array.ndim)
    if array.shape[np_axis] < 1:
        raise AI2ReflError("ai2refl requires a non-empty axis")
    epsilon = np.finfo(np.float32).eps if eps is None else float(eps)
    if epsilon < 0.0:
        raise AI2ReflError("eps= must be non-negative")

    moved = np.moveaxis(array.astype(np.float64, copy=False), np_axis, -1)
    out = np.zeros_like(moved, dtype=np.float64)
    if moved.shape[-1] > 1:
        imp1 = moved[..., :-1]
        imp2 = moved[..., 1:]
        out[..., :-1] = (imp2 - imp1) / (imp2 + imp1 + epsilon)
    result = np.moveaxis(out, -1, np_axis)
    dtype = np.float64 if array.dtype == np.dtype("float64") else np.float32
    return np.ascontiguousarray(result.astype(dtype, copy=False))


def ai2refl_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    axis: int = 1,
    eps: float | None = None,
) -> RSFArray:
    """Apply the bounded ``sfai2refl`` subset to RSF files."""

    rsf = read_rsf(input_path)
    result = ai2refl(rsf.data, axis=axis, eps=eps)
    header = rsf.header.copy()
    header["ai2refl_axis"] = axis
    header["ai2refl_source"] = "../src-master/system/seismic/Mai2refl.c"
    return write_rsf(output_path, result, header)


def _real_array(data: Any, *, name: str) -> np.ndarray:
    array = np.asarray(data)
    if np.iscomplexobj(array):
        raise AI2ReflError(f"{name} must be real-valued")
    if not np.issubdtype(array.dtype, np.number):
        raise AI2ReflError(f"{name} must be numeric")
    dtype = np.float64 if array.dtype == np.dtype("float64") else np.float32
    return np.asarray(array, dtype=dtype)


__all__ = ["AI2ReflError", "ai2refl", "ai2refl_rsf"]
