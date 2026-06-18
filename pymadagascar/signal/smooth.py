"""Small NumPy smoothing helpers for RSF data."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Literal

import numpy as np

from pymadagascar.io.rsf import RSFArray, read_rsf, write_rsf


SmoothKind = Literal["triangle", "box"]


class SmoothError(ValueError):
    """Raised when a smoothing request is invalid."""


def triangle_smooth(
    data: Any,
    rect: int | Sequence[int] | Mapping[int, int],
    axes: int | Sequence[int] | None = None,
    repeat: int = 1,
) -> np.ndarray:
    """Apply separable triangle smoothing along RSF-style axes.

    ``rect`` follows the Madagascar convention of a smoothing radius. A value
    of 1 is a no-op. Axis numbers are 1-based RSF axes, so axis 1 is the last
    NumPy dimension.
    """

    return _smooth(data, rect=rect, axes=axes, repeat=repeat, kind="triangle")


def box_smooth(
    data: Any,
    rect: int | Sequence[int] | Mapping[int, int],
    axes: int | Sequence[int] | None = None,
    repeat: int = 1,
) -> np.ndarray:
    """Apply separable centered box smoothing along RSF-style axes."""

    return _smooth(data, rect=rect, axes=axes, repeat=repeat, kind="box")


def smooth_rsf(
    input_path: str | Path,
    output_path: str | Path,
    rect: int | Sequence[int] | Mapping[int, int],
    axes: int | Sequence[int] | None = None,
    repeat: int = 1,
    kind: SmoothKind = "triangle",
) -> RSFArray:
    """Smooth a real-valued RSF file and write a shape-preserving output."""

    rsf = read_rsf(input_path)
    if kind == "triangle":
        result = triangle_smooth(rsf.data, rect=rect, axes=axes, repeat=repeat)
    elif kind == "box":
        result = box_smooth(rsf.data, rect=rect, axes=axes, repeat=repeat)
    else:
        raise SmoothError("kind must be 'triangle' or 'box'")
    return write_rsf(output_path, np.ascontiguousarray(result), rsf.header.copy())


def _smooth(
    data: Any,
    *,
    rect: int | Sequence[int] | Mapping[int, int],
    axes: int | Sequence[int] | None,
    repeat: int,
    kind: SmoothKind,
) -> np.ndarray:
    array = _coerce_real_array(data)
    axes_tuple = _normalize_axes(axes, array.ndim)
    rects = _normalize_rects(rect, axes_tuple, array.ndim)
    repeats = _normalize_repeat(repeat)

    result = array.copy()
    for rsf_axis in axes_tuple:
        radius = rects[rsf_axis]
        if radius <= 1:
            continue
        kernel = _triangle_kernel(radius) if kind == "triangle" else _box_kernel(radius)
        numpy_axis = array.ndim - rsf_axis
        for _ in range(repeats):
            result = _apply_kernel_along_axis(result, kernel, numpy_axis)
    return np.ascontiguousarray(result.astype(array.dtype, copy=False))


def _coerce_real_array(data: Any) -> np.ndarray:
    array = np.asarray(data)
    if np.iscomplexobj(array):
        raise SmoothError("smoothing currently supports real-valued data only")
    if array.ndim < 1 or array.ndim > 3:
        raise SmoothError("smoothing currently supports 1D, 2D, and 3D data")

    if array.dtype == np.dtype("float64"):
        dtype = np.float64
    else:
        dtype = np.float32
    try:
        return np.asarray(array, dtype=dtype)
    except (TypeError, ValueError) as exc:
        raise SmoothError("smoothing only supports numeric data") from exc


def _normalize_axes(axes: int | Sequence[int] | None, ndim: int) -> tuple[int, ...]:
    if axes is None:
        values = tuple(range(1, ndim + 1))
    elif isinstance(axes, int):
        values = (axes,)
    else:
        values = tuple(int(axis) for axis in axes)
    if not values:
        raise SmoothError("axes must not be empty")
    if len(set(values)) != len(values):
        raise SmoothError("axes must not contain duplicates")
    for axis in values:
        if axis < 1 or axis > ndim:
            raise SmoothError(f"axis must be between 1 and {ndim}, got {axis}")
    return values


def _normalize_rects(
    rect: int | Sequence[int] | Mapping[int, int],
    axes: tuple[int, ...],
    ndim: int,
) -> dict[int, int]:
    if isinstance(rect, Mapping):
        rects = {int(axis): _normalize_rect(value, axis=int(axis)) for axis, value in rect.items()}
    elif isinstance(rect, int):
        rects = {axis: _normalize_rect(rect, axis=axis) for axis in axes}
    else:
        values = tuple(int(value) for value in rect)
        if len(values) == ndim:
            rects = {axis: _normalize_rect(value, axis=axis) for axis, value in enumerate(values, start=1)}
        elif len(values) == len(axes):
            rects = {axis: _normalize_rect(value, axis=axis) for axis, value in zip(axes, values)}
        else:
            raise SmoothError("rect length must match selected axes or all data dimensions")

    for axis in rects:
        if axis < 1 or axis > ndim:
            raise SmoothError(f"rect axis must be between 1 and {ndim}, got {axis}")
    return {axis: rects.get(axis, 1) for axis in axes}


def _normalize_rect(value: int, *, axis: int) -> int:
    radius = int(value)
    if radius < 1:
        raise SmoothError(f"rect{axis}= must be >= 1")
    return radius


def _normalize_repeat(value: int) -> int:
    repeat = int(value)
    if repeat < 1:
        raise SmoothError("repeat= must be >= 1")
    return repeat


def _triangle_kernel(rect: int) -> np.ndarray:
    left = np.arange(1, rect + 1, dtype=np.float64)
    right = np.arange(rect - 1, 0, -1, dtype=np.float64)
    kernel = np.concatenate([left, right])
    kernel /= float(rect * rect)
    return kernel


def _box_kernel(rect: int) -> np.ndarray:
    width = 2 * rect - 1
    return np.full(width, 1.0 / float(width), dtype=np.float64)


def _apply_kernel_along_axis(array: np.ndarray, kernel: np.ndarray, axis: int) -> np.ndarray:
    radius = kernel.size // 2
    if radius == 0:
        return array.copy()

    moved = np.moveaxis(array, axis, -1)
    flat = moved.reshape(-1, moved.shape[-1])
    padded = np.pad(flat, ((0, 0), (radius, radius)), mode="edge")
    smoothed = np.empty_like(flat, dtype=np.float64)
    for row, padded_row in enumerate(padded):
        smoothed[row] = np.convolve(padded_row, kernel, mode="valid")
    return np.moveaxis(smoothed.reshape(moved.shape), -1, axis)
