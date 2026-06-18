"""Small-data signal conditioning and local-QC helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal
import warnings

import numpy as np

from pymadagascar.core.hypercube import Hypercube
from pymadagascar.io.rsf import RSFArray, read_rsf, write_rsf
from pymadagascar.signal.filter import FilterError, make_filter_taper


NanPolicy = Literal["propagate", "omit", "raise"]
DetrendType = Literal["constant", "linear"]


class SignalQCError(ValueError):
    """Raised when a signal-QC request is invalid."""


def demean(
    data: Any,
    axis: int | None = None,
    nan_policy: NanPolicy = "propagate",
) -> np.ndarray:
    """Subtract the global or axis-wise mean while preserving shape."""

    array = _coerce_numeric_array(data)
    policy = _normalize_nan_policy(nan_policy)
    numpy_axis = _numpy_axis(axis, array.ndim)
    _raise_for_nan(array, policy)
    reducer = np.nanmean if policy == "omit" else np.mean
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        center = reducer(array, axis=numpy_axis, keepdims=numpy_axis is not None)
    result = array - center
    return np.ascontiguousarray(result.astype(_transform_dtype(array), copy=False))


def detrend(
    data: Any,
    axis: int = 1,
    type: DetrendType = "linear",
    nan_policy: NanPolicy = "propagate",
) -> np.ndarray:
    """Remove a constant or least-squares linear trend along one RSF axis."""

    array = _coerce_numeric_array(data)
    kind = str(type).strip().lower()
    if kind not in {"constant", "linear"}:
        raise SignalQCError("type must be constant or linear")
    policy = _normalize_nan_policy(nan_policy)
    numpy_axis = _numpy_axis(axis, array.ndim)
    assert numpy_axis is not None
    if kind == "constant":
        return demean(array, axis=axis, nan_policy=policy)
    if array.shape[numpy_axis] < 2:
        raise SignalQCError("linear detrend requires at least two samples")
    _raise_for_nan(array, policy)

    dtype = _transform_dtype(array)
    moved = np.moveaxis(array.astype(dtype, copy=False), numpy_axis, -1)
    traces = moved.reshape(-1, moved.shape[-1])
    x = np.arange(moved.shape[-1], dtype=np.float64)
    output = np.empty_like(traces, dtype=dtype)
    for index, trace in enumerate(traces):
        output[index] = _detrend_trace(trace, x, policy)
    restored = np.moveaxis(output.reshape(moved.shape), -1, numpy_axis)
    return np.ascontiguousarray(restored)


def decimate(
    data: Any,
    factor: int,
    axis: int = 1,
    anti_alias: bool = True,
    filter: str = "moving_average",
) -> np.ndarray:
    """Downsample one RSF axis by an integer factor."""

    array = _coerce_numeric_array(data)
    factor = int(factor)
    if factor < 1:
        raise SignalQCError("factor must be a positive integer")
    filter_name = str(filter).strip().lower()
    if filter_name not in {"moving_average", "none"}:
        raise SignalQCError("filter must be moving_average or none")
    numpy_axis = _numpy_axis(axis, array.ndim)
    assert numpy_axis is not None
    working = array.astype(_transform_dtype(array), copy=False)
    if anti_alias and factor > 1:
        if filter_name == "none":
            raise SignalQCError("filter=none requires anti_alias=n")
        working = _moving_average(working, factor, numpy_axis)
    slices = [slice(None)] * working.ndim
    slices[numpy_axis] = slice(None, None, factor)
    return np.ascontiguousarray(working[tuple(slices)])


def bandstop(
    data: Any,
    dt: float,
    fmin: float,
    fmax: float,
    axis: int = 1,
    taper: float = 0.0,
) -> np.ndarray:
    """Apply a zero-phase FFT band-stop filter to real-valued data."""

    array = _coerce_real_array(data, operation="bandstop")
    numpy_axis = _numpy_axis(axis, array.ndim)
    assert numpy_axis is not None
    dt = float(dt)
    if dt <= 0.0:
        raise SignalQCError("dt must be positive")
    low = float(fmin)
    high = float(fmax)
    taper = float(taper)
    nyquist = 0.5 / dt
    if low < 0.0 or low >= high:
        raise SignalQCError("fmin must be non-negative and smaller than fmax")
    if high > nyquist:
        raise SignalQCError(f"fmax must not exceed Nyquist ({nyquist:g})")
    if taper < 0.0:
        raise SignalQCError("taper must be non-negative")

    frequencies = np.fft.rfftfreq(array.shape[numpy_axis], d=dt)
    try:
        stop_band = make_filter_taper(
            frequencies,
            kind="bandpass",
            flo=low,
            fhi=high,
            taper=taper,
        )
    except FilterError as exc:
        raise SignalQCError(str(exc)) from exc
    response = 1.0 - stop_band
    response_shape = [1] * array.ndim
    response_shape[numpy_axis] = response.size
    spectrum = np.fft.rfft(array.astype(np.float64, copy=False), axis=numpy_axis)
    result = np.fft.irfft(
        spectrum * response.reshape(response_shape),
        n=array.shape[numpy_axis],
        axis=numpy_axis,
    )
    return np.ascontiguousarray(result.astype(_real_output_dtype(array), copy=False))


def notch(
    data: Any,
    dt: float,
    f0: float,
    width: float | None = None,
    q: float | None = None,
    axis: int = 1,
    taper: float = 0.0,
) -> np.ndarray:
    """Apply a narrow band-stop centered on ``f0``."""

    center = float(f0)
    if center <= 0.0:
        raise SignalQCError("f0 must be positive")
    if width is not None and q is not None:
        raise SignalQCError("specify width or q, not both")
    if width is None:
        if q is None or float(q) <= 0.0:
            raise SignalQCError("width or q is required; q must be positive")
        width_value = center / float(q)
    else:
        width_value = float(width)
    if width_value <= 0.0:
        raise SignalQCError("width must be positive")
    return bandstop(
        data,
        dt=dt,
        fmin=center - 0.5 * width_value,
        fmax=center + 0.5 * width_value,
        axis=axis,
        taper=taper,
    )


def local_rms(data: Any, rect: int, axis: int = 1, mode: str = "same") -> np.ndarray:
    """Compute centered sliding RMS with clipped windows at the boundaries."""

    array = _coerce_numeric_array(data)
    if str(mode).strip().lower() != "same":
        raise SignalQCError("mode currently supports only same")
    window = int(rect)
    if window < 1:
        raise SignalQCError("rect must be a positive sample count")
    numpy_axis = _numpy_axis(axis, array.ndim)
    assert numpy_axis is not None
    window = min(window, array.shape[numpy_axis])

    moved = np.moveaxis(array, numpy_axis, -1)
    traces = moved.reshape(-1, moved.shape[-1])
    output_dtype = _real_output_dtype(array)
    output = np.empty(traces.shape, dtype=output_dtype)
    kernel = np.ones(window, dtype=np.float64)
    for index, trace in enumerate(traces):
        power = np.square(np.abs(trace).astype(np.float64, copy=False))
        summed = np.convolve(power, kernel, mode="same")
        count = np.convolve(np.ones(trace.size, dtype=np.float64), kernel, mode="same")
        output[index] = np.sqrt(summed / count).astype(output_dtype, copy=False)
    restored = np.moveaxis(output.reshape(moved.shape), -1, numpy_axis)
    return np.ascontiguousarray(restored)


def demean_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    axis: int | None = None,
    nan_policy: NanPolicy = "propagate",
) -> RSFArray:
    """Write a shape-preserving demeaned RSF dataset."""

    rsf = read_rsf(input_path)
    result = demean(rsf.data, axis=axis, nan_policy=nan_policy)
    header = rsf.header.copy()
    header["demean_axis"] = "global" if axis in {None, 0} else int(axis)
    header["nan_policy"] = nan_policy
    return write_rsf(output_path, result, header)


def detrend_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    axis: int = 1,
    type: DetrendType = "linear",
    nan_policy: NanPolicy = "propagate",
) -> RSFArray:
    """Write a shape-preserving detrended RSF dataset."""

    rsf = read_rsf(input_path)
    result = detrend(rsf.data, axis=axis, type=type, nan_policy=nan_policy)
    header = rsf.header.copy()
    header["detrend_axis"] = axis
    header["detrend_type"] = type
    header["nan_policy"] = nan_policy
    return write_rsf(output_path, result, header)


def decimate_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    factor: int,
    axis: int = 1,
    anti_alias: bool = True,
    filter: str = "moving_average",
) -> RSFArray:
    """Write an integer-decimated RSF dataset and update axis sampling."""

    rsf = read_rsf(input_path)
    cube = Hypercube.from_header(rsf.header)
    rsf_axis = _validate_rsf_axis(axis, cube.ndim)
    result = decimate(
        rsf.data,
        factor=factor,
        axis=rsf_axis,
        anti_alias=anti_alias,
        filter=filter,
    )
    numpy_axis = cube.ndim - rsf_axis
    source_axis = cube.axis(rsf_axis)
    header = cube.update_axis(
        rsf_axis,
        n=result.shape[numpy_axis],
        d=source_axis.d * int(factor),
    ).to_header(rsf.header)
    header["decimate_factor"] = int(factor)
    header["anti_alias"] = bool(anti_alias)
    header["decimate_filter"] = filter
    return write_rsf(output_path, result, header)


def bandstop_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    fmin: float,
    fmax: float,
    axis: int = 1,
    taper: float = 0.0,
) -> RSFArray:
    """Write a shape-preserving zero-phase band-stop result."""

    rsf = read_rsf(input_path)
    cube = Hypercube.from_header(rsf.header)
    rsf_axis = _validate_rsf_axis(axis, cube.ndim)
    dt = cube.axis(rsf_axis).d
    result = bandstop(rsf.data, dt=dt, fmin=fmin, fmax=fmax, axis=rsf_axis, taper=taper)
    header = rsf.header.copy()
    header["bandstop_axis"] = rsf_axis
    header["bandstop_fmin"] = fmin
    header["bandstop_fmax"] = fmax
    header["bandstop_taper"] = taper
    return write_rsf(output_path, result, header)


def notch_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    f0: float,
    width: float | None = None,
    q: float | None = None,
    axis: int = 1,
    taper: float = 0.0,
) -> RSFArray:
    """Write a shape-preserving narrow band-stop result."""

    rsf = read_rsf(input_path)
    cube = Hypercube.from_header(rsf.header)
    rsf_axis = _validate_rsf_axis(axis, cube.ndim)
    result = notch(
        rsf.data,
        dt=cube.axis(rsf_axis).d,
        f0=f0,
        width=width,
        q=q,
        axis=rsf_axis,
        taper=taper,
    )
    header = rsf.header.copy()
    header["notch_axis"] = rsf_axis
    header["notch_f0"] = f0
    if width is not None:
        header["notch_width"] = width
    if q is not None:
        header["notch_q"] = q
    header["notch_taper"] = taper
    return write_rsf(output_path, result, header)


def localrms_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    rect: int,
    axis: int = 1,
) -> RSFArray:
    """Write a shape-preserving centered local-RMS attribute."""

    rsf = read_rsf(input_path)
    result = local_rms(rsf.data, rect=rect, axis=axis)
    header = rsf.header.copy()
    header["localrms_axis"] = axis
    header["localrms_rect"] = int(rect)
    return write_rsf(output_path, result, header)


def _detrend_trace(trace: np.ndarray, x: np.ndarray, policy: NanPolicy) -> np.ndarray:
    valid = ~np.isnan(trace) if policy == "omit" else np.ones(trace.size, dtype=bool)
    if np.count_nonzero(valid) < 2:
        raise SignalQCError("linear detrend requires at least two non-NaN samples per trace")
    xv = x[valid]
    yv = trace[valid]
    x_centered = xv - np.mean(xv)
    denominator = float(np.dot(x_centered, x_centered))
    slope = np.sum(x_centered * yv) / denominator
    intercept = np.mean(yv)
    trend = intercept + slope * (x - np.mean(xv))
    result = trace - trend
    if policy == "omit":
        result[~valid] = trace[~valid]
    return result


def _moving_average(array: np.ndarray, width: int, axis: int) -> np.ndarray:
    left = (width - 1) // 2
    right = width - 1 - left
    moved = np.moveaxis(array, axis, -1)
    traces = moved.reshape(-1, moved.shape[-1])
    kernel = np.full(width, 1.0 / width, dtype=np.float64)
    dtype = _transform_dtype(array)
    output = np.empty_like(traces, dtype=dtype)
    for index, trace in enumerate(traces):
        padded = np.pad(trace, (left, right), mode="edge")
        output[index] = np.convolve(padded, kernel, mode="valid").astype(dtype, copy=False)
    return np.moveaxis(output.reshape(moved.shape), -1, axis)


def _coerce_numeric_array(data: Any) -> np.ndarray:
    array = np.asarray(data)
    if array.ndim < 1 or array.ndim > 3:
        raise SignalQCError("signal QC currently supports 1D, 2D, and 3D data")
    if array.size == 0 or array.dtype.kind not in {"f", "i", "u", "c"}:
        raise SignalQCError("input must contain numeric samples")
    return array


def _coerce_real_array(data: Any, *, operation: str) -> np.ndarray:
    array = _coerce_numeric_array(data)
    if np.iscomplexobj(array):
        raise SignalQCError(f"{operation} currently requires real-valued input")
    return array


def _transform_dtype(array: np.ndarray) -> np.dtype[Any]:
    if array.dtype == np.dtype("float64"):
        return np.dtype("float64")
    if array.dtype == np.dtype("complex128"):
        return np.dtype("complex128")
    if np.iscomplexobj(array):
        return np.dtype("complex64")
    return np.dtype("float32")


def _real_output_dtype(array: np.ndarray) -> np.dtype[Any]:
    if array.dtype in {np.dtype("float64"), np.dtype("complex128")}:
        return np.dtype("float64")
    return np.dtype("float32")


def _numpy_axis(axis: int | None, ndim: int) -> int | None:
    if axis in {None, 0}:
        return None
    return ndim - _validate_rsf_axis(int(axis), ndim)


def _validate_rsf_axis(axis: int, ndim: int) -> int:
    value = int(axis)
    if value < 1 or value > ndim:
        raise SignalQCError(f"axis must be between 1 and {ndim}, got {axis}")
    return value


def _normalize_nan_policy(value: str) -> NanPolicy:
    normalized = str(value).strip().lower()
    if normalized not in {"propagate", "omit", "raise"}:
        raise SignalQCError("nan_policy must be propagate, omit, or raise")
    return normalized  # type: ignore[return-value]


def _raise_for_nan(array: np.ndarray, policy: NanPolicy) -> None:
    if policy == "raise" and bool(np.any(np.isnan(array))):
        raise SignalQCError("input contains NaN samples")


__all__ = [
    "SignalQCError",
    "bandstop",
    "bandstop_rsf",
    "decimate",
    "decimate_rsf",
    "demean",
    "demean_rsf",
    "detrend",
    "detrend_rsf",
    "local_rms",
    "localrms_rsf",
    "notch",
    "notch_rsf",
]
