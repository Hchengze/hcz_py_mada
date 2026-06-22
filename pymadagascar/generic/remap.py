"""Small interpolation, remap, and warp utilities for RSF data."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from pymadagascar.core.hypercube import Hypercube
from pymadagascar.io.rsf import RSFArray, RSFHeader, read_rsf, write_rsf


class RemapError(ValueError):
    """Raised when a remap/interpolation request is invalid."""


def remap1(
    data: Any,
    *,
    axis: int = 1,
    n: int | None = None,
    o: float | None = None,
    d: float | None = None,
    input_o: float = 0.0,
    input_d: float = 1.0,
    fill_value: float = 0.0,
    order: int = 1,
) -> np.ndarray:
    """Resample one regular axis with a bounded linear ``sfremap1`` subset."""

    if int(order) != 1:
        raise RemapError("remap1 currently supports order=1 linear interpolation only")
    array = _coerce_real_array(data)
    rsf_axis = _validate_axis(axis, array.ndim)
    numpy_axis = array.ndim - rsf_axis
    input_d = _nonzero_float(input_d, "input_d")
    old_n = array.shape[numpy_axis]
    output_n = _normalize_n(n, old_n)
    output_o = float(input_o) if o is None else float(o)
    output_d = input_d if d is None else _nonzero_float(d, "d")
    output_coords = output_o + np.arange(output_n, dtype=np.float64) * output_d
    return _interp_along_axis(
        array,
        axis=numpy_axis,
        input_o=float(input_o),
        input_d=input_d,
        output_coords=output_coords,
        fill_value=float(fill_value),
    )


def remap1_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    axis: int = 1,
    n: int | None = None,
    o: float | None = None,
    d: float | None = None,
    fill_value: float = 0.0,
    order: int = 1,
) -> RSFArray:
    """Apply the bounded ``sfremap1`` regular-axis remap to an RSF file."""

    rsf = read_rsf(input_path)
    cube = Hypercube.from_header(rsf.header)
    axis = _validate_axis(axis, cube.ndim)
    axis_obj = cube.axis(axis)
    output_n = _normalize_n(n, axis_obj.n)
    output_o = axis_obj.o if o is None else float(o)
    output_d = axis_obj.d if d is None else _nonzero_float(d, "d")
    result = remap1(
        rsf.data,
        axis=axis,
        n=output_n,
        o=output_o,
        d=output_d,
        input_o=axis_obj.o,
        input_d=axis_obj.d,
        fill_value=fill_value,
        order=order,
    )
    header = cube.update_axis(axis, n=output_n, o=output_o, d=output_d).to_header(rsf.header)
    header["remap1_order"] = 1
    return write_rsf(output_path, result, header)


def spline(
    data: Any,
    *,
    axis: int = 1,
    n: int | None = None,
    o: float | None = None,
    d: float | None = None,
    input_o: float = 0.0,
    input_d: float = 1.0,
    fill_value: float = 0.0,
) -> np.ndarray:
    """Resample one regular axis with a pure-NumPy natural cubic spline."""

    array = _coerce_real_array(data)
    rsf_axis = _validate_axis(axis, array.ndim)
    numpy_axis = array.ndim - rsf_axis
    input_d = _nonzero_float(input_d, "input_d")
    old_n = array.shape[numpy_axis]
    if old_n < 2:
        raise RemapError("spline interpolation requires at least two input samples")
    output_n = _normalize_n(n, old_n)
    output_o = float(input_o) if o is None else float(o)
    output_d = input_d if d is None else _nonzero_float(d, "d")
    output_coords = output_o + np.arange(output_n, dtype=np.float64) * output_d
    return _natural_cubic_along_axis(
        array,
        axis=numpy_axis,
        input_o=float(input_o),
        input_d=input_d,
        output_coords=output_coords,
        fill_value=float(fill_value),
    )


def spline_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    axis: int = 1,
    n: int | None = None,
    o: float | None = None,
    d: float | None = None,
    fill_value: float = 0.0,
) -> RSFArray:
    """Apply the bounded ``sfspline`` natural-cubic subset to an RSF file."""

    rsf = read_rsf(input_path)
    cube = Hypercube.from_header(rsf.header)
    axis = _validate_axis(axis, cube.ndim)
    axis_obj = cube.axis(axis)
    output_n = _normalize_n(n, axis_obj.n)
    output_o = axis_obj.o if o is None else float(o)
    output_d = axis_obj.d if d is None else _nonzero_float(d, "d")
    result = spline(
        rsf.data,
        axis=axis,
        n=output_n,
        o=output_o,
        d=output_d,
        input_o=axis_obj.o,
        input_d=axis_obj.d,
        fill_value=fill_value,
    )
    header = cube.update_axis(axis, n=output_n, o=output_o, d=output_d).to_header(rsf.header)
    header["spline_boundary"] = "natural"
    return write_rsf(output_path, result, header)


def t2warp(
    data: Any,
    *,
    axis: int = 1,
    inverse: bool = False,
    pad: int | None = None,
    input_o: float = 0.0,
    input_d: float = 1.0,
    original_n: int | None = None,
    fill_value: float = 0.0,
) -> np.ndarray:
    """Apply a bounded linear ``sft2warp`` time-squared coordinate warp."""

    array = _coerce_real_array(data)
    rsf_axis = _validate_axis(axis, array.ndim)
    numpy_axis = array.ndim - rsf_axis
    input_d = _positive_float(input_d, "input_d")
    input_coords = float(input_o) + np.arange(array.shape[numpy_axis], dtype=np.float64) * input_d
    if np.any(input_coords < 0.0):
        raise RemapError("t2warp requires nonnegative input coordinates")

    if inverse:
        output_n = _normalize_n(original_n, array.shape[numpy_axis])
        if output_n < 2:
            raise RemapError("inverse t2warp output length must be at least 2")
        output_o = float(np.sqrt(input_coords[0]))
        output_d = (float(np.sqrt(input_coords[-1])) - output_o) / float(output_n - 1)
        sample_coords = (output_o + np.arange(output_n, dtype=np.float64) * output_d) ** 2
    else:
        output_n = _normalize_n(pad, array.shape[numpy_axis])
        if output_n < 2:
            raise RemapError("t2warp output length must be at least 2")
        output_o = input_coords[0] ** 2
        output_d = (input_coords[-1] ** 2 - output_o) / float(output_n - 1)
        output_tau = output_o + np.arange(output_n, dtype=np.float64) * output_d
        sample_coords = np.sqrt(np.maximum(output_tau, 0.0))

    return _interp_along_axis(
        array,
        axis=numpy_axis,
        input_o=float(input_o),
        input_d=input_d,
        output_coords=sample_coords,
        fill_value=float(fill_value),
    )


def t2warp_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    axis: int = 1,
    inverse: bool = False,
    pad: int | None = None,
    fill_value: float = 0.0,
) -> RSFArray:
    """Apply the bounded ``sft2warp`` subset to an RSF file."""

    rsf = read_rsf(input_path)
    cube = Hypercube.from_header(rsf.header)
    axis = _validate_axis(axis, cube.ndim)
    axis_obj = cube.axis(axis)
    original_key = f"n{axis}_t2warp"

    if inverse:
        output_n = int(rsf.header.get(original_key, axis_obj.n))
        if output_n < 2:
            raise RemapError("inverse t2warp output length must be at least 2")
        tau0 = axis_obj.o
        tau1 = axis_obj.o + (axis_obj.n - 1) * axis_obj.d
        if tau0 < 0.0 or tau1 < 0.0:
            raise RemapError("inverse t2warp requires nonnegative squared-time axis")
        output_o = float(np.sqrt(tau0))
        output_d = (float(np.sqrt(tau1)) - output_o) / float(output_n - 1)
        result = t2warp(
            rsf.data,
            axis=axis,
            inverse=True,
            input_o=axis_obj.o,
            input_d=axis_obj.d,
            original_n=output_n,
            fill_value=fill_value,
        )
        header = cube.update_axis(axis, n=output_n, o=output_o, d=output_d).to_header(rsf.header)
        if original_key in header:
            del header[original_key]
    else:
        output_n = _normalize_n(pad, axis_obj.n)
        if output_n < 2:
            raise RemapError("t2warp output length must be at least 2")
        t0 = axis_obj.o
        t1 = axis_obj.o + (axis_obj.n - 1) * axis_obj.d
        if t0 < 0.0 or t1 < 0.0:
            raise RemapError("t2warp requires nonnegative input axis coordinates")
        output_o = t0 * t0
        output_d = (t1 * t1 - output_o) / float(output_n - 1)
        result = t2warp(
            rsf.data,
            axis=axis,
            inverse=False,
            pad=output_n,
            input_o=axis_obj.o,
            input_d=axis_obj.d,
            fill_value=fill_value,
        )
        header = cube.update_axis(axis, n=output_n, o=output_o, d=output_d).to_header(rsf.header)
        header[original_key] = axis_obj.n

    header["t2warp_interpolation"] = "linear"
    return write_rsf(output_path, result, header)


def _interp_along_axis(
    array: np.ndarray,
    *,
    axis: int,
    input_o: float,
    input_d: float,
    output_coords: np.ndarray,
    fill_value: float,
) -> np.ndarray:
    old_n = array.shape[axis]
    input_coords = input_o + np.arange(old_n, dtype=np.float64) * input_d
    moved = np.moveaxis(array, axis, -1)
    flat = moved.reshape(-1, old_n)
    out = np.empty((flat.shape[0], output_coords.size), dtype=np.float64)
    if input_coords[0] <= input_coords[-1]:
        xp = input_coords
        reverse = False
    else:
        xp = input_coords[::-1]
        reverse = True
    for irow, row in enumerate(flat):
        fp = row[::-1] if reverse else row
        out[irow] = np.interp(output_coords, xp, fp, left=fill_value, right=fill_value)
    result = out.reshape(moved.shape[:-1] + (output_coords.size,))
    result = np.moveaxis(result, -1, axis)
    return np.ascontiguousarray(_float_output_dtype(result, array.dtype))


def _natural_cubic_along_axis(
    array: np.ndarray,
    *,
    axis: int,
    input_o: float,
    input_d: float,
    output_coords: np.ndarray,
    fill_value: float,
) -> np.ndarray:
    old_n = array.shape[axis]
    input_coords = input_o + np.arange(old_n, dtype=np.float64) * input_d
    moved = np.moveaxis(array, axis, -1)
    flat = moved.reshape(-1, old_n)
    out = np.empty((flat.shape[0], output_coords.size), dtype=np.float64)
    for irow, row in enumerate(flat):
        out[irow] = _natural_cubic_eval(input_coords, row.astype(np.float64), output_coords, fill_value)
    result = out.reshape(moved.shape[:-1] + (output_coords.size,))
    result = np.moveaxis(result, -1, axis)
    return np.ascontiguousarray(_float_output_dtype(result, array.dtype))


def _natural_cubic_eval(x: np.ndarray, y: np.ndarray, output_x: np.ndarray, fill_value: float) -> np.ndarray:
    if x[0] > x[-1]:
        x = x[::-1]
        y = y[::-1]
    if np.any(np.diff(x) <= 0.0):
        raise RemapError("spline input coordinates must be strictly monotonic")
    h = np.diff(x)
    n = x.size
    second = np.zeros(n, dtype=np.float64)
    if n > 2:
        matrix = np.zeros((n - 2, n - 2), dtype=np.float64)
        rhs = np.zeros(n - 2, dtype=np.float64)
        for row in range(n - 2):
            i = row + 1
            if row > 0:
                matrix[row, row - 1] = h[i - 1]
            matrix[row, row] = 2.0 * (h[i - 1] + h[i])
            if row < n - 3:
                matrix[row, row + 1] = h[i]
            rhs[row] = 6.0 * ((y[i + 1] - y[i]) / h[i] - (y[i] - y[i - 1]) / h[i - 1])
        second[1:-1] = np.linalg.solve(matrix, rhs)

    result = np.full(output_x.shape, fill_value, dtype=np.float64)
    inside = (output_x >= x[0]) & (output_x <= x[-1])
    if not np.any(inside):
        return result
    indices = np.searchsorted(x, output_x[inside], side="right") - 1
    indices = np.clip(indices, 0, n - 2)
    xi = output_x[inside]
    hi = x[indices + 1] - x[indices]
    a = (x[indices + 1] - xi) / hi
    b = (xi - x[indices]) / hi
    values = (
        a * y[indices]
        + b * y[indices + 1]
        + ((a**3 - a) * second[indices] + (b**3 - b) * second[indices + 1]) * hi**2 / 6.0
    )
    result[inside] = values
    return result


def _coerce_real_array(data: Any) -> np.ndarray:
    array = np.asarray(data)
    if array.ndim < 1:
        raise RemapError("remap input must have at least one dimension")
    if np.iscomplexobj(array):
        raise RemapError("remap tools require real-valued input")
    if not np.issubdtype(array.dtype, np.number):
        raise RemapError("remap tools require numeric input")
    return np.asarray(array, dtype=np.float64 if array.dtype == np.dtype("float64") else np.float32)


def _float_output_dtype(data: np.ndarray, source_dtype: np.dtype[Any]) -> np.ndarray:
    if np.dtype(source_dtype) == np.dtype("float64"):
        return np.asarray(data, dtype=np.float64)
    return np.asarray(data, dtype=np.float32)


def _validate_axis(axis: int, ndim: int) -> int:
    value = int(axis)
    if value < 1 or value > ndim:
        raise RemapError(f"axis must be between 1 and {ndim}, got {axis}")
    return value


def _normalize_n(value: int | None, default: int | None) -> int:
    if value is None:
        if default is None:
            raise RemapError("n must be specified")
        value = default
    n = int(value)
    if n < 1:
        raise RemapError("n must be positive")
    return n


def _nonzero_float(value: float, name: str) -> float:
    result = float(value)
    if result == 0.0:
        raise RemapError(f"{name}= must be nonzero")
    return result


def _positive_float(value: float, name: str) -> float:
    result = float(value)
    if result <= 0.0:
        raise RemapError(f"{name}= must be positive")
    return result
