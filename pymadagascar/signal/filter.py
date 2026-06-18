"""Frequency-domain filters for file-backed RSF datasets."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import numpy as np

from pymadagascar.core.hypercube import Hypercube
from pymadagascar.io.rsf import RSFArray, read_rsf, write_rsf


FilterKind = Literal["bandpass", "lowpass", "highpass"]


class FilterError(ValueError):
    """Raised when a frequency-domain filter request is invalid."""


def bandpass_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    flo: float,
    fhi: float,
    axis: int = 1,
    taper: float = 0.0,
) -> RSFArray:
    """Apply a zero-phase FFT bandpass filter to real-valued RSF data."""

    return _filter_rsf(
        input_path,
        output_path,
        kind="bandpass",
        axis=axis,
        flo=flo,
        fhi=fhi,
        taper=taper,
    )


def lowpass_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    fcut: float,
    axis: int = 1,
    taper: float = 0.0,
) -> RSFArray:
    """Apply a zero-phase FFT lowpass filter to real-valued RSF data."""

    return _filter_rsf(
        input_path,
        output_path,
        kind="lowpass",
        axis=axis,
        fcut=fcut,
        taper=taper,
    )


def highpass_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    fcut: float,
    axis: int = 1,
    taper: float = 0.0,
) -> RSFArray:
    """Apply a zero-phase FFT highpass filter to real-valued RSF data."""

    return _filter_rsf(
        input_path,
        output_path,
        kind="highpass",
        axis=axis,
        fcut=fcut,
        taper=taper,
    )


def make_filter_taper(
    frequencies: np.ndarray,
    *,
    kind: FilterKind = "bandpass",
    flo: float | None = None,
    fhi: float | None = None,
    fcut: float | None = None,
    taper: float = 0.0,
) -> np.ndarray:
    """Create a real-valued zero-phase frequency taper.

    Frequencies are ordinary cycles per unit of ``d#``. For time axes measured
    in seconds, this means Hz.
    """

    freq = np.asarray(frequencies, dtype=np.float64)
    if freq.ndim != 1:
        raise FilterError("frequencies must be a 1D array")
    if np.any(freq < 0):
        raise FilterError("frequencies must be non-negative")
    if taper < 0:
        raise FilterError("taper= must be non-negative")

    if kind == "bandpass":
        low = _require_frequency(flo, "flo")
        high = _require_frequency(fhi, "fhi")
        if low >= high:
            raise FilterError("flo= must be smaller than fhi=")
        response = _highpass_response(freq, low, taper) * _lowpass_response(freq, high, taper)
    elif kind == "lowpass":
        cutoff = _require_frequency(fcut, "fcut")
        response = _lowpass_response(freq, cutoff, taper)
    elif kind == "highpass":
        cutoff = _require_frequency(fcut, "fcut")
        response = _highpass_response(freq, cutoff, taper)
    else:
        raise FilterError(f"unsupported filter kind {kind!r}")
    return response.astype(np.float32)


def _filter_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    kind: FilterKind,
    axis: int,
    taper: float,
    flo: float | None = None,
    fhi: float | None = None,
    fcut: float | None = None,
) -> RSFArray:
    rsf = read_rsf(input_path)
    if np.iscomplexobj(rsf.data):
        raise FilterError("frequency-domain filters currently require real-valued input")

    cube = Hypercube.from_header(rsf.header)
    axis = _validate_axis(axis, cube.ndim)
    axis_obj = cube.axis(axis)
    if axis_obj.d <= 0.0:
        raise FilterError(f"d{axis}= must be positive")
    nyquist = 0.5 / axis_obj.d
    _validate_frequency_limits(kind=kind, nyquist=nyquist, flo=flo, fhi=fhi, fcut=fcut, taper=taper)

    numpy_axis = cube.ndim - axis
    frequencies = np.fft.rfftfreq(axis_obj.n, d=axis_obj.d)
    response = make_filter_taper(
        frequencies,
        kind=kind,
        flo=flo,
        fhi=fhi,
        fcut=fcut,
        taper=taper,
    )
    shape = [1] * rsf.data.ndim
    shape[numpy_axis] = response.size
    response_nd = response.reshape(shape)

    spectrum = np.fft.rfft(np.asarray(rsf.data, dtype=np.float64), axis=numpy_axis)
    filtered = np.fft.irfft(spectrum * response_nd, n=axis_obj.n, axis=numpy_axis)
    output_dtype = np.float64 if rsf.data.dtype == np.dtype("float64") else np.float32
    output = np.ascontiguousarray(filtered.astype(output_dtype))
    return write_rsf(output_path, output, rsf.header.copy())


def _lowpass_response(freq: np.ndarray, cutoff: float, taper: float) -> np.ndarray:
    response = np.zeros_like(freq, dtype=np.float64)
    if taper == 0.0:
        response[freq <= cutoff] = 1.0
        return response

    stop_start = cutoff + taper
    response[freq <= cutoff] = 1.0
    ramp = (freq > cutoff) & (freq < stop_start)
    response[ramp] = 0.5 * (1.0 + np.cos(np.pi * (freq[ramp] - cutoff) / taper))
    return response


def _highpass_response(freq: np.ndarray, cutoff: float, taper: float) -> np.ndarray:
    response = np.zeros_like(freq, dtype=np.float64)
    if taper == 0.0:
        response[freq >= cutoff] = 1.0
        return response

    stop_end = max(0.0, cutoff - taper)
    response[freq >= cutoff] = 1.0
    ramp = (freq > stop_end) & (freq < cutoff)
    response[ramp] = 0.5 * (1.0 - np.cos(np.pi * (freq[ramp] - stop_end) / (cutoff - stop_end)))
    return response


def _validate_frequency_limits(
    *,
    kind: FilterKind,
    nyquist: float,
    taper: float,
    flo: float | None,
    fhi: float | None,
    fcut: float | None,
) -> None:
    if taper > nyquist:
        raise FilterError(f"taper= must not exceed Nyquist ({nyquist:g})")
    if kind == "bandpass":
        low = _require_frequency(flo, "flo")
        high = _require_frequency(fhi, "fhi")
        if low >= high:
            raise FilterError("flo= must be smaller than fhi=")
        if high > nyquist:
            raise FilterError(f"fhi= must not exceed Nyquist ({nyquist:g})")
    else:
        cutoff = _require_frequency(fcut, "fcut")
        if cutoff > nyquist:
            raise FilterError(f"fcut= must not exceed Nyquist ({nyquist:g})")


def _require_frequency(value: float | None, name: str) -> float:
    if value is None:
        raise FilterError(f"{name}= is required")
    number = float(value)
    if number < 0.0:
        raise FilterError(f"{name}= must be non-negative")
    return number


def _validate_axis(axis: int, ndim: int) -> int:
    value = int(axis)
    if value < 1 or value > ndim:
        raise FilterError(f"axis must be between 1 and {ndim}, got {axis}")
    return value
