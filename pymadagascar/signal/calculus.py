"""Small axis-calculus helpers for in-memory and RSF workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import numpy as np

from pymadagascar.core.hypercube import Hypercube
from pymadagascar.io.rsf import RSFArray, read_rsf, write_rsf


DerivativeMethod = Literal["central", "forward", "backward"]
IntegralMethod = Literal["cumsum", "trapezoid"]


class CalculusError(ValueError):
    """Raised when an axis-calculus request is invalid."""


def deriv(
    data: Any,
    *,
    axis: int = 1,
    method: DerivativeMethod = "central",
    scale_by_d: bool = True,
    d: float | None = None,
) -> np.ndarray:
    """Compute a first finite-difference derivative along one 1-based RSF axis.

    Central differences use one-sided first differences at both boundaries.
    Forward and backward modes repeat their nearest available first difference
    at the otherwise undefined boundary.
    """

    array = _coerce_numeric_array(data)
    rsf_axis = _validate_axis(axis, array.ndim)
    normalized = _normalize_derivative_method(method)
    spacing = _spacing(d, scale_by_d=scale_by_d)
    numpy_axis = array.ndim - rsf_axis
    moved = np.moveaxis(array, numpy_axis, -1)
    result = np.zeros_like(moved)

    if moved.shape[-1] > 1:
        differences = np.diff(moved, axis=-1)
        if normalized == "central":
            result[..., 0] = differences[..., 0]
            result[..., -1] = differences[..., -1]
            if moved.shape[-1] > 2:
                result[..., 1:-1] = 0.5 * (moved[..., 2:] - moved[..., :-2])
        elif normalized == "forward":
            result[..., :-1] = differences
            result[..., -1] = differences[..., -1]
        else:
            result[..., 0] = differences[..., 0]
            result[..., 1:] = differences

    if scale_by_d:
        result = result / spacing
    return np.ascontiguousarray(np.moveaxis(result, -1, numpy_axis))


def deriv_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    axis: int = 1,
    method: DerivativeMethod = "central",
    scale_by_d: bool = True,
) -> RSFArray:
    """Differentiate an RSF dataset while preserving shape and metadata."""

    rsf = read_rsf(input_path)
    cube = Hypercube.from_header(rsf.header)
    rsf_axis = _validate_axis(axis, cube.ndim)
    result = deriv(
        rsf.data,
        axis=rsf_axis,
        method=method,
        scale_by_d=scale_by_d,
        d=cube.axis(rsf_axis).d,
    )
    return write_rsf(output_path, result, rsf.header.copy())


def causal_integrate(
    data: Any,
    *,
    axis: int = 1,
    scale_by_d: bool = False,
    d: float | None = None,
) -> np.ndarray:
    """Apply forward causal cumulative integration along one RSF axis."""

    array = _coerce_numeric_array(data)
    rsf_axis = _validate_axis(axis, array.ndim)
    spacing = _spacing(d, scale_by_d=scale_by_d)
    numpy_axis = array.ndim - rsf_axis
    result = np.cumsum(array, axis=numpy_axis, dtype=_accumulator_dtype(array))
    if scale_by_d:
        result = result * spacing
    return np.ascontiguousarray(result.astype(array.dtype, copy=False))


def causint_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    axis: int = 1,
    scale_by_d: bool = False,
) -> RSFArray:
    """Causally integrate an RSF dataset while preserving its header."""

    rsf = read_rsf(input_path)
    cube = Hypercube.from_header(rsf.header)
    rsf_axis = _validate_axis(axis, cube.ndim)
    result = causal_integrate(
        rsf.data,
        axis=rsf_axis,
        scale_by_d=scale_by_d,
        d=cube.axis(rsf_axis).d,
    )
    return write_rsf(output_path, result, rsf.header.copy())


def integral(
    data: Any,
    *,
    axis: int = 1,
    method: IntegralMethod = "trapezoid",
    scale_by_d: bool = True,
    d: float | None = None,
) -> np.ndarray:
    """Compute a cumulative cumsum or trapezoid integral along one RSF axis."""

    array = _coerce_numeric_array(data)
    rsf_axis = _validate_axis(axis, array.ndim)
    normalized = _normalize_integral_method(method)
    spacing = _spacing(d, scale_by_d=scale_by_d)
    if normalized == "cumsum":
        return causal_integrate(
            array,
            axis=rsf_axis,
            scale_by_d=scale_by_d,
            d=spacing,
        )

    numpy_axis = array.ndim - rsf_axis
    moved = np.moveaxis(array, numpy_axis, -1)
    result = np.zeros_like(moved)
    if moved.shape[-1] > 1:
        increments = 0.5 * (moved[..., 1:] + moved[..., :-1])
        if scale_by_d:
            increments = increments * spacing
        result[..., 1:] = np.cumsum(
            increments,
            axis=-1,
            dtype=_accumulator_dtype(array),
        )
    return np.ascontiguousarray(np.moveaxis(result, -1, numpy_axis))


def integral_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    axis: int = 1,
    method: IntegralMethod = "trapezoid",
    scale_by_d: bool = True,
) -> RSFArray:
    """Integrate an RSF dataset while preserving shape and metadata."""

    rsf = read_rsf(input_path)
    cube = Hypercube.from_header(rsf.header)
    rsf_axis = _validate_axis(axis, cube.ndim)
    result = integral(
        rsf.data,
        axis=rsf_axis,
        method=method,
        scale_by_d=scale_by_d,
        d=cube.axis(rsf_axis).d,
    )
    return write_rsf(output_path, result, rsf.header.copy())


def _coerce_numeric_array(data: Any) -> np.ndarray:
    array = np.asarray(data)
    if array.ndim < 1 or array.ndim > 3:
        raise CalculusError("axis calculus currently supports 1D, 2D, and 3D data")
    if not np.issubdtype(array.dtype, np.number):
        raise CalculusError("axis calculus requires numeric data")
    if np.iscomplexobj(array):
        return np.asarray(array, dtype=np.complex64)
    if array.dtype == np.dtype("float64"):
        return np.asarray(array, dtype=np.float64)
    return np.asarray(array, dtype=np.float32)


def _validate_axis(axis: int, ndim: int) -> int:
    value = int(axis)
    if value < 1 or value > ndim:
        raise CalculusError(f"axis must be between 1 and {ndim}, got {axis}")
    return value


def _spacing(value: float | None, *, scale_by_d: bool) -> float:
    if not scale_by_d:
        return 1.0
    spacing = 1.0 if value is None else float(value)
    if spacing == 0.0:
        raise CalculusError("d/header d# must be nonzero when scale_by_d=y")
    return spacing


def _normalize_derivative_method(value: str) -> DerivativeMethod:
    normalized = str(value).strip().lower()
    if normalized not in {"central", "forward", "backward"}:
        raise CalculusError("method= must be central, forward, or backward")
    return normalized  # type: ignore[return-value]


def _normalize_integral_method(value: str) -> IntegralMethod:
    normalized = str(value).strip().lower()
    if normalized not in {"cumsum", "trapezoid"}:
        raise CalculusError("method= must be cumsum or trapezoid")
    return normalized  # type: ignore[return-value]


def _accumulator_dtype(array: np.ndarray) -> np.dtype[Any]:
    if np.iscomplexobj(array):
        return np.dtype("complex128")
    return np.dtype("float64")


__all__ = [
    "CalculusError",
    "causal_integrate",
    "causint_rsf",
    "deriv",
    "deriv_rsf",
    "integral",
    "integral_rsf",
]
