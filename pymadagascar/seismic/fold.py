"""Bounded source-aligned foldplot histogram utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from pymadagascar.io.rsf import RSFArray, RSFHeader, read_rsf, write_rsf


class FoldError(ValueError):
    """Raised when a foldplot request is invalid."""


def fold_table(
    data: Any,
    *,
    columns: tuple[int, int, int] = (0, 1, 2),
    n: tuple[int, int, int],
    o: tuple[float, float, float],
    d: tuple[float, float, float],
) -> np.ndarray:
    """Build the bounded ``sffold`` three-axis histogram subset."""

    table = _real_array(data, name="data")
    if table.ndim != 2:
        raise FoldError("fold requires a 2D trace-header table")
    if table.shape[0] == 0:
        raise FoldError("fold requires at least one header row")
    cols = tuple(int(value) for value in columns)
    if len(cols) != 3:
        raise FoldError("columns must contain exactly three zero-based column indices")
    if min(cols) < 0 or max(cols) >= table.shape[1]:
        raise FoldError(f"columns must be within input table width {table.shape[1]}")
    sizes = _triple_positive_int(n, "n")
    origins = _triple_float(o, "o")
    deltas = _triple_nonzero_float(d, "d")

    out = np.zeros((sizes[2], sizes[1], sizes[0]), dtype=np.float32)
    coords = table[:, cols].astype(np.float64, copy=False)
    bins = np.rint((coords - np.asarray(origins, dtype=np.float64)) / np.asarray(deltas, dtype=np.float64)).astype(int)
    valid = (
        (bins[:, 0] >= 0)
        & (bins[:, 0] < sizes[0])
        & (bins[:, 1] >= 0)
        & (bins[:, 1] < sizes[1])
        & (bins[:, 2] >= 0)
        & (bins[:, 2] < sizes[2])
    )
    for i1, i2, i3 in bins[valid]:
        out[i3, i2, i1] += 1.0
    return np.ascontiguousarray(out)


def fold_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    columns: tuple[int, int, int] = (0, 1, 2),
    n: tuple[int, int, int],
    o: tuple[float, float, float],
    d: tuple[float, float, float],
    labels: tuple[str, str, str] = ("offset", "cdp", "iline"),
) -> RSFArray:
    """Apply the bounded numeric-header ``sffold`` subset to RSF files."""

    rsf = read_rsf(input_path)
    result = fold_table(rsf.data, columns=columns, n=n, o=o, d=d)
    header = RSFHeader(
        {
            "n1": int(n[0]),
            "o1": float(o[0]),
            "d1": float(d[0]),
            "label1": labels[0],
            "n2": int(n[1]),
            "o2": float(o[1]),
            "d2": float(d[1]),
            "label2": labels[1],
            "n3": int(n[2]),
            "o3": float(o[2]),
            "d3": float(d[2]),
            "label3": labels[2],
            "fold_columns": ",".join(str(int(value)) for value in columns),
            "fold_subset": "numeric-header-table",
        }
    )
    return write_rsf(output_path, result, header)


def _real_array(data: Any, *, name: str) -> np.ndarray:
    array = np.asarray(data)
    if np.iscomplexobj(array):
        raise FoldError(f"{name} must be real-valued")
    if not np.issubdtype(array.dtype, np.number):
        raise FoldError(f"{name} must be numeric")
    return np.asarray(array, dtype=np.float64)


def _triple_positive_int(values: tuple[int, int, int], name: str) -> tuple[int, int, int]:
    result = tuple(int(value) for value in values)
    if len(result) != 3 or any(value < 1 for value in result):
        raise FoldError(f"{name}= must contain three positive values")
    return result


def _triple_float(values: tuple[float, float, float], name: str) -> tuple[float, float, float]:
    result = tuple(float(value) for value in values)
    if len(result) != 3:
        raise FoldError(f"{name}= must contain three values")
    return result


def _triple_nonzero_float(values: tuple[float, float, float], name: str) -> tuple[float, float, float]:
    result = _triple_float(values, name)
    if any(value == 0.0 for value in result):
        raise FoldError(f"{name}= values must be nonzero")
    return result


__all__ = ["FoldError", "fold_rsf", "fold_table"]
