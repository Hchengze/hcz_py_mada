"""Bounded seismic gather organization and integer-binning utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from pymadagascar.core.hypercube import Hypercube
from pymadagascar.io.rsf import RSFArray, RSFHeader, read_rsf, write_rsf


class GatherError(ValueError):
    """Raised when a gather organization request is invalid."""


def cmp2shot(data: Any, *, dh: float, dy: float, oh: float, oy: float, positive: bool = True) -> np.ndarray:
    """Convert regular 2-D CMP gathers to shot gathers.

    The input follows the bounded ``sfcmp2shot`` layout with NumPy shape
    ``(n_cmp, n_offset, n_time)``. The output shape is
    ``(n_shot, type * n_offset, n_time)``.
    """

    array = np.asarray(data)
    if array.ndim != 3:
        raise GatherError("cmp2shot requires input shape (n_cmp, n_offset, n_time)")
    if not np.issubdtype(array.dtype, np.number):
        raise GatherError("cmp2shot input must be numeric")
    n_cmp, n_offset, n_time = array.shape
    if n_cmp < 1 or n_offset < 1 or n_time < 1:
        raise GatherError("cmp2shot input axes must be non-empty")
    offset_sampling = _nonzero_float(dh, "dh")
    cmp_sampling = _nonzero_float(dy, "dy")
    _finite_float(oh, "oh")
    _finite_float(oy, "oy")
    ratio = offset_sampling / cmp_sampling
    trace_type = int(np.floor(ratio + 0.5))
    if trace_type < 1 or not np.isclose(ratio, trace_type):
        raise GatherError("dh/dy must be a positive integer for the bounded cmp2shot subset")

    n_shot = (n_cmp - 1) // trace_type + n_offset
    output = np.zeros((n_shot, trace_type * n_offset, n_time), dtype=array.dtype)
    for ishot in range(n_shot):
        for ioffset in range(n_offset):
            for itype in range(trace_type):
                if positive:
                    icmp = itype + trace_type * (ishot + ioffset - n_offset + 1)
                else:
                    icmp = trace_type * (ishot - ioffset) - itype
                if 0 <= icmp < n_cmp:
                    output[ishot, ioffset * trace_type + itype] = array[icmp, ioffset]
    return np.ascontiguousarray(output)


def cmp2shot_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    positive: bool = True,
) -> RSFArray:
    """Apply the bounded ``sfcmp2shot`` subset to RSF files."""

    rsf = read_rsf(input_path)
    cube = Hypercube.from_header(rsf.header)
    if cube.ndim != 3:
        raise GatherError("cmp2shot_rsf requires an RSF with n1=time, n2=offset, n3=cmp")
    offset_axis = cube.axis(2)
    cmp_axis = cube.axis(3)
    result = cmp2shot(
        rsf.data,
        dh=offset_axis.d,
        dy=cmp_axis.d,
        oh=offset_axis.o,
        oy=cmp_axis.o,
        positive=positive,
    )
    trace_type = result.shape[1] // int(offset_axis.n)
    shot_sampling = offset_axis.d
    shot_origin = cmp_axis.o - offset_axis.o - (offset_axis.n - 1) * offset_axis.d if positive else cmp_axis.o + offset_axis.o

    header = rsf.header.copy()
    header["n2"] = int(trace_type * offset_axis.n)
    header["d2"] = float(offset_axis.d / trace_type)
    header["n3"] = int(result.shape[0])
    header["o3"] = float(shot_origin)
    header["d3"] = float(shot_sampling)
    header["label3"] = "Shot"
    header["cmp2shot_positive"] = "y" if positive else "n"
    header["cmp2shot_source"] = "../src-master/system/seismic/Mcmp2shot.c"
    header["cmp2shot_subset"] = "regular-2d-geometry-reorder"
    return write_rsf(output_path, result, header)


def intbin(
    data: Any,
    headers: Any,
    *,
    xkey: int = 0,
    ykey: int = 1,
    xmin: int | None = None,
    xmax: int | None = None,
    ymin: int | None = None,
    ymax: int | None = None,
) -> np.ndarray:
    """Sort traces into a 2-D integer-key bin grid."""

    array = np.asarray(data)
    if array.ndim != 2:
        raise GatherError("intbin requires input shape (n_trace, n_time)")
    table = _integer_header_table(headers, expected_rows=array.shape[0])
    xvals, yvals = _xy_keys(table, xkey=xkey, ykey=ykey)
    xlo, xhi = _bounds(xvals, xmin, xmax, "x")
    ylo, yhi = _bounds(yvals, ymin, ymax, "y")
    nx = xhi - xlo + 1
    ny = yhi - ylo + 1
    output = np.zeros((ny, nx, array.shape[1]), dtype=array.dtype)
    for itrace, (xval, yval) in enumerate(zip(xvals, yvals, strict=True)):
        if xlo <= xval <= xhi and ylo <= yval <= yhi:
            output[yval - ylo, xval - xlo] = array[itrace]
    return np.ascontiguousarray(output)


def intbin3(
    data: Any,
    headers: Any,
    *,
    xkey: int = 0,
    ykey: int = 1,
    zkey: int = 2,
    xmin: int | None = None,
    xmax: int | None = None,
    ymin: int | None = None,
    ymax: int | None = None,
    zmin: int | None = None,
    zmax: int | None = None,
) -> np.ndarray:
    """Sort traces into a 3-D integer-key bin grid."""

    array = np.asarray(data)
    if array.ndim != 2:
        raise GatherError("intbin3 requires input shape (n_trace, n_time)")
    table = _integer_header_table(headers, expected_rows=array.shape[0])
    xvals, yvals = _xy_keys(table, xkey=xkey, ykey=ykey)
    zidx = _key_index(zkey, table.shape[1], "zkey")
    zvals = table[:, zidx]
    xlo, xhi = _bounds(xvals, xmin, xmax, "x")
    ylo, yhi = _bounds(yvals, ymin, ymax, "y")
    zlo, zhi = _bounds(zvals, zmin, zmax, "z")
    nx = xhi - xlo + 1
    ny = yhi - ylo + 1
    nz = zhi - zlo + 1
    output = np.zeros((nz, ny, nx, array.shape[1]), dtype=array.dtype)
    for itrace, (xval, yval, zval) in enumerate(zip(xvals, yvals, zvals, strict=True)):
        if xlo <= xval <= xhi and ylo <= yval <= yhi and zlo <= zval <= zhi:
            output[zval - zlo, yval - ylo, xval - xlo] = array[itrace]
    return np.ascontiguousarray(output)


def intbin_rsf(
    input_path: str | Path,
    header_path: str | Path,
    output_path: str | Path,
    *,
    xkey: int = 0,
    ykey: int = 1,
    xmin: int | None = None,
    xmax: int | None = None,
    ymin: int | None = None,
    ymax: int | None = None,
) -> RSFArray:
    """Apply the bounded numeric-header ``sfintbin`` subset to RSF files."""

    rsf = read_rsf(input_path)
    head = read_rsf(header_path)
    result = intbin(rsf.data, head.data, xkey=xkey, ykey=ykey, xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax)
    xvals, yvals = _xy_keys(_integer_header_table(head.data, expected_rows=rsf.data.shape[0]), xkey=xkey, ykey=ykey)
    xlo, xhi = _bounds(xvals, xmin, xmax, "x")
    ylo, yhi = _bounds(yvals, ymin, ymax, "y")
    header = _trace_grid_header(
        rsf.header,
        n2=xhi - xlo + 1,
        n3=yhi - ylo + 1,
        o2=xlo,
        o3=ylo,
        source="../src-master/system/seismic/Mintbin.c",
        subset="integer-header-2d-trace-sorting",
    )
    header["intbin_xkey"] = int(xkey)
    header["intbin_ykey"] = int(ykey)
    return write_rsf(output_path, result, header)


def intbin3_rsf(
    input_path: str | Path,
    header_path: str | Path,
    output_path: str | Path,
    *,
    xkey: int = 0,
    ykey: int = 1,
    zkey: int = 2,
    xmin: int | None = None,
    xmax: int | None = None,
    ymin: int | None = None,
    ymax: int | None = None,
    zmin: int | None = None,
    zmax: int | None = None,
) -> RSFArray:
    """Apply the bounded numeric-header ``sfintbin3`` subset to RSF files."""

    rsf = read_rsf(input_path)
    head = read_rsf(header_path)
    result = intbin3(
        rsf.data,
        head.data,
        xkey=xkey,
        ykey=ykey,
        zkey=zkey,
        xmin=xmin,
        xmax=xmax,
        ymin=ymin,
        ymax=ymax,
        zmin=zmin,
        zmax=zmax,
    )
    table = _integer_header_table(head.data, expected_rows=rsf.data.shape[0])
    xvals, yvals = _xy_keys(table, xkey=xkey, ykey=ykey)
    zvals = table[:, _key_index(zkey, table.shape[1], "zkey")]
    xlo, xhi = _bounds(xvals, xmin, xmax, "x")
    ylo, yhi = _bounds(yvals, ymin, ymax, "y")
    zlo, zhi = _bounds(zvals, zmin, zmax, "z")
    header = _trace_grid_header(
        rsf.header,
        n2=xhi - xlo + 1,
        n3=yhi - ylo + 1,
        o2=xlo,
        o3=ylo,
        source="../src-master/system/seismic/Mintbin3.c",
        subset="integer-header-3d-trace-sorting",
    )
    header["n4"] = zhi - zlo + 1
    header["o4"] = zlo
    header["d4"] = 1
    header["intbin3_xkey"] = int(xkey)
    header["intbin3_ykey"] = int(ykey)
    header["intbin3_zkey"] = int(zkey)
    return write_rsf(output_path, result, header)


def _integer_header_table(headers: Any, *, expected_rows: int) -> np.ndarray:
    table = np.asarray(headers)
    if table.ndim != 2:
        raise GatherError("header table must be 2D")
    if table.shape[0] != expected_rows:
        raise GatherError("header table row count must match number of traces")
    if table.shape[1] < 1:
        raise GatherError("header table must contain at least one key column")
    if np.iscomplexobj(table) or not np.issubdtype(table.dtype, np.number):
        raise GatherError("header table must be real numeric data")
    rounded = np.rint(table).astype(np.int64)
    if not np.allclose(table, rounded):
        raise GatherError("header table values must be integer-valued")
    return rounded


def _xy_keys(table: np.ndarray, *, xkey: int, ykey: int) -> tuple[np.ndarray, np.ndarray]:
    yidx = _key_index(ykey, table.shape[1], "ykey")
    if int(xkey) < 0:
        xvals = np.zeros(table.shape[0], dtype=np.int64)
        current = -1
        previous_y: int | None = None
        for irow, yval in enumerate(table[:, yidx]):
            if previous_y is None or yval != previous_y:
                current = 0
            else:
                current += 1
            xvals[irow] = current
            previous_y = int(yval)
    else:
        xvals = table[:, _key_index(xkey, table.shape[1], "xkey")]
    return xvals, table[:, yidx]


def _key_index(value: int, width: int, name: str) -> int:
    index = int(value)
    if index < 0 or index >= width:
        raise GatherError(f"{name}= must be in [0,{width - 1}]")
    return index


def _bounds(values: np.ndarray, lower: int | None, upper: int | None, name: str) -> tuple[int, int]:
    if values.size == 0:
        raise GatherError(f"{name} values are empty")
    lo = int(np.min(values)) if lower is None else int(lower)
    hi = int(np.max(values)) if upper is None else int(upper)
    if hi < lo:
        raise GatherError(f"{name}max must be greater than or equal to {name}min")
    return lo, hi


def _trace_grid_header(
    input_header: RSFHeader,
    *,
    n2: int,
    n3: int,
    o2: int,
    o3: int,
    source: str,
    subset: str,
) -> RSFHeader:
    header = RSFHeader(
        {
            "n1": int(input_header.get_int("n1") or 1),
            "o1": float(input_header.get_float("o1", 0.0) or 0.0),
            "d1": float(input_header.get_float("d1", 1.0) or 1.0),
            "n2": int(n2),
            "o2": int(o2),
            "d2": 1,
            "n3": int(n3),
            "o3": int(o3),
            "d3": 1,
            "intbin_source": source,
            "intbin_subset": subset,
        }
    )
    for key in ("label1", "unit1"):
        if key in input_header:
            header[key] = input_header[key]
    header["label2"] = "xkey"
    header["label3"] = "ykey"
    return header


def _finite_float(value: float, name: str) -> float:
    result = float(value)
    if not np.isfinite(result):
        raise GatherError(f"{name}= must be finite")
    return result


def _nonzero_float(value: float, name: str) -> float:
    result = _finite_float(value, name)
    if result == 0.0:
        raise GatherError(f"{name}= must be nonzero")
    return result


__all__ = [
    "GatherError",
    "cmp2shot",
    "cmp2shot_rsf",
    "intbin",
    "intbin3",
    "intbin3_rsf",
    "intbin_rsf",
]
