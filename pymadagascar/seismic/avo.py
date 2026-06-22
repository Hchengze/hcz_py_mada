"""Bounded source-aligned AVO intercept/gradient utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from pymadagascar.io.rsf import RSFArray, read_rsf, write_rsf


class AVOError(ValueError):
    """Raised when an AVO request is invalid."""


def avo_intercept_gradient(
    data: Any,
    *,
    offsets: Any | None = None,
    o2: float = 0.0,
    d2: float = 1.0,
    half: bool = True,
) -> np.ndarray:
    """Compute the bounded ``sfavo`` intercept/gradient least-squares subset.

    The input follows RSF storage convention: axis 1 is the last NumPy
    dimension (time) and axis 2 is the second-last NumPy dimension (offset).
    The output replaces the offset axis by two components: intercept and
    gradient.
    """

    array = _real_array(data, name="data")
    if array.ndim < 2:
        raise AVOError("avo requires at least two RSF axes: n1=time and n2=offset")
    nh = array.shape[-2]
    if nh < 2:
        raise AVOError("avo requires at least two offsets on RSF axis 2")

    offset_values = _offset_values(offsets, nh=nh, leading_shape=array.shape[:-2], o2=o2, d2=d2, half=half)
    traces = array.astype(np.float64, copy=False)

    if offset_values.ndim == 1:
        h = offset_values.astype(np.float64, copy=False)
        sh = float(np.sum(h))
        sh2 = float(np.sum(h * h))
        det = nh * sh2 - sh * sh
        if det == 0.0:
            raise AVOError("avo offset sampling has zero least-squares determinant")
        sx = np.sum(traces, axis=-2)
        sxh = np.sum(traces * h.reshape((1,) * (traces.ndim - 2) + (nh, 1)), axis=-2)
        intercept = (sx * sh2 - sxh * sh) / det
        gradient = (sxh * nh - sx * sh) / det
    else:
        h = offset_values.astype(np.float64, copy=False)
        sh = np.sum(h, axis=-1)
        sh2 = np.sum(h * h, axis=-1)
        det = nh * sh2 - sh * sh
        if np.any(det == 0.0):
            raise AVOError("avo offset sampling has zero least-squares determinant")
        h_expanded = h[..., :, np.newaxis]
        sx = np.sum(traces, axis=-2)
        sxh = np.sum(traces * h_expanded, axis=-2)
        intercept = (sx * sh2[..., np.newaxis] - sxh * sh[..., np.newaxis]) / det[..., np.newaxis]
        gradient = (sxh * nh - sx * sh[..., np.newaxis]) / det[..., np.newaxis]

    result = np.stack([intercept, gradient], axis=-2)
    dtype = np.float64 if array.dtype == np.dtype("float64") else np.float32
    return np.ascontiguousarray(result.astype(dtype, copy=False))


def avo_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    offset_path: str | Path | None = None,
    half: bool = True,
) -> RSFArray:
    """Apply the bounded ``sfavo`` subset to RSF files."""

    rsf = read_rsf(input_path)
    header = rsf.header.copy()
    if rsf.data.ndim < 2:
        raise AVOError("avo_rsf expects input with n1=time and n2=offset")
    offsets = None
    if offset_path is not None:
        offsets = read_rsf(offset_path).data
    else:
        o2 = header.get_float("o2")
        d2 = header.get_float("d2")
        if o2 is None or d2 is None:
            raise AVOError("avo_rsf requires o2= and d2= when offset= is not supplied")
    result = avo_intercept_gradient(
        rsf.data,
        offsets=offsets,
        o2=float(header.get("o2", 0.0)),
        d2=float(header.get("d2", 1.0)),
        half=half,
    )
    header["n2"] = 2
    header["o2"] = 0.0
    header["d2"] = 1.0
    header["label2"] = "AVO"
    header["avo_components"] = "intercept,gradient"
    header["avo_half_offset"] = "y" if half else "n"
    if offset_path is not None:
        header["avo_offset_source"] = "offset"
    return write_rsf(output_path, result, header)


def _real_array(data: Any, *, name: str) -> np.ndarray:
    array = np.asarray(data)
    if array.ndim < 1:
        raise AVOError(f"{name} must have at least one dimension")
    if np.iscomplexobj(array):
        raise AVOError(f"{name} must be real-valued")
    if not np.issubdtype(array.dtype, np.number):
        raise AVOError(f"{name} must be numeric")
    dtype = np.float64 if array.dtype == np.dtype("float64") else np.float32
    return np.asarray(array, dtype=dtype)


def _offset_values(
    offsets: Any | None,
    *,
    nh: int,
    leading_shape: tuple[int, ...],
    o2: float,
    d2: float,
    half: bool,
) -> np.ndarray:
    if offsets is None:
        scale = 2.0 if half else 1.0
        return (float(o2) + np.arange(nh, dtype=np.float64) * float(d2)) * scale

    values = _real_array(offsets, name="offset")
    if values.ndim == 1:
        if values.size != nh:
            raise AVOError(f"offset length {values.size} does not match n2={nh}")
        return values.astype(np.float64, copy=False)
    expected = leading_shape + (nh,)
    if values.shape != expected:
        raise AVOError(f"offset shape must be {(nh,)} or {expected}, got {values.shape}")
    return values.astype(np.float64, copy=False)


__all__ = ["AVOError", "avo_intercept_gradient", "avo_rsf"]
