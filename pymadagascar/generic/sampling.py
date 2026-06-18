"""Small generic sampling, binning, slicing, and picking utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import numpy as np

from pymadagascar.core.axis import Axis
from pymadagascar.core.hypercube import Hypercube
from pymadagascar.io.rsf import RSFArray, RSFHeader, read_rsf, write_rsf


Statistic = Literal["mean", "sum", "count"]
MaxMode = Literal["value", "index", "coord"]
NanPolicy = Literal["propagate", "omit"]


class SamplingError(ValueError):
    """Raised when a generic sampling or picking request is invalid."""


def linear_resample(
    data: Any,
    *,
    axis: int = 1,
    n: int | None = None,
    o: float | None = None,
    d: float | None = None,
    input_o: float = 0.0,
    input_d: float = 1.0,
    fill: float = 0.0,
) -> np.ndarray:
    """Linearly resample a regular 1D axis using 1-based RSF axis numbering.

    Samples outside the input coordinate range are filled with ``fill``. This is
    a regular-grid pymadagascar subset and is not Madagascar ``sflinear``'s
    irregular coordinate/value-table mode.
    """

    array = _coerce_real_array(data)
    rsf_axis = _validate_axis(axis, array.ndim)
    numpy_axis = array.ndim - rsf_axis
    old_n = array.shape[numpy_axis]
    output_n = _normalize_n(n, old_n)
    output_o = float(input_o) if o is None else float(o)
    output_d = float(input_d) if d is None else _normalize_spacing(d, "d")
    input_d = _normalize_spacing(input_d, "input_d")

    input_coords = float(input_o) + np.arange(old_n, dtype=np.float64) * input_d
    output_coords = output_o + np.arange(output_n, dtype=np.float64) * output_d

    moved = np.moveaxis(array, numpy_axis, -1)
    flat = moved.reshape(-1, old_n)
    out = np.empty((flat.shape[0], output_n), dtype=np.float64)
    if input_coords[0] <= input_coords[-1]:
        xp = input_coords
        reverse = False
    else:
        xp = input_coords[::-1]
        reverse = True

    for irow, row in enumerate(flat):
        fp = row[::-1] if reverse else row
        out[irow] = np.interp(output_coords, xp, fp, left=float(fill), right=float(fill))

    result = out.reshape(moved.shape[:-1] + (output_n,))
    result = np.moveaxis(result, -1, numpy_axis)
    return np.ascontiguousarray(_float_output_dtype(result, array.dtype))


def linear_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    axis: int = 1,
    n: int | None = None,
    o: float | None = None,
    d: float | None = None,
    fill: float = 0.0,
) -> RSFArray:
    """Linearly resample one regular RSF axis and update n#/o#/d# metadata."""

    rsf = read_rsf(input_path)
    cube = Hypercube.from_header(rsf.header)
    rsf_axis = _validate_axis(axis, cube.ndim)
    axis_obj = cube.axis(rsf_axis)
    output_n = _normalize_n(n, axis_obj.n)
    output_o = axis_obj.o if o is None else float(o)
    output_d = axis_obj.d if d is None else _normalize_spacing(d, "d")
    result = linear_resample(
        rsf.data,
        axis=rsf_axis,
        n=output_n,
        o=output_o,
        d=output_d,
        input_o=axis_obj.o,
        input_d=axis_obj.d,
        fill=fill,
    )
    header = cube.update_axis(rsf_axis, n=output_n, o=output_o, d=output_d).to_header(
        rsf.header
    )
    return write_rsf(output_path, result, header)


