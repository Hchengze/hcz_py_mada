"""Finite-difference Laplacian helpers for RSF data."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np

from pymadagascar.core.hypercube import Hypercube
from pymadagascar.io.rsf import RSFArray, read_rsf, write_rsf


class LaplacError(ValueError):
    """Raised when a Laplacian request is invalid."""


def laplac(
    data: Any,
    *,
    axes: int | Sequence[int] | None = None,
    spacing: float | Sequence[float] | None = None,
    boundary: str = "edge",
) -> np.ndarray:
    """Apply a source-aligned graph Laplacian on 1-based RSF axes.

    The sign follows Madagascar's ``laplac2_lop`` convention: each selected
    axis contributes ``center - neighbor`` for existing adjacent samples.
    """

    array = _coerce_real_array(data)
    axes_tuple = _normalize_axes(axes, array.ndim)
    spacings = _normalize_spacings(spacing, axes_tuple)
    _validate_boundary(boundary)

    result = np.zeros_like(array, dtype=np.float64)
    work = array.astype(np.float64, copy=False)
    for rsf_axis, delta in zip(axes_tuple, spacings):
        numpy_axis = array.ndim - rsf_axis
        scale = 1.0 / (delta * delta)
        result += _axis_graph_laplacian(work, numpy_axis) * scale
    dtype = np.float64 if array.dtype == np.dtype("float64") else np.float32
    return np.ascontiguousarray(result.astype(dtype))


def laplac_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    axes: int | Sequence[int] | None = None,
    spacing_from_header: bool = True,
    boundary: str = "edge",
) -> RSFArray:
    """Apply a bounded ``sflaplac`` subset to a real-valued RSF file."""

    rsf = read_rsf(input_path)
    if np.iscomplexobj(rsf.data):
        raise LaplacError("laplac_rsf only supports real-valued data")
    cube = Hypercube.from_header(rsf.header)
    axes_tuple = _normalize_axes(axes, cube.ndim)
    spacing = [cube.axis(axis).d for axis in axes_tuple] if spacing_from_header else None
    if spacing_from_header and any(delta <= 0.0 for delta in spacing):
        raise LaplacError("selected axis d# values must be positive")

    result = laplac(rsf.data, axes=axes_tuple, spacing=spacing, boundary=boundary)
    return write_rsf(output_path, result, rsf.header.copy())


def _axis_graph_laplacian(array: np.ndarray, axis: int) -> np.ndarray:
    contribution = np.zeros_like(array, dtype=np.float64)
    lower_current = [slice(None)] * array.ndim
    lower_neighbor = [slice(None)] * array.ndim
    lower_current[axis] = slice(1, None)
    lower_neighbor[axis] = slice(None, -1)
    contribution[tuple(lower_current)] += (
        array[tuple(lower_current)] - array[tuple(lower_neighbor)]
    )

    upper_current = [slice(None)] * array.ndim
    upper_neighbor = [slice(None)] * array.ndim
    upper_current[axis] = slice(None, -1)
    upper_neighbor[axis] = slice(1, None)
    contribution[tuple(upper_current)] += (
        array[tuple(upper_current)] - array[tuple(upper_neighbor)]
    )
    return contribution


def _coerce_real_array(data: Any) -> np.ndarray:
    array = np.asarray(data)
    if np.iscomplexobj(array):
        raise LaplacError("laplac only supports real-valued data")
    if array.ndim < 1:
        raise LaplacError("laplac requires at least one data axis")
    dtype = np.float64 if array.dtype == np.dtype("float64") else np.float32
    try:
        return np.asarray(array, dtype=dtype)
    except (TypeError, ValueError) as exc:
        raise LaplacError("laplac only supports numeric data") from exc


def _normalize_axes(axes: int | Sequence[int] | None, ndim: int) -> tuple[int, ...]:
    if axes is None:
        values = tuple(range(1, ndim + 1))
    elif isinstance(axes, int):
        values = (int(axes),)
    else:
        values = tuple(int(axis) for axis in axes)
    if not values:
        raise LaplacError("axes must not be empty")
    if len(set(values)) != len(values):
        raise LaplacError("axes must not contain duplicates")
    for axis in values:
        if axis < 1 or axis > ndim:
            raise LaplacError(f"axis must be between 1 and {ndim}, got {axis}")
    return values


def _normalize_spacings(
    spacing: float | Sequence[float] | None,
    axes: tuple[int, ...],
) -> tuple[float, ...]:
    if spacing is None:
        values = (1.0,) * len(axes)
    elif isinstance(spacing, (int, float, np.integer, np.floating)):
        values = (float(spacing),) * len(axes)
    else:
        values = tuple(float(value) for value in spacing)
        if len(values) != len(axes):
            raise LaplacError("spacing length must match selected axes")
    if any(value <= 0.0 for value in values):
        raise LaplacError("spacing values must be positive")
    return values


def _validate_boundary(boundary: str) -> None:
    if str(boundary).strip().lower() != "edge":
        raise LaplacError("boundary= currently supports only edge")
