"""Small signal/data conditioning helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from pymadagascar.core.hypercube import Hypercube
from pymadagascar.io.rsf import RSFArray, read_rsf, write_rsf


class ConditioningError(ValueError):
    """Raised when a signal conditioning request is invalid."""


def shift(
    data: Any,
    shift: int,
    *,
    axis: int = 1,
    fill: float | complex = 0.0,
    circular: bool = False,
) -> np.ndarray:
    """Shift samples along one 1-based RSF axis.

    Positive shifts delay samples toward larger indices. Non-circular shifts
    fill uncovered samples with ``fill``.
    """

    array = np.asarray(data)
    return _shift_array(array, int(shift), axis=axis, fill=fill, circular=circular)


def _shift_array(
    array: np.ndarray,
    amount: int,
    *,
    axis: int,
    fill: float | complex,
    circular: bool,
) -> np.ndarray:
    if array.ndim < 1 or array.ndim > 3:
        raise ConditioningError("shift currently supports 1D, 2D, and 3D data")
    if not np.issubdtype(array.dtype, np.number):
        raise ConditioningError("shift requires numeric data")
    rsf_axis = _validate_axis(axis, array.ndim)
    numpy_axis = array.ndim - rsf_axis
    if circular:
        return np.ascontiguousarray(np.roll(array, amount, axis=numpy_axis))

    result = np.full(array.shape, fill, dtype=_output_dtype(array, fill))
    n = array.shape[numpy_axis]
    if abs(amount) >= n:
        return np.ascontiguousarray(result)

    src = [slice(None)] * array.ndim
    dst = [slice(None)] * array.ndim
    if amount >= 0:
        src[numpy_axis] = slice(0, n - amount)
        dst[numpy_axis] = slice(amount, n)
    else:
        src[numpy_axis] = slice(-amount, n)
        dst[numpy_axis] = slice(0, n + amount)
    result[tuple(dst)] = array[tuple(src)]
    return np.ascontiguousarray(result)


def shifts_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    shift: int,
    axis: int = 1,
    fill: float | complex = 0.0,
    circular: bool = False,
) -> RSFArray:
    """Shift RSF samples along one axis while preserving shape and header."""

    rsf = read_rsf(input_path)
    cube = Hypercube.from_header(rsf.header)
    axis = _validate_axis(axis, cube.ndim)
    result = _shift_array(rsf.data, int(shift), axis=axis, fill=fill, circular=circular)
    return write_rsf(output_path, result, rsf.header.copy())


def clip2(
    data: Any,
    *,
    min_value: float | None = None,
    max_value: float | None = None,
    pclip: float | None = None,
    symmetric: bool = False,
) -> np.ndarray:
    """Clip real data with explicit bounds or percentile-derived bounds.

    Without ``symmetric``, percentile clipping keeps the central ``pclip``
    percent of finite samples. With ``symmetric``, the limit is the ``pclip``
    percentile of absolute amplitude.
    """

    array = np.asarray(data)
    if array.ndim < 1 or array.ndim > 3:
        raise ConditioningError("clip2 currently supports 1D, 2D, and 3D data")
    if np.iscomplexobj(array):
        raise ConditioningError("clip2 currently requires real-valued input")
    if not np.issubdtype(array.dtype, np.number):
        raise ConditioningError("clip2 requires numeric data")

    values = np.asarray(array, dtype=np.float64 if array.dtype == np.dtype("float64") else np.float32)
    lower, upper = _clip_bounds(
        values,
        min_value=min_value,
        max_value=max_value,
        pclip=pclip,
        symmetric=symmetric,
    )
    return np.ascontiguousarray(np.clip(values, lower, upper))


def clip2_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    min_value: float | None = None,
    max_value: float | None = None,
    pclip: float | None = None,
    symmetric: bool = False,
) -> RSFArray:
    """Clip an RSF dataset while preserving shape and header."""

    rsf = read_rsf(input_path)
    result = clip2(
        rsf.data,
        min_value=min_value,
        max_value=max_value,
        pclip=pclip,
        symmetric=symmetric,
    )
    return write_rsf(output_path, result, rsf.header.copy())


def _validate_axis(axis: int, ndim: int) -> int:
    value = int(axis)
    if value < 1 or value > ndim:
        raise ConditioningError(f"axis must be between 1 and {ndim}, got {axis}")
    return value


def _output_dtype(array: np.ndarray, fill: float | complex) -> np.dtype[Any]:
    if np.iscomplexobj(array) or isinstance(fill, complex):
        return np.dtype("complex64")
    if array.dtype == np.dtype("float64"):
        return np.dtype("float64")
    return np.asarray(array, dtype=np.float32).dtype


def _clip_bounds(
    values: np.ndarray,
    *,
    min_value: float | None,
    max_value: float | None,
    pclip: float | None,
    symmetric: bool,
) -> tuple[float, float]:
    if pclip is not None and (min_value is not None or max_value is not None):
        raise ConditioningError("pclip= cannot be combined with min=/max=")

    if pclip is not None:
        percentile = float(pclip)
        if percentile <= 0.0 or percentile > 100.0:
            raise ConditioningError("pclip= must be in the interval (0, 100]")
        finite = values[np.isfinite(values)]
        if finite.size == 0:
            raise ConditioningError("clip2 cannot derive percentile bounds without finite samples")
        if symmetric:
            limit = float(np.percentile(np.abs(finite), percentile))
            return -limit, limit
        tail = 0.5 * (100.0 - percentile)
        return (
            float(np.percentile(finite, tail)),
            float(np.percentile(finite, 100.0 - tail)),
        )

    if min_value is None and max_value is None:
        raise ConditioningError("clip2 requires min=/max= or pclip=")

    if symmetric:
        limits = [abs(float(value)) for value in (min_value, max_value) if value is not None]
        if len(limits) == 2 and not np.isclose(limits[0], limits[1]):
            raise ConditioningError("symmetric explicit min=/max= bounds must have equal magnitude")
        limit = limits[0]
        return -limit, limit

    lower = -np.inf if min_value is None else float(min_value)
    upper = np.inf if max_value is None else float(max_value)
    if lower > upper:
        raise ConditioningError("min= must be less than or equal to max=")
    return lower, upper


__all__ = [
    "ConditioningError",
    "clip2",
    "clip2_rsf",
    "shift",
    "shifts_rsf",
]
