"""Shared helpers for seismic gather processing."""

from __future__ import annotations

from typing import Any

import numpy as np

from pymadagascar.core.axis import Axis
from pymadagascar.core.hypercube import Hypercube
from pymadagascar.io.rsf import RSFHeader


def validate_rsf_axis(axis: int, ndim: int) -> int:
    value = int(axis)
    if value < 1 or value > ndim:
        raise ValueError(f"axis must be between 1 and {ndim}, got {axis}")
    return value


def numpy_axis(axis: int, ndim: int) -> int:
    return ndim - validate_rsf_axis(axis, ndim)


def output_dtype(data: np.ndarray) -> np.dtype[Any]:
    dtype = np.asarray(data).dtype
    if np.issubdtype(dtype, np.complexfloating):
        return np.dtype("complex64")
    if dtype == np.dtype("float64"):
        return np.dtype("float64")
    return np.dtype("float32")


def real_output_dtype(data: np.ndarray) -> np.dtype[Any]:
    dtype = np.asarray(data).dtype
    if np.issubdtype(dtype, np.complexfloating):
        raise ValueError("operation requires real-valued seismic data")
    if dtype == np.dtype("float64"):
        return np.dtype("float64")
    return np.dtype("float32")


def header_without_axis(header: RSFHeader, axis: int) -> RSFHeader:
    cube = Hypercube.from_header(header)
    validate_rsf_axis(axis, cube.ndim)
    axes = [cube.axis(index) for index in range(1, cube.ndim + 1) if index != axis]
    if not axes:
        axes = [Axis(n=1, o=0.0, d=1.0, label="Stack", index=1)]
    return Hypercube(axes).to_header(header.copy())


def broadcast_axis_values(values: np.ndarray, *, axis: int, ndim: int) -> np.ndarray:
    shape = [1] * ndim
    shape[numpy_axis(axis, ndim)] = values.size
    return values.reshape(shape)
