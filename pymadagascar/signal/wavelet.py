"""Wavelet generators for synthetic RSF workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from pymadagascar.io.rsf import RSFArray, RSFHeader, format_from_dtype, write_rsf


class WaveletError(ValueError):
    """Raised when a wavelet request is invalid."""


def ricker_wavelet(
    frequency: float,
    dt: float,
    nt: int,
    *,
    t0: float | None = None,
    peak_time: float | None = None,
    amplitude: float = 1.0,
    dtype: str | np.dtype[Any] = "float32",
) -> np.ndarray:
    """Return a sampled zero-phase Ricker wavelet.

    ``frequency`` is the peak frequency in Hz, ``dt`` is the time sample
    interval in seconds, and ``nt`` is the number of output samples. ``t0`` and
    ``peak_time`` are aliases for the time at which the central peak occurs.
    When neither is provided, the peak is placed at ``1 / frequency``.
    """

    frequency_value = _positive_float(frequency, "frequency")
    dt_value = _positive_float(dt, "dt")
    nt_value = _positive_int(nt, "nt")
    amplitude_value = float(amplitude)
    peak = _resolve_peak_time(frequency_value, t0=t0, peak_time=peak_time)
    try:
        dtype_obj = np.dtype(dtype)
        format_from_dtype(dtype_obj)
    except (TypeError, ValueError) as exc:
        raise WaveletError(str(exc)) from exc

    time = np.arange(nt_value, dtype=np.float64) * dt_value
    arg = np.pi * frequency_value * (time - peak)
    arg2 = arg * arg
    wavelet = amplitude_value * (1.0 - 2.0 * arg2) * np.exp(-arg2)
    return np.ascontiguousarray(wavelet.astype(dtype_obj, copy=False))


def ricker_rsf(
    output_path: str | Path,
    frequency: float,
    dt: float,
    nt: int,
    *,
    t0: float | None = None,
    peak_time: float | None = None,
    amplitude: float = 1.0,
    dtype: str | np.dtype[Any] = "float32",
) -> RSFArray:
    """Write a 1D Ricker wavelet RSF file and return the loaded metadata."""

    frequency_value = _positive_float(frequency, "frequency")
    dt_value = _positive_float(dt, "dt")
    nt_value = _positive_int(nt, "nt")
    peak = _resolve_peak_time(frequency_value, t0=t0, peak_time=peak_time)
    data = ricker_wavelet(
        frequency_value,
        dt_value,
        nt_value,
        peak_time=peak,
        amplitude=amplitude,
        dtype=dtype,
    )
    header = RSFHeader(
        {
            "n1": nt_value,
            "o1": 0.0,
            "d1": dt_value,
            "label1": "Time",
            "unit1": "s",
            "ricker_frequency": frequency_value,
            "ricker_peak_time": peak,
            "ricker_amplitude": float(amplitude),
        }
    )
    return write_rsf(output_path, data, header)


def _resolve_peak_time(
    frequency: float,
    *,
    t0: float | None,
    peak_time: float | None,
) -> float:
    if t0 is None and peak_time is None:
        return 1.0 / frequency
    if t0 is None:
        assert peak_time is not None
        return float(peak_time)
    if peak_time is None:
        return float(t0)

    t0_value = float(t0)
    peak_value = float(peak_time)
    if not np.isclose(t0_value, peak_value, rtol=0.0, atol=1e-12):
        raise WaveletError("t0= and peak_time= are aliases and must match when both are provided")
    return peak_value


def _positive_float(value: float, name: str) -> float:
    normalized = float(value)
    if normalized <= 0.0:
        raise WaveletError(f"{name}= must be positive")
    return normalized


def _positive_int(value: int, name: str) -> int:
    normalized = int(value)
    if normalized < 1:
        raise WaveletError(f"{name}= must be positive")
    return normalized
