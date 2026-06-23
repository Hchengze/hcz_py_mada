"""Angle-domain stack-panel transforms."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import numpy as np

from pymadagascar.core.hypercube import Hypercube
from pymadagascar.io.rsf import RSFArray, RSFHeader, read_rsf, write_rsf
from pymadagascar.seismic._utils import numpy_axis, real_output_dtype, validate_rsf_axis


class AngleTransformError(ValueError):
    """Raised when an angle transform request is invalid."""


AngleMode = Literal["cos", "sin"]


def cos2ang(
    data: Any,
    *,
    t0: float,
    dt: float,
    transform_axis: int = 2,
    na: int | None = None,
    a0: float = 0.0,
    da: float | None = None,
    fill_value: float = 0.0,
) -> np.ndarray:
    """Resample an inverse-cosine stack panel to an angle axis."""

    return _angle_transform(
        data,
        mode="cos",
        t0=t0,
        dt=dt,
        transform_axis=transform_axis,
        na=na,
        a0=a0,
        da=da,
        fill_value=fill_value,
    )


def isin2ang(
    data: Any,
    *,
    t0: float,
    dt: float,
    transform_axis: int = 2,
    na: int | None = None,
    a0: float = 0.0,
    da: float | None = None,
    fill_value: float = 0.0,
) -> np.ndarray:
    """Resample an inverse-sine stack panel to an angle axis."""

    return _angle_transform(
        data,
        mode="sin",
        t0=t0,
        dt=dt,
        transform_axis=transform_axis,
        na=na,
        a0=a0,
        da=da,
        fill_value=fill_value,
    )


def cos2ang_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    transform_axis: int = 2,
    na: int | None = None,
    a0: float = 0.0,
    da: float | None = None,
    fill_value: float = 0.0,
) -> RSFArray:
    """Apply the bounded ``sfcos2ang`` subset to RSF files."""

    return _angle_transform_rsf(
        input_path,
        output_path,
        mode="cos",
        source="../src-master/system/seismic/Mcos2ang.c",
        transform_axis=transform_axis,
        na=na,
        a0=a0,
        da=da,
        fill_value=fill_value,
    )


def isin2ang_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    transform_axis: int = 2,
    na: int | None = None,
    a0: float = 0.0,
    da: float | None = None,
    fill_value: float = 0.0,
) -> RSFArray:
    """Apply the bounded ``sfisin2ang`` subset to RSF files."""

    return _angle_transform_rsf(
        input_path,
        output_path,
        mode="sin",
        source="../src-master/system/seismic/Misin2ang.c",
        transform_axis=transform_axis,
        na=na,
        a0=a0,
        da=da,
        fill_value=fill_value,
    )


def _angle_transform(
    data: Any,
    *,
    mode: AngleMode,
    t0: float,
    dt: float,
    transform_axis: int,
    na: int | None,
    a0: float,
    da: float | None,
    fill_value: float,
) -> np.ndarray:
    array = np.asarray(data)
    if array.ndim < 2:
        raise AngleTransformError("angle transform requires at least two dimensions")
    if np.iscomplexobj(array) or not np.issubdtype(array.dtype, np.number):
        raise AngleTransformError("angle transform input must be real numeric data")
    axis = validate_rsf_axis(transform_axis, array.ndim)
    np_axis = numpy_axis(axis, array.ndim)
    nt = array.shape[np_axis]
    if nt < 2:
        raise AngleTransformError("transform axis must contain at least two samples")
    origin = _finite_float(t0, "t0")
    sampling = _positive_float(dt, "dt")
    angle_count = nt if na is None else int(na)
    if angle_count <= 0:
        raise AngleTransformError("na= must be positive")
    angle_origin = _finite_float(a0, "a0")
    angle_sampling = 90.0 / (nt - 1) if da is None else _finite_float(da, "da")
    if angle_sampling == 0.0:
        raise AngleTransformError("da= must be nonzero")
    fill = _finite_float(fill_value, "fill_value")

    angles = angle_origin + np.arange(angle_count, dtype=np.float64) * angle_sampling
    coords = _angle_coordinates(angles, mode=mode)
    sample_coords = (coords - origin) / sampling
    source_coords = np.arange(nt, dtype=np.float64)

    dtype = real_output_dtype(array)
    moved = np.moveaxis(np.asarray(array, dtype=np.float64), np_axis, -1)
    flat = moved.reshape((-1, nt))
    transformed = np.empty((flat.shape[0], angle_count), dtype=np.float64)
    for row, trace in enumerate(flat):
        transformed[row] = np.interp(sample_coords, source_coords, trace, left=fill, right=fill)
        transformed[row][~np.isfinite(sample_coords)] = fill
    restored = transformed.reshape(moved.shape[:-1] + (angle_count,))
    restored = np.moveaxis(restored, -1, np_axis)
    return np.ascontiguousarray(restored.astype(dtype, copy=False))


def _angle_transform_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    mode: AngleMode,
    source: str,
    transform_axis: int,
    na: int | None,
    a0: float,
    da: float | None,
    fill_value: float,
) -> RSFArray:
    rsf = read_rsf(input_path)
    cube = Hypercube.from_header(rsf.header)
    axis = validate_rsf_axis(transform_axis, cube.ndim)
    transform = cube.axis(axis)
    result = _angle_transform(
        rsf.data,
        mode=mode,
        t0=transform.o,
        dt=transform.d,
        transform_axis=axis,
        na=na,
        a0=a0,
        da=da,
        fill_value=fill_value,
    )
    angle_count = result.shape[numpy_axis(axis, result.ndim)]
    angle_sampling = 90.0 / (transform.n - 1) if da is None else float(da)
    header = rsf.header.copy()
    header[f"n{axis}"] = angle_count
    header[f"o{axis}"] = float(a0)
    header[f"d{axis}"] = angle_sampling
    header[f"label{axis}"] = "Angle"
    header[f"unit{axis}"] = "degree"
    key_prefix = "isin2ang" if mode == "sin" else "cos2ang"
    header[f"{key_prefix}_axis"] = axis
    header[f"{key_prefix}_source"] = source
    header[f"{key_prefix}_subset"] = "angle-axis-linear-resampling"
    header[f"{key_prefix}_top"] = "n"
    header[f"{key_prefix}_fill_value"] = float(fill_value)
    return write_rsf(output_path, result, header)


def _angle_coordinates(angles: np.ndarray, *, mode: AngleMode) -> np.ndarray:
    radians = np.deg2rad(angles)
    if mode == "cos":
        denom = np.cos(radians)
        return -1.0 / denom
    if mode == "sin":
        denom = np.sin(radians)
        return 1.0 / denom
    raise AngleTransformError(f"unknown angle mode: {mode}")


def _finite_float(value: float, name: str) -> float:
    result = float(value)
    if not np.isfinite(result):
        raise AngleTransformError(f"{name}= must be finite")
    return result


def _positive_float(value: float, name: str) -> float:
    result = _finite_float(value, name)
    if result <= 0.0:
        raise AngleTransformError(f"{name}= must be positive")
    return result


__all__ = [
    "AngleTransformError",
    "cos2ang",
    "cos2ang_rsf",
    "isin2ang",
    "isin2ang_rsf",
]
