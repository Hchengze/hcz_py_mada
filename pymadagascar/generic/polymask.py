"""Source-aligned polygon masks for regular 2-D RSF grids."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from pymadagascar.core.hypercube import Hypercube
from pymadagascar.io.rsf import RSFArray, read_rsf, write_rsf


class PolyMaskError(ValueError):
    """Raised when a polygon-mask request is invalid."""


def polymask(
    shape: tuple[int, int],
    vertices: Any,
    *,
    o1: float = 0.0,
    d1: float = 1.0,
    o2: float = 0.0,
    d2: float = 1.0,
) -> np.ndarray:
    """Return the bounded ``sfpolymask`` point-in-polygon mask."""

    if len(shape) != 2:
        raise PolyMaskError("polymask requires a 2-D grid shape")
    n2, n1 = (int(shape[0]), int(shape[1]))
    if n1 < 1 or n2 < 1:
        raise PolyMaskError("polymask grid axes must be non-empty")
    if not np.isfinite([o1, d1, o2, d2]).all():
        raise PolyMaskError("polymask axis origin and sampling must be finite")
    points = _vertices(vertices)
    x = float(o1) + np.arange(n1, dtype=np.float64) * float(d1)
    y = float(o2) + np.arange(n2, dtype=np.float64) * float(d2)
    return _points_in_polygon(x, y, points).astype(np.int32, copy=False)


def polymask_rsf(input_path: str | Path, poly_path: str | Path, output_path: str | Path) -> RSFArray:
    """Apply the bounded ``sfpolymask`` subset to RSF files."""

    rsf = read_rsf(input_path)
    cube = Hypercube.from_header(rsf.header)
    if cube.ndim != 2:
        raise PolyMaskError("polymask_rsf requires a 2-D RSF input grid")
    if np.iscomplexobj(rsf.data):
        raise PolyMaskError("polymask_rsf only supports real-valued grid inputs")
    poly = read_rsf(poly_path)
    if not np.issubdtype(poly.data.dtype, np.floating):
        raise PolyMaskError("poly= must point to a floating-point RSF vertex table")
    axis1 = cube.axis(1)
    axis2 = cube.axis(2)
    result = polymask(
        rsf.data.shape,
        poly.data,
        o1=axis1.o,
        d1=axis1.d,
        o2=axis2.o,
        d2=axis2.d,
    )

    header = rsf.header.copy()
    header["polymask_source"] = "../src-master/system/generic/Mpolymask.c"
    header["polymask_subset"] = "regular-2d-point-in-polygon-mask"
    return write_rsf(output_path, result, header)


def _vertices(vertices: Any) -> np.ndarray:
    array = np.asarray(vertices)
    if not np.issubdtype(array.dtype, np.number):
        raise PolyMaskError("polygon vertices must be numeric")
    array = np.asarray(array, dtype=np.float64)
    if array.ndim != 2:
        raise PolyMaskError("polygon vertices must be a 2-D array")
    if array.shape[0] == 2:
        points = array.T
    elif array.shape[1] == 2:
        points = array
    else:
        raise PolyMaskError("polygon vertices must have shape (2, nv) or (nv, 2)")
    if points.shape[0] < 3:
        raise PolyMaskError("polygon must contain at least three vertices")
    if not np.isfinite(points).all():
        raise PolyMaskError("polygon vertices must be finite")
    return np.ascontiguousarray(points)


def _points_in_polygon(x: np.ndarray, y: np.ndarray, vertices: np.ndarray) -> np.ndarray:
    inside = np.zeros((y.size, x.size), dtype=bool)
    xj, yj = vertices[-1]
    for xi, yi in vertices:
        active_rows = ((yi > y) != (yj > y))
        edge_x = np.empty((y.size, 1), dtype=np.float64)
        edge_x.fill(np.inf)
        if np.any(active_rows):
            edge_x[active_rows, 0] = (xj - xi) * (y[active_rows] - yi) / (yj - yi) + xi
        crosses = active_rows[:, None] & (x[None, :] < edge_x)
        inside ^= crosses
        xj, yj = xi, yi
    return inside


__all__ = ["PolyMaskError", "polymask", "polymask_rsf"]
