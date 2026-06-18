"""Complex-valued RSF helper tools."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from pymadagascar.io.rsf import RSFArray, read_rsf, write_rsf


class ComplexToolError(ValueError):
    """Raised when a complex RSF helper cannot complete safely."""


def real_rsf(input_path: str | Path, output_path: str | Path) -> RSFArray:
    """Write the real part of a complex RSF file as a real RSF file."""

    rsf = read_rsf(input_path)
    _require_complex(rsf.data, "real_rsf")
    data = np.ascontiguousarray(np.real(rsf.data).astype(_real_dtype(rsf.data.dtype)))
    return write_rsf(output_path, data, rsf.header.copy())


def imag_rsf(input_path: str | Path, output_path: str | Path) -> RSFArray:
    """Write the imaginary part of a complex RSF file as a real RSF file."""

    rsf = read_rsf(input_path)
    _require_complex(rsf.data, "imag_rsf")
    data = np.ascontiguousarray(np.imag(rsf.data).astype(_real_dtype(rsf.data.dtype)))
    return write_rsf(output_path, data, rsf.header.copy())


def cmplx_rsf(
    real_path: str | Path,
    imag_path: str | Path,
    output_path: str | Path,
) -> RSFArray:
    """Combine real and imaginary RSF files into one complex RSF file."""

    real = read_rsf(real_path)
    imag = read_rsf(imag_path)
    _require_real_numeric(real.data, "cmplx_rsf real input")
    _require_real_numeric(imag.data, "cmplx_rsf imag input")
    if real.data.shape != imag.data.shape:
        raise ComplexToolError(
            "cmplx_rsf inputs must have the same shape: "
            f"{real.data.shape} != {imag.data.shape}"
        )

    data = (
        real.data.astype(np.float32, copy=False)
        + 1j * imag.data.astype(np.float32, copy=False)
    ).astype(np.complex64)
    return write_rsf(output_path, np.ascontiguousarray(data), real.header.copy())


def rtoc_rsf(input_path: str | Path, output_path: str | Path) -> RSFArray:
    """Convert a real RSF file to complex by adding a zero imaginary part."""

    rsf = read_rsf(input_path)
    _require_real_numeric(rsf.data, "rtoc_rsf")
    data = rsf.data.astype(np.float32, copy=False).astype(np.complex64)
    return write_rsf(output_path, np.ascontiguousarray(data), rsf.header.copy())


def _require_complex(data: np.ndarray, context: str) -> None:
    if not np.iscomplexobj(data):
        raise ComplexToolError(f"{context} requires a complex RSF input")


def _require_real_numeric(data: np.ndarray, context: str) -> None:
    dtype = np.dtype(data.dtype)
    if np.iscomplexobj(data) or dtype.kind not in {"f", "i", "u"}:
        raise ComplexToolError(f"{context} requires a real numeric RSF input")


def _real_dtype(dtype: np.dtype[Any]) -> np.dtype[Any]:
    normalized = np.dtype(dtype)
    if normalized == np.dtype("complex64"):
        return np.dtype("float32")
    if normalized == np.dtype("complex128"):
        return np.dtype("float64")
    raise ComplexToolError(f"unsupported complex dtype: {normalized}")
