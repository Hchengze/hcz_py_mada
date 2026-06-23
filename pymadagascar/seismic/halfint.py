"""Half-order trace integration and differentiation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from pymadagascar.io.rsf import RSFArray, read_rsf, write_rsf
from pymadagascar.seismic._utils import numpy_axis, real_output_dtype, validate_rsf_axis


class HalfIntError(ValueError):
    """Raised when half-order trace-transform parameters are invalid."""


def halfint(data: Any, *, axis: int = 1, inv: bool = False, adj: bool = False, rho: float | None = None) -> np.ndarray:
    """Apply a bounded half-order integration or differentiation along one RSF axis."""

    array = np.asarray(data)
    if array.ndim < 1:
        raise HalfIntError("halfint requires at least one dimension")
    if np.iscomplexobj(array):
        raise HalfIntError("halfint requires real-valued input")
    if not np.issubdtype(array.dtype, np.number):
        raise HalfIntError("halfint requires numeric input")
    axis = validate_rsf_axis(axis, array.ndim)
    np_axis = numpy_axis(axis, array.ndim)
    n = array.shape[np_axis]
    if n < 2:
        raise HalfIntError("halfint requires at least two samples along the transform axis")
    rho_value = 1.0 - 1.0 / n if rho is None else float(rho)
    if not np.isfinite(rho_value) or rho_value <= 0.0:
        raise HalfIntError("rho= must be a positive finite value")

    dtype = real_output_dtype(array)
    moved = np.moveaxis(np.asarray(array, dtype=np.float64), np_axis, -1)
    spectrum = np.fft.rfft(moved, axis=-1)
    freqs = np.fft.rfftfreq(n, d=1.0)
    omega = 2.0 * np.pi * freqs
    floor = max(1.0 - min(rho_value, 0.999999999), np.finfo(np.float64).eps)
    safe_omega = np.maximum(omega, floor)
    power = 0.5 if inv else -0.5
    weights = safe_omega**power
    weights[0] = 0.0
    phase_sign = 1.0 if adj else -1.0
    phase = np.exp(phase_sign * 0.25j * np.pi) if not inv else np.exp(-phase_sign * 0.25j * np.pi)
    transformed = np.fft.irfft(spectrum * weights * phase, n=n, axis=-1)
    result = np.moveaxis(transformed, -1, np_axis)
    return np.ascontiguousarray(result.astype(dtype, copy=False))


def halfint_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    axis: int = 1,
    inv: bool = False,
    adj: bool = False,
    rho: float | None = None,
) -> RSFArray:
    """Apply the bounded ``sfhalfint`` subset to RSF files."""

    rsf = read_rsf(input_path)
    result = halfint(rsf.data, axis=axis, inv=inv, adj=adj, rho=rho)
    header = rsf.header.copy()
    header["halfint_axis"] = axis
    header["halfint_inv"] = "y" if inv else "n"
    header["halfint_adj"] = "y" if adj else "n"
    header["halfint_rho"] = 1.0 - 1.0 / result.shape[numpy_axis(axis, result.ndim)] if rho is None else float(rho)
    header["halfint_source"] = "../src-master/system/seismic/Mhalfint.c"
    header["halfint_subset"] = "fft-fractional-trace-transform"
    return write_rsf(output_path, result, header)


__all__ = ["HalfIntError", "halfint", "halfint_rsf"]
