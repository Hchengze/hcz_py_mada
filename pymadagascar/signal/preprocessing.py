"""Small signal preprocessing tools for in-memory and RSF workflows."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Literal

import numpy as np

from pymadagascar.core.axis import Axis
from pymadagascar.core.hypercube import Hypercube
from pymadagascar.io.rsf import RSFArray, RSFHeader, read_rsf, write_rsf


ThresholdMode = Literal["hard", "soft"]
SpectraMode = Literal["amplitude", "power"]


class PreprocessingError(ValueError):
    """Raised when a signal preprocessing request is invalid."""


def cosine_taper(
    data: Any,
    widths: int | Sequence[int] | Mapping[int, int],
    axes: int | Sequence[int] | None = None,
) -> np.ndarray:
    """Apply a separable cosine taper on selected 1-based RSF axes."""

    array = _coerce_numeric_array(data, allow_complex=True)
    axes_tuple = _normalize_axes(axes, array.ndim)
    width_map = _normalize_widths(widths, axes_tuple, array.ndim)

    result = array.copy()
    for rsf_axis in axes_tuple:
        width = width_map.get(rsf_axis, 0)
        if width == 0:
            continue
        numpy_axis = array.ndim - rsf_axis
        weights = _cosine_weights(result.shape[numpy_axis], width, rsf_axis)
        shape = [1] * result.ndim
        shape[numpy_axis] = weights.size
        result = result * weights.reshape(shape)
    return np.ascontiguousarray(result.astype(array.dtype, copy=False))


def costaper_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    widths: int | Sequence[int] | Mapping[int, int],
    axes: int | Sequence[int] | None = None,
) -> RSFArray:
    """Apply a shape-preserving cosine taper to an RSF file."""

    rsf = read_rsf(input_path)
    result = cosine_taper(rsf.data, widths=widths, axes=axes)
    return write_rsf(output_path, result, rsf.header.copy())


def threshold(
    data: Any,
    value: float,
    *,
    mode: ThresholdMode = "hard",
    substitute: float | complex = 0.0,
) -> np.ndarray:
    """Apply hard or soft magnitude thresholding."""

    threshold_value = float(value)
    if threshold_value < 0.0:
        raise PreprocessingError("value= must be nonnegative")

    normalized = mode.strip().lower()
    if normalized not in {"hard", "soft"}:
        raise PreprocessingError("mode= must be 'hard' or 'soft'")

    array = _coerce_numeric_array(data, allow_complex=True)
    amplitudes = np.abs(array)
    below = amplitudes < threshold_value

    if normalized == "hard":
        result = array.copy()
        result[below] = substitute
        return np.ascontiguousarray(_supported_output_dtype(result))

    if np.iscomplexobj(array):
        scale = np.zeros_like(amplitudes, dtype=np.float64)
        above = amplitudes >= threshold_value
        scale[above] = (amplitudes[above] - threshold_value) / np.maximum(amplitudes[above], np.finfo(float).eps)
        result = array * scale
    else:
        result = np.sign(array) * np.maximum(amplitudes - threshold_value, 0.0)
    result[below] = substitute
    return np.ascontiguousarray(_supported_output_dtype(result))


def threshold_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    value: float,
    mode: ThresholdMode = "hard",
    substitute: float | complex = 0.0,
) -> RSFArray:
    """Apply hard or soft thresholding to an RSF file."""

    rsf = read_rsf(input_path)
    result = threshold(rsf.data, value=value, mode=mode, substitute=substitute)
    return write_rsf(output_path, result, rsf.header.copy())


def spectra(
    data: Any,
    *,
    axis: int = 1,
    dt: float | None = None,
    mode: SpectraMode = "amplitude",
    average: bool = True,
) -> np.ndarray:
    """Return a simple one-sided RFFT amplitude or power spectrum."""

    array = _coerce_real_array(data)
    rsf_axis = _validate_axis(axis, array.ndim)
    normalized = mode.strip().lower()
    if normalized not in {"amplitude", "power"}:
        raise PreprocessingError("mode= must be 'amplitude' or 'power'")
    _normalize_dt(dt)

    numpy_axis = array.ndim - rsf_axis
    n = array.shape[numpy_axis]
    spectrum = np.fft.rfft(np.asarray(array, dtype=np.float64), axis=numpy_axis)
    values = np.abs(spectrum) / np.sqrt(float(n))
    if normalized == "power":
        values = values * values
    if average:
        mean_axes = tuple(i for i in range(values.ndim) if i != numpy_axis)
        if mean_axes:
            values = values.mean(axis=mean_axes)
    output_dtype = np.float64 if array.dtype == np.dtype("float64") else np.float32
    return np.ascontiguousarray(values.astype(output_dtype))


def spectra_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    axis: int = 1,
    mode: SpectraMode = "amplitude",
    average: bool = True,
) -> RSFArray:
    """Compute a simple one-sided spectrum from an RSF file."""

    rsf = read_rsf(input_path)
    cube = Hypercube.from_header(rsf.header)
    axis = _validate_axis(axis, cube.ndim)
    axis_obj = cube.axis(axis)
    dt = axis_obj.d
    result = spectra(rsf.data, axis=axis, dt=dt, mode=mode, average=average)
    header = _spectra_header(rsf.header, axis=axis, average=average, output_n=result.shape[-1] if average else result.shape[rsf.data.ndim - axis])
    return write_rsf(output_path, result, header)


def envelope(data: Any, *, axis: int = 1) -> np.ndarray:
    """Compute the analytic-signal envelope with a NumPy FFT Hilbert transform."""

    array = _coerce_real_array(data)
    rsf_axis = _validate_axis(axis, array.ndim)
    numpy_axis = array.ndim - rsf_axis
    analytic = _analytic_signal(array, axis=numpy_axis)
    result = np.abs(analytic)
    output_dtype = np.float64 if array.dtype == np.dtype("float64") else np.float32
    return np.ascontiguousarray(result.astype(output_dtype))


def envelope_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    axis: int = 1,
) -> RSFArray:
    """Compute a shape-preserving envelope for an RSF file."""

    rsf = read_rsf(input_path)
    result = envelope(rsf.data, axis=axis)
    return write_rsf(output_path, result, rsf.header.copy())


def _coerce_numeric_array(data: Any, *, allow_complex: bool) -> np.ndarray:
    array = np.asarray(data)
    if array.ndim < 1 or array.ndim > 3:
        raise PreprocessingError("signal preprocessing currently supports 1D, 2D, and 3D data")
    if np.iscomplexobj(array):
        if not allow_complex:
            raise PreprocessingError("this operation requires real-valued input")
        return np.asarray(array, dtype=np.complex64)
    if not np.issubdtype(array.dtype, np.number):
        raise PreprocessingError("signal preprocessing requires numeric data")
    return np.asarray(array, dtype=np.float64 if array.dtype == np.dtype("float64") else np.float32)


def _coerce_real_array(data: Any) -> np.ndarray:
    return _coerce_numeric_array(data, allow_complex=False)


def _normalize_axes(axes: int | Sequence[int] | None, ndim: int) -> tuple[int, ...]:
    if axes is None:
        values = tuple(range(1, ndim + 1))
    elif isinstance(axes, int):
        values = (axes,)
    else:
        values = tuple(int(axis) for axis in axes)
    if not values:
        raise PreprocessingError("axes must not be empty")
    if len(set(values)) != len(values):
        raise PreprocessingError("axes must not contain duplicates")
    for axis in values:
        _validate_axis(axis, ndim)
    return values


def _normalize_widths(
    widths: int | Sequence[int] | Mapping[int, int],
    axes: tuple[int, ...],
    ndim: int,
) -> dict[int, int]:
    if isinstance(widths, Mapping):
        values = {int(axis): _normalize_width(width, axis=int(axis)) for axis, width in widths.items()}
    elif isinstance(widths, int):
        values = {axis: _normalize_width(widths, axis=axis) for axis in axes}
    else:
        items = tuple(int(value) for value in widths)
        if len(items) == ndim:
            values = {axis: _normalize_width(width, axis=axis) for axis, width in enumerate(items, start=1)}
        elif len(items) == len(axes):
            values = {axis: _normalize_width(width, axis=axis) for axis, width in zip(axes, items)}
        else:
            raise PreprocessingError("widths length must match selected axes or all data dimensions")

    for axis in values:
        _validate_axis(axis, ndim)
    return {axis: values.get(axis, 0) for axis in axes}


def _normalize_width(value: int, *, axis: int) -> int:
    width = int(value)
    if width < 0:
        raise PreprocessingError(f"width{axis}= must be nonnegative")
    return width


def _cosine_weights(size: int, width: int, axis: int) -> np.ndarray:
    if width < 0:
        raise PreprocessingError(f"width{axis}= must be nonnegative")
    if width == 0:
        return np.ones(size, dtype=np.float32)
    if 2 * width > size:
        raise PreprocessingError(f"width{axis}= must be <= half of axis length {size}")
    ramp = np.arange(1, width + 1, dtype=np.float64)
    edge = np.sin(0.5 * np.pi * ramp / (width + 1.0)) ** 2
    weights = np.ones(size, dtype=np.float64)
    weights[:width] = edge
    weights[-width:] = edge[::-1]
    return weights.astype(np.float32)


def _validate_axis(axis: int, ndim: int) -> int:
    value = int(axis)
    if value < 1 or value > ndim:
        raise PreprocessingError(f"axis must be between 1 and {ndim}, got {axis}")
    return value


def _normalize_dt(value: float | None) -> float:
    dt = 1.0 if value is None else float(value)
    if dt <= 0.0:
        raise PreprocessingError("dt/d# must be positive")
    return dt


def _spectra_header(
    header: RSFHeader,
    *,
    axis: int,
    average: bool,
    output_n: int,
) -> RSFHeader:
    cube = Hypercube.from_header(header)
    axis_obj = cube.axis(axis)
    spacing = 1.0 / (axis_obj.n * _normalize_dt(axis_obj.d))
    freq_axis = Axis(
        n=output_n,
        o=0.0,
        d=spacing,
        label="Frequency",
        unit=_frequency_unit(axis_obj.unit),
        index=axis,
    )
    if average:
        return Hypercube([freq_axis.copy(index=1)]).to_header(header)
    return cube.update_axis(
        axis,
        n=freq_axis.n,
        o=freq_axis.o,
        d=freq_axis.d,
        label=freq_axis.label,
        unit=freq_axis.unit,
    ).to_header(header)


def _frequency_unit(unit: str | None) -> str | None:
    if unit is None:
        return None
    if unit == "s":
        return "Hz"
    if unit.startswith("1/"):
        return unit[2:]
    return f"1/{unit}"


def _analytic_signal(array: np.ndarray, *, axis: int) -> np.ndarray:
    n = array.shape[axis]
    spectrum = np.fft.fft(np.asarray(array, dtype=np.float64), axis=axis)
    multiplier = np.zeros(n, dtype=np.float64)
    if n == 1:
        multiplier[0] = 1.0
    elif n % 2 == 0:
        multiplier[0] = 1.0
        multiplier[n // 2] = 1.0
        multiplier[1 : n // 2] = 2.0
    else:
        multiplier[0] = 1.0
        multiplier[1 : (n + 1) // 2] = 2.0
    shape = [1] * array.ndim
    shape[axis] = n
    return np.fft.ifft(spectrum * multiplier.reshape(shape), axis=axis)


def _supported_output_dtype(data: np.ndarray) -> np.ndarray:
    array = np.asarray(data)
    if np.iscomplexobj(array):
        return np.asarray(array, dtype=np.complex64)
    if array.dtype == np.dtype("float64"):
        return np.asarray(array, dtype=np.float64)
    return np.asarray(array, dtype=np.float32)
