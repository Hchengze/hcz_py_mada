"""Small source-aligned array algebra utilities for RSF datasets."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from pymadagascar.io.rsf import RSFArray, RSFHeader, read_rsf, write_rsf


class ArrayAlgebraError(ValueError):
    """Raised when an array algebra request is invalid."""


def matmult(data: Any, matrix: Any, *, adj: bool = False) -> np.ndarray:
    """Apply the bounded real ``sfmatmult`` matrix-vector subset."""

    vector = _real_array(data, name="input").reshape(-1)
    mat = _real_array(matrix, name="mat")
    if mat.ndim != 2:
        raise ArrayAlgebraError("matmult requires a 2D matrix")
    if adj:
        if mat.shape[0] != vector.size:
            raise ArrayAlgebraError(
                f"adjoint matmult shape mismatch: matrix n2={mat.shape[0]} "
                f"but input n1={vector.size}"
            )
        result = mat.T @ vector
    else:
        if mat.shape[1] != vector.size:
            raise ArrayAlgebraError(
                f"matmult shape mismatch: matrix n1={mat.shape[1]} "
                f"but input n1={vector.size}"
            )
        result = mat @ vector
    return np.ascontiguousarray(_float_dtype(result, vector.dtype))


def matmult_rsf(
    input_path: str | Path,
    mat_path: str | Path,
    output_path: str | Path,
    *,
    adj: bool = False,
) -> RSFArray:
    """Apply the bounded real ``sfmatmult`` subset to RSF files."""

    inp = read_rsf(input_path)
    mat = read_rsf(mat_path)
    if inp.data.ndim != 1:
        raise ArrayAlgebraError("matmult_rsf currently expects a 1D input vector")
    if mat.data.ndim != 2:
        raise ArrayAlgebraError("matmult_rsf currently expects a 2D matrix")
    result = matmult(inp.data, mat.data, adj=adj)
    output_axis = 1 if adj else 2
    header = _vector_header_from_matrix(mat.header, output_axis, result.size)
    header["matmult_adj"] = "y" if adj else "n"
    return write_rsf(output_path, result, header)


def match(data: Any, other: Any, *, adj: bool = False, nf: int | None = None) -> np.ndarray:
    """Apply the bounded real ``sfmatch`` symmetric matching-filter subset."""

    left = _real_array(data, name="input")
    noise = _real_array(other, name="other")
    if adj:
        if nf is None:
            raise ArrayAlgebraError("adjoint match requires nf=")
        nf = _positive_int(nf, "nf")
        if left.shape != noise.shape:
            raise ArrayAlgebraError(f"adjoint match shape mismatch: {left.shape} != {noise.shape}")
        rows = _as_trace_rows(left)
        noise_rows = _as_trace_rows(noise)
        filt = np.zeros(nf, dtype=np.float64)
        half = nf // 2
        for data_row, noise_row in zip(rows, noise_rows):
            n1 = data_row.size
            for i in range(nf):
                for i1 in range(n1):
                    j = i1 - i + half
                    if 0 <= j < n1:
                        filt[i] += float(noise_row[j]) * float(data_row[i1])
        return np.ascontiguousarray(_float_dtype(filt, left.dtype))

    filt = left.reshape(-1)
    if filt.ndim != 1 or filt.size == 0:
        raise ArrayAlgebraError("forward match requires a non-empty 1D filter")
    rows = _as_trace_rows(noise)
    out = np.zeros_like(rows, dtype=np.float64)
    nf = filt.size
    half = nf // 2
    for row_index, noise_row in enumerate(rows):
        n1 = noise_row.size
        for i in range(nf):
            for i1 in range(n1):
                j = i1 - i + half
                if 0 <= j < n1:
                    out[row_index, i1] += float(noise_row[j]) * float(filt[i])
    return np.ascontiguousarray(_float_dtype(out.reshape(noise.shape), noise.dtype))


def match_rsf(
    input_path: str | Path,
    other_path: str | Path,
    output_path: str | Path,
    *,
    adj: bool = False,
    nf: int | None = None,
) -> RSFArray:
    """Apply the bounded real ``sfmatch`` subset to RSF files."""

    inp = read_rsf(input_path)
    other = read_rsf(other_path)
    result = match(inp.data, other.data, adj=adj, nf=nf)
    if adj:
        header = RSFHeader(
            {
                "n1": result.size,
                "o1": 0.0,
                "d1": 1.0,
                "label1": "Filter sample",
                "match_adj": "y",
            }
        )
    else:
        header = other.header.copy()
        header["match_adj"] = "n"
        header["match_nf"] = inp.data.size
    return write_rsf(output_path, result, header)


def linefit(data: Any, *, n: int, o: float, d: float) -> np.ndarray:
    """Fit ``y = a*x + b`` and evaluate it on a regular output grid."""

    table = _real_array(data, name="input")
    if table.ndim != 2 or table.shape[1] != 2:
        raise ArrayAlgebraError("linefit requires a 2D table with last axis length 2")
    if table.shape[0] < 2:
        raise ArrayAlgebraError("linefit requires at least two points")
    n = _positive_int(n, "n")
    d = _nonzero_float(d, "d")
    x = table[:, 0].astype(np.float64)
    y = table[:, 1].astype(np.float64)
    sx = float(np.sum(x))
    sx2 = float(np.sum(x * x))
    sxy = float(np.sum(x * y))
    sy = float(np.sum(y))
    det = table.shape[0] * sx2 - sx * sx
    if det == 0.0:
        raise ArrayAlgebraError("linefit has zero determinant")
    slope = (table.shape[0] * sxy - sx * sy) / det
    intercept = (sy * sx2 - sx * sxy) / det
    grid = float(o) + np.arange(n, dtype=np.float64) * d
    result = slope * grid + intercept
    return np.ascontiguousarray(_float_dtype(result, table.dtype))


def linefit_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    n: int,
    o: float,
    d: float,
) -> RSFArray:
    """Apply the bounded ``sflinefit`` table-fit subset to an RSF file."""

    inp = read_rsf(input_path)
    if inp.header.dimensions[0] != 2:
        raise ArrayAlgebraError("linefit_rsf expects RSF n1=2 coordinate/value table input")
    result = linefit(inp.data, n=n, o=o, d=d)
    header = RSFHeader(
        {
            "n1": result.size,
            "o1": float(o),
            "d1": float(d),
            "label1": "Linefit",
            "linefit_model": "y=a*x+b",
        }
    )
    return write_rsf(output_path, result, header)


def _vector_header_from_matrix(header: RSFHeader, axis: int, n: int) -> RSFHeader:
    result = RSFHeader(
        {
            "n1": n,
            "o1": header.get(f"o{axis}", 0.0),
            "d1": header.get(f"d{axis}", 1.0),
            "label1": header.get(f"label{axis}", "Matrix output"),
        }
    )
    unit = header.get(f"unit{axis}")
    if unit is not None:
        result["unit1"] = unit
    return result


def _as_trace_rows(data: np.ndarray) -> np.ndarray:
    if data.ndim == 1:
        return data.reshape(1, data.size)
    return data.reshape(-1, data.shape[-1])


def _real_array(data: Any, *, name: str) -> np.ndarray:
    array = np.asarray(data)
    if array.ndim < 1:
        raise ArrayAlgebraError(f"{name} must have at least one dimension")
    if np.iscomplexobj(array):
        raise ArrayAlgebraError(f"{name} must be real-valued")
    if not np.issubdtype(array.dtype, np.number):
        raise ArrayAlgebraError(f"{name} must be numeric")
    dtype = np.float64 if array.dtype == np.dtype("float64") else np.float32
    return np.asarray(array, dtype=dtype)


def _float_dtype(data: np.ndarray, source_dtype: np.dtype[Any]) -> np.ndarray:
    if np.dtype(source_dtype) == np.dtype("float64"):
        return np.asarray(data, dtype=np.float64)
    return np.asarray(data, dtype=np.float32)


def _positive_int(value: int, name: str) -> int:
    result = int(value)
    if result < 1:
        raise ArrayAlgebraError(f"{name}= must be positive")
    return result


def _nonzero_float(value: float, name: str) -> float:
    result = float(value)
    if result == 0.0:
        raise ArrayAlgebraError(f"{name}= must be nonzero")
    return result


__all__ = [
    "ArrayAlgebraError",
    "linefit",
    "linefit_rsf",
    "match",
    "match_rsf",
    "matmult",
    "matmult_rsf",
]