def bin_1d(
    coords: Any,
    values: Any,
    *,
    o: float,
    d: float,
    n: int,
    statistic: Statistic = "mean",
    fill: float = 0.0,
) -> np.ndarray:
    """Bin coordinate/value samples onto a 1D regular grid."""

    coord_array = np.asarray(coords, dtype=np.float64).reshape(-1)
    value_array = _coerce_real_array(values).reshape(-1)
    if coord_array.shape != value_array.shape:
        raise SamplingError("coords and values must have the same length")
    n = _normalize_n(n, None)
    d = _normalize_positive_spacing(d, "d")
    stat = _normalize_statistic(statistic)

    bins = np.floor((coord_array - float(o)) / d).astype(np.int64)
    valid = (bins >= 0) & (bins < n)
    return _finish_binning((n,), (bins[valid],), value_array[valid], stat, fill, value_array.dtype)


def bin_2d(
    x: Any,
    y: Any,
    values: Any,
    *,
    o1: float,
    d1: float,
    n1: int,
    o2: float,
    d2: float,
    n2: int,
    statistic: Statistic = "mean",
    fill: float = 0.0,
) -> np.ndarray:
    """Bin x/y/value samples onto a 2D RSF grid with NumPy shape (n2, n1)."""

    x_array = np.asarray(x, dtype=np.float64).reshape(-1)
    y_array = np.asarray(y, dtype=np.float64).reshape(-1)
    value_array = _coerce_real_array(values).reshape(-1)
    if x_array.shape != y_array.shape or x_array.shape != value_array.shape:
        raise SamplingError("x, y, and values must have the same length")
    n1 = _normalize_n(n1, None)
    n2 = _normalize_n(n2, None)
    d1 = _normalize_positive_spacing(d1, "d1")
    d2 = _normalize_positive_spacing(d2, "d2")
    stat = _normalize_statistic(statistic)

    ix = np.floor((x_array - float(o1)) / d1).astype(np.int64)
    iy = np.floor((y_array - float(o2)) / d2).astype(np.int64)
    valid = (ix >= 0) & (ix < n1) & (iy >= 0) & (iy < n2)
    return _finish_binning(
        (n2, n1),
        (iy[valid], ix[valid]),
        value_array[valid],
        stat,
        fill,
        value_array.dtype,
    )


def bin_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    x: int = 0,
    y: int = 1,
    value: int = 2,
    n1: int,
    o1: float,
    d1: float,
    n2: int,
    o2: float,
    d2: float,
    statistic: Statistic = "mean",
    fill: float = 0.0,
) -> RSFArray:
    """Bin a table-like RSF point cloud into a 2D grid.

    The input subset expects a 2D table with one point per NumPy row and
    columns on the last axis, typically shape ``(npoints, ncolumns)``.
    Column indices are zero-based.
    """

    rsf = read_rsf(input_path)
    table = _coerce_real_array(rsf.data)
    if table.ndim != 2:
        raise SamplingError("bin_rsf expects a 2D table-like RSF input")
    max_column = max(int(x), int(y), int(value))
    if min(int(x), int(y), int(value)) < 0 or max_column >= table.shape[1]:
        raise SamplingError(
            f"column indices must be in 0..{table.shape[1] - 1} for input table"
        )
    grid = bin_2d(
        table[:, int(x)],
        table[:, int(y)],
        table[:, int(value)],
        n1=n1,
        o1=o1,
        d1=d1,
        n2=n2,
        o2=o2,
        d2=d2,
        statistic=statistic,
        fill=fill,
    )
    header = Hypercube(
        [
            Axis(n=int(n1), o=float(o1), d=float(d1), label="X", index=1),
            Axis(n=int(n2), o=float(o2), d=float(d2), label="Y", index=2),
        ]
    ).to_header(RSFHeader({"statistic": statistic}))
    return write_rsf(output_path, grid, header)


def slice_array(data: Any, *, axis: int = 3, index: int = 0) -> np.ndarray:
    """Extract a fixed zero-based index along a 1-based RSF axis."""

    array = np.asarray(data)
    if array.ndim < 2:
        raise SamplingError("slice_array requires at least 2D input")
    rsf_axis = _validate_axis(axis, array.ndim)
    numpy_axis = array.ndim - rsf_axis
    index = _normalize_index(index, array.shape[numpy_axis], axis=rsf_axis)
    return np.ascontiguousarray(np.take(array, index, axis=numpy_axis))


