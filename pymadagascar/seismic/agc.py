"""Automatic gain control for RSF seismic gathers."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from pymadagascar.core.hypercube import Hypercube
from pymadagascar.io.rsf import RSFArray, read_rsf, write_rsf

from ._utils import numpy_axis, real_output_dtype, validate_rsf_axis


class AGCError(ValueError):
    """Raised when AGC parameters are invalid."""


def agc_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    rect: float,
    axis: int = 1,
    eps: float = 1e-12,
) -> RSFArray:
    """Apply local RMS AGC along the selected RSF time axis.

    ``rect`` is a physical window length in the same units as ``d#`` and is
    converted to samples with ``round(rect / d#)``.
    """

    if rect <= 0.0:
        raise AGCError("rect= must be positive")
    if eps < 0.0:
        raise AGCError("eps= must be non-negative")

    rsf = read_rsf(input_path)
    if np.iscomplexobj(rsf.data):
        raise AGCError("agc_rsf requires real-valued seismic data")
    cube = Hypercube.from_header(rsf.header)
    axis = validate_rsf_axis(axis, cube.ndim)
    axis_obj = cube.axis(axis)
    if axis_obj.d <= 0.0:
        raise AGCError(f"d{axis}= must be positive for AGC window conversion")

    window = min(axis_obj.n, max(1, int(round(rect / axis_obj.d))))
    dtype = real_output_dtype(rsf.data)
    data = np.asarray(rsf.data, dtype=dtype)
    result = _agc_along_axis(data, numpy_axis(axis, cube.ndim), window, eps)
    return write_rsf(output_path, np.ascontiguousarray(result.astype(dtype, copy=False)), rsf.header.copy())


def _agc_along_axis(data: np.ndarray, axis: int, window: int, eps: float) -> np.ndarray:
    moved = np.moveaxis(data, axis, -1)
    trace_shape = moved.shape[:-1]
    traces = moved.reshape((-1, moved.shape[-1]))
    output = np.empty_like(traces, dtype=data.dtype)
    kernel = np.ones(window, dtype=np.float64)

    for index, trace in enumerate(traces):
        values = np.asarray(trace, dtype=np.float64)
        power = np.convolve(values * values, kernel, mode="same")
        fold = np.convolve(np.ones(values.size, dtype=np.float64), kernel, mode="same")
        rms = np.sqrt(power / np.maximum(fold, 1.0))
        output[index] = np.where(rms > eps, values / rms, 0.0).astype(data.dtype, copy=False)

    reshaped = output.reshape(trace_shape + (moved.shape[-1],))
    return np.ascontiguousarray(np.moveaxis(reshaped, -1, axis))
