"""Trapezoidal frequency-domain filtering for RSF data."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np

from pymadagascar.core.hypercube import Hypercube
from pymadagascar.io.rsf import RSFArray, read_rsf, write_rsf


class TrapezError(ValueError):
    """Raised when a trapezoidal filter request is invalid."""


def trapez_filter(
    data: Any,
    *,
    d: float = 1.0,
    frequency: Sequence[float] | None = None,
    axis: int = 1,
) -> np.ndarray:
    """Apply a four-corner trapezoidal frequency filter along one RSF axis."""

    array = _coerce_real_array(data)
    if d <= 0.0:
        raise TrapezError("d= must be positive")
    axis = _validate_axis(axis, array.ndim)
    numpy_axis = array.ndim - axis
    n = array.shape[numpy_axis]
    freq = _normalize_frequency(frequency, d=d)
    bins = np.fft.rfftfreq(n, d=d)
    response = trapez_response(bins, freq)

    shape = [1] * array.ndim
    shape[numpy_axis] = response.size
    spectrum = np.fft.rfft(array.astype(np.float64, copy=False), axis=numpy_axis)
    filtered = np.fft.irfft(spectrum * response.reshape(shape), n=n, axis=numpy_axis)
    dtype = np.float64 if array.dtype == np.dtype("float64") else np.float32
    return np.ascontiguousarray(filtered.astype(dtype))


def trapez_response(frequencies: Any, frequency: Sequence[float]) -> np.ndarray:
    """Return the source-aligned sin-squared trapezoidal response."""

    freq = np.asarray(frequencies, dtype=np.float64)
    if freq.ndim != 1:
        raise TrapezError("frequencies must be a 1D array")
    f1, f2, f3, f4 = _validate_corners(tuple(float(value) for value in frequency))
    response = np.zeros_like(freq, dtype=np.float64)

    ramp_up = (freq >= f1) & (freq < f2)
    if f2 > f1:
        t = np.sin(0.5 * np.pi * (f2 - freq[ramp_up]) / (f2 - f1))
        response[ramp_up] = 1.0 - t * t
    response[(freq >= f2) & (freq < f3)] = 1.0
    ramp_down = (freq >= f3) & (freq < f4)
    if f4 > f3:
        t = np.sin(0.5 * np.pi * (f4 - freq[ramp_down]) / (f4 - f3))
        response[ramp_down] = t * t
    return response.astype(np.float32)


def trapez_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    axis: int = 1,
    frequency: Sequence[float] | None = None,
    f1: float | None = None,
    f2: float | None = None,
    f3: float | None = None,
    f4: float | None = None,
    dt: float | None = None,
) -> RSFArray:
    """Apply a bounded ``sftrapez`` subset to a real-valued RSF file."""

    rsf = read_rsf(input_path)
    if np.iscomplexobj(rsf.data):
        raise TrapezError("trapez_rsf only supports real-valued input")
    cube = Hypercube.from_header(rsf.header)
    axis = _validate_axis(axis, cube.ndim)
    axis_obj = cube.axis(axis)
    spacing = axis_obj.d if dt is None else float(dt)
    if spacing <= 0.0:
        raise TrapezError("dt= or selected d# must be positive")

    corners = _corners_from_args(frequency, f1=f1, f2=f2, f3=f3, f4=f4, d=spacing)
    result = trapez_filter(rsf.data, d=spacing, frequency=corners, axis=axis)
    return write_rsf(output_path, result, rsf.header.copy())


def _corners_from_args(
    frequency: Sequence[float] | None,
    *,
    f1: float | None,
    f2: float | None,
    f3: float | None,
    f4: float | None,
    d: float,
) -> tuple[float, float, float, float]:
    if frequency is not None and any(value is not None for value in (f1, f2, f3, f4)):
        raise TrapezError("use either frequency= or f1/f2/f3/f4, not both")
    if frequency is not None:
        return _normalize_frequency(frequency, d=d)
    supplied = (f1, f2, f3, f4)
    if any(value is None for value in supplied):
        return _normalize_frequency(None, d=d)
    return _validate_corners(tuple(float(value) for value in supplied if value is not None))


def _normalize_frequency(
    frequency: Sequence[float] | None,
    *,
    d: float,
) -> tuple[float, float, float, float]:
    nyquist = 0.5 / d
    if frequency is None:
        return (0.1 * nyquist, 0.15 * nyquist, 0.45 * nyquist, 0.5 * nyquist)
    values = tuple(float(value) for value in frequency)
    return _validate_corners(values)


def _validate_corners(values: tuple[float, ...]) -> tuple[float, float, float, float]:
    if len(values) != 4:
        raise TrapezError("frequency= must contain exactly four values")
    if any(value < 0.0 for value in values):
        raise TrapezError("frequency corners must be non-negative")
    if not (values[0] <= values[1] <= values[2] <= values[3]):
        raise TrapezError("frequency corners must satisfy f1 <= f2 <= f3 <= f4")
    if values[0] == values[1] or values[2] == values[3]:
        raise TrapezError("ramp intervals f1-f2 and f3-f4 must have positive width")
    return values  # type: ignore[return-value]


def _coerce_real_array(data: Any) -> np.ndarray:
    array = np.asarray(data)
    if np.iscomplexobj(array):
        raise TrapezError("trapez_filter only supports real-valued input")
    if array.ndim < 1:
        raise TrapezError("trapez_filter requires at least one data axis")
    dtype = np.float64 if array.dtype == np.dtype("float64") else np.float32
    try:
        return np.asarray(array, dtype=dtype)
    except (TypeError, ValueError) as exc:
        raise TrapezError("trapez_filter only supports numeric data") from exc


def _validate_axis(axis: int, ndim: int) -> int:
    value = int(axis)
    if value < 1 or value > ndim:
        raise TrapezError(f"axis must be between 1 and {ndim}, got {axis}")
    return value