def slice_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    axis: int = 3,
    index: int = 0,
) -> RSFArray:
    """Extract a fixed-index slice from an RSF file and remove that axis."""

    rsf = read_rsf(input_path)
    cube = Hypercube.from_header(rsf.header)
    rsf_axis = _validate_axis(axis, cube.ndim)
    result = slice_array(rsf.data, axis=rsf_axis, index=index)
    axes = [axis_obj for i, axis_obj in enumerate(cube.axes, start=1) if i != rsf_axis]
    if not axes:
        raise SamplingError("slice_rsf requires at least 2D input")
    header = Hypercube(axes).to_header(rsf.header)
    return write_rsf(output_path, result, header)


def max1(
    data: Any,
    *,
    axis: int = 1,
    mode: MaxMode = "value",
    abs_search: bool = False,
    nan_policy: NanPolicy = "propagate",
    input_o: float = 0.0,
    input_d: float = 1.0,
) -> np.ndarray:
    """Pick a maximum along one 1-based RSF axis.

    ``mode='value'`` returns the original sample value at the maximum. With
    ``abs_search=True``, the search is by absolute amplitude but the returned
    value remains signed.
    """

    array = _coerce_real_array(data)
    rsf_axis = _validate_axis(axis, array.ndim)
    mode = _normalize_mode(mode)
    nan_policy = _normalize_nan_policy(nan_policy)
    input_d = _normalize_spacing(input_d, "input_d")
    numpy_axis = array.ndim - rsf_axis

    moved = np.moveaxis(array, numpy_axis, -1)
    metric = np.abs(moved) if abs_search else moved
    flat_values = moved.reshape(-1, moved.shape[-1])
    flat_metric = metric.reshape(-1, metric.shape[-1])
    output = np.empty(flat_values.shape[0], dtype=np.float64)

    for irow, (value_row, metric_row) in enumerate(zip(flat_values, flat_metric)):
        output[irow] = _pick_row(
            value_row,
            metric_row,
            mode=mode,
            nan_policy=nan_policy,
            input_o=float(input_o),
            input_d=input_d,
        )

    result = output.reshape(moved.shape[:-1])
    return np.ascontiguousarray(_float_output_dtype(result, array.dtype))


def max1_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    axis: int = 1,
    mode: MaxMode = "value",
    abs_search: bool = False,
    nan_policy: NanPolicy = "propagate",
) -> RSFArray:
    """Pick maxima from an RSF file and remove the searched axis."""

    rsf = read_rsf(input_path)
    cube = Hypercube.from_header(rsf.header)
    rsf_axis = _validate_axis(axis, cube.ndim)
    axis_obj = cube.axis(rsf_axis)
    result = max1(
        rsf.data,
        axis=rsf_axis,
        mode=mode,
        abs_search=abs_search,
        nan_policy=nan_policy,
        input_o=axis_obj.o,
        input_d=axis_obj.d,
    )
    axes = [axis_obj for i, axis_obj in enumerate(cube.axes, start=1) if i != rsf_axis]
    output_data = result
    if not axes:
        axes = [Axis(n=1, o=0.0, d=1.0, label=f"max1_{mode}", index=1)]
        output_data = np.asarray(result).reshape(1)
    header = Hypercube(axes).to_header(rsf.header)
    header["max1_mode"] = mode
    header["max1_axis"] = rsf_axis
    return write_rsf(output_path, output_data, header)


def _finish_binning(
    shape: tuple[int, ...],
    indices: tuple[np.ndarray, ...],
    values: np.ndarray,
    statistic: Statistic,
    fill: float,
    dtype: np.dtype[Any],
) -> np.ndarray:
    sums = np.zeros(shape, dtype=np.float64)
    counts = np.zeros(shape, dtype=np.float64)
    if values.size:
        np.add.at(sums, indices, values.astype(np.float64, copy=False))
        np.add.at(counts, indices, 1.0)

    output = np.full(shape, float(fill), dtype=np.float64)
    used = counts > 0
    if statistic == "mean":
        output[used] = sums[used] / counts[used]
    elif statistic == "sum":
        output[used] = sums[used]
    elif statistic == "count":
        output[used] = counts[used]
    else:  # pragma: no cover - guarded by _normalize_statistic.
        raise SamplingError(f"unsupported statistic {statistic!r}")
    return np.ascontiguousarray(_float_output_dtype(output, dtype))


