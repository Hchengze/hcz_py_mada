"""Small deterministic RSF fixtures for migration tests."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from pymadagascar.io.rsf import RSFArray, RSFHeader, format_from_dtype, write_rsf


def make_1d_rsf(
    path: str | os.PathLike[str] | None = None,
    n: int = 16,
    dtype: Any = np.float32,
) -> RSFArray:
    """Create a deterministic 1-D RSF ramp."""

    data = make_ramp((n,), dtype=dtype)
    header = _default_header(data, labels=("Sample",), units=("sample",))
    return _as_rsf_array(data, header, path)


def make_2d_rsf(
    path: str | os.PathLike[str] | None = None,
    shape: Sequence[int] = (4, 5),
    dtype: Any = np.float32,
) -> RSFArray:
    """Create a deterministic 2-D RSF panel in NumPy shape order."""

    data = make_ramp(shape, dtype=dtype)
    header = _default_header(data, labels=("Fast", "Slow"), units=("sample", "trace"))
    return _as_rsf_array(data, header, path)


def make_3d_rsf(
    path: str | os.PathLike[str] | None = None,
    shape: Sequence[int] = (2, 3, 4),
    dtype: Any = np.float32,
) -> RSFArray:
    """Create a deterministic 3-D RSF cube in NumPy shape order."""

    data = make_ramp(shape, dtype=dtype)
    header = _default_header(
        data,
        labels=("Fast", "Mid", "Slow"),
        units=("sample", "trace", "slice"),
    )
    return _as_rsf_array(data, header, path)


def make_spike(
    shape: Sequence[int] = (16,),
    position: int | Sequence[int] | None = None,
    amplitude: float | complex = 1.0,
    dtype: Any = np.float32,
    path: str | os.PathLike[str] | None = None,
    header: RSFHeader | None = None,
) -> np.ndarray | RSFArray:
    """Create an array with a single nonzero sample."""

    normalized_shape = _normalize_shape(shape)
    data = np.zeros(normalized_shape, dtype=dtype)
    index = _normalize_index(position, normalized_shape)
    data[index] = amplitude
    return _maybe_write(data, header, path)


def make_ramp(
    shape: Sequence[int] = (16,),
    start: float = 0.0,
    step: float = 1.0,
    dtype: Any = np.float32,
    path: str | os.PathLike[str] | None = None,
    header: RSFHeader | None = None,
) -> np.ndarray | RSFArray:
    """Create a deterministic ramp array."""

    normalized_shape = _normalize_shape(shape)
    values = start + step * np.arange(np.prod(normalized_shape), dtype=np.float64)
    data = values.reshape(normalized_shape).astype(dtype)
    return _maybe_write(data, header, path)


def make_sine(
    shape: Sequence[int] = (128,),
    frequency: float = 1.0,
    sample_interval: float = 1.0,
    phase: float = 0.0,
    amplitude: float = 1.0,
    axis: int = -1,
    dtype: Any = np.float32,
    path: str | os.PathLike[str] | None = None,
    header: RSFHeader | None = None,
) -> np.ndarray | RSFArray:
    """Create a sine wave broadcast over the requested shape."""

    normalized_shape = _normalize_shape(shape)
    axis = axis % len(normalized_shape)
    samples = np.arange(normalized_shape[axis], dtype=np.float64) * sample_interval
    line = amplitude * np.sin(2.0 * np.pi * frequency * samples + phase)
    view_shape = [1] * len(normalized_shape)
    view_shape[axis] = normalized_shape[axis]
    data = np.broadcast_to(line.reshape(view_shape), normalized_shape).astype(dtype)
    return _maybe_write(data, header, path)


def make_random(
    shape: Sequence[int] = (16,),
    seed: int = 0,
    dtype: Any = np.float32,
    path: str | os.PathLike[str] | None = None,
    header: RSFHeader | None = None,
) -> np.ndarray | RSFArray:
    """Create deterministic pseudo-random data."""

    normalized_shape = _normalize_shape(shape)
    rng = np.random.default_rng(seed)
    dtype_obj = np.dtype(dtype)
    if np.issubdtype(dtype_obj, np.complexfloating):
        data = (
            rng.standard_normal(normalized_shape)
            + 1j * rng.standard_normal(normalized_shape)
        ).astype(dtype_obj)
    else:
        data = rng.standard_normal(normalized_shape).astype(dtype_obj)
    return _maybe_write(data, header, path)


def _maybe_write(
    data: np.ndarray,
    header: RSFHeader | None,
    path: str | os.PathLike[str] | None,
) -> np.ndarray | RSFArray:
    if path is None:
        return data
    rsf_header = header.copy() if header is not None else _default_header(data)
    return write_rsf(path, data, rsf_header)


def _as_rsf_array(
    data: np.ndarray,
    header: RSFHeader,
    path: str | os.PathLike[str] | None,
) -> RSFArray:
    if path is None:
        return RSFArray(data, header)
    return write_rsf(path, data, header)


def _default_header(
    data: np.ndarray,
    labels: Sequence[str] | None = None,
    units: Sequence[str] | None = None,
) -> RSFHeader:
    header = RSFHeader()
    header.set_dimensions_from_shape(data.shape)
    data_format = format_from_dtype(data.dtype)
    header["data_format"] = data_format
    header["esize"] = np.dtype(data.dtype).itemsize
    ndim = data.ndim
    for axis in range(1, ndim + 1):
        header[f"o{axis}"] = 0.0
        header[f"d{axis}"] = 1.0
        if labels and axis <= len(labels):
            header[f"label{axis}"] = labels[axis - 1]
        if units and axis <= len(units):
            header[f"unit{axis}"] = units[axis - 1]
    return header


def _normalize_shape(shape: Sequence[int]) -> tuple[int, ...]:
    normalized = tuple(int(size) for size in shape)
    if not normalized:
        raise ValueError("shape must contain at least one dimension")
    if any(size < 1 for size in normalized):
        raise ValueError("all shape dimensions must be positive")
    return normalized


def _normalize_index(
    position: int | Sequence[int] | None,
    shape: tuple[int, ...],
) -> tuple[int, ...]:
    if position is None:
        return tuple(size // 2 for size in shape)
    if isinstance(position, int):
        if len(shape) != 1:
            raise ValueError("integer position is only valid for 1-D spikes")
        return (position,)
    index = tuple(int(value) for value in position)
    if len(index) != len(shape):
        raise ValueError("position dimensionality must match shape")
    return index