def _pick_row(
    value_row: np.ndarray,
    metric_row: np.ndarray,
    *,
    mode: MaxMode,
    nan_policy: NanPolicy,
    input_o: float,
    input_d: float,
) -> float:
    row = np.asarray(metric_row, dtype=np.float64)
    if nan_policy == "propagate" and np.isnan(row).any():
        return float("nan")
    if nan_policy == "omit":
        valid = ~np.isnan(row)
        if not np.any(valid):
            return float("nan")
        search = np.where(valid, row, -np.inf)
    else:
        search = row

    index = int(np.argmax(search))
    if mode == "value":
        return float(value_row[index])
    if mode == "index":
        return float(index)
    if mode == "coord":
        return input_o + index * input_d
    raise SamplingError(f"unsupported mode {mode!r}")


def _coerce_real_array(data: Any) -> np.ndarray:
    array = np.asarray(data)
    if array.ndim < 1 or array.ndim > 4:
        raise SamplingError("generic sampling currently supports 1D, 2D, 3D, and 4D data")
    if np.iscomplexobj(array):
        raise SamplingError("generic sampling tools currently require real-valued input")
    if not np.issubdtype(array.dtype, np.number):
        raise SamplingError("generic sampling tools require numeric data")
    return np.asarray(array, dtype=np.float64 if array.dtype == np.dtype("float64") else np.float32)


def _float_output_dtype(data: np.ndarray, source_dtype: np.dtype[Any]) -> np.ndarray:
    if np.dtype(source_dtype) == np.dtype("float64"):
        return np.asarray(data, dtype=np.float64)
    return np.asarray(data, dtype=np.float32)


def _validate_axis(axis: int, ndim: int) -> int:
    value = int(axis)
    if value < 1 or value > ndim:
        raise SamplingError(f"axis must be between 1 and {ndim}, got {axis}")
    return value


def _normalize_n(value: int | None, default: int | None) -> int:
    if value is None:
        if default is None:
            raise SamplingError("n must be specified")
        value = default
    n = int(value)
    if n < 1:
        raise SamplingError("n must be positive")
    return n


def _normalize_spacing(value: float, name: str) -> float:
    spacing = float(value)
    if spacing == 0.0:
        raise SamplingError(f"{name}= must be nonzero")
    return spacing


def _normalize_positive_spacing(value: float, name: str) -> float:
    spacing = float(value)
    if spacing <= 0.0:
        raise SamplingError(f"{name}= must be positive")
    return spacing


def _normalize_index(index: int, size: int, *, axis: int) -> int:
    value = int(index)
    if value < 0 or value >= size:
        raise SamplingError(f"index={value} is outside axis {axis} range 0..{size - 1}")
    return value


def _normalize_statistic(value: str) -> Statistic:
    normalized = str(value).strip().lower()
    if normalized not in {"mean", "sum", "count"}:
        raise SamplingError("statistic= must be 'mean', 'sum', or 'count'")
    return normalized  # type: ignore[return-value]


def _normalize_mode(value: str) -> MaxMode:
    normalized = str(value).strip().lower()
    if normalized not in {"value", "index", "coord"}:
        raise SamplingError("mode= must be 'value', 'index', or 'coord'")
    return normalized  # type: ignore[return-value]


def _normalize_nan_policy(value: str) -> NanPolicy:
    normalized = str(value).strip().lower()
    if normalized not in {"propagate", "omit"}:
        raise SamplingError("nan_policy= must be 'propagate' or 'omit'")
    return normalized  # type: ignore[return-value]
