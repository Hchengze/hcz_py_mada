"""Convolution and correlation helpers for RSF datasets."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import numpy as np

from pymadagascar.core.hypercube import Hypercube
from pymadagascar.io.rsf import RSFArray, RSFHeader, read_rsf, write_rsf
from pymadagascar.signal.preprocessing import PreprocessingError, envelope


ConvMode = Literal["full", "same", "valid"]
ConvMethod = Literal["auto", "direct", "fft"]


class ConvolutionError(ValueError):
    """Raised when convolution or correlation parameters are invalid."""


def convolve_rsf(
    input_path: str | Path,
    filter_path: str | Path,
    output_path: str | Path,
    *,
    mode: ConvMode = "same",
    axis: int = 1,
    method: ConvMethod = "auto",
) -> RSFArray:
    """Convolve RSF data with a 1D or matching per-trace filter."""

    data_rsf = read_rsf(input_path)
    filter_rsf = read_rsf(filter_path)
    cube = Hypercube.from_header(data_rsf.header)
    axis = _validate_axis(axis, cube.ndim)
    filter_axis = _filter_axis(filter_rsf.header, axis, cube.ndim)
    _validate_sampling(data_rsf.header, filter_rsf.header, axis, filter_axis)

    result, out_len, crop_start = _apply_binary_operation(
        data_rsf.data,
        filter_rsf.data,
        axis=axis,
        mode=mode,
        method=method,
        operation="convolve",
    )
    data_axis = cube.axis(axis)
    kernel_axis = Hypercube.from_header(filter_rsf.header).axis(filter_axis)
    full_origin = data_axis.o + kernel_axis.o
    header = _updated_axis_header(data_rsf.header, axis, out_len, full_origin + crop_start * data_axis.d)
    return write_rsf(output_path, result, header)


def convolve(
    data: Any,
    kernel: Any,
    *,
    axis: int = 1,
    mode: ConvMode = "same",
    method: ConvMethod = "auto",
) -> np.ndarray:
    """Convolve an array with a 1D or matching per-trace kernel."""

    result, _, _ = _apply_binary_operation(
        np.asarray(data),
        np.asarray(kernel),
        axis=axis,
        mode=mode,
        method=method,
        operation="convolve",
    )
    return result


def correlate_rsf(
    input1_path: str | Path,
    input2_path: str | Path,
    output_path: str | Path,
    *,
    mode: ConvMode = "full",
    axis: int = 1,
    method: ConvMethod = "auto",
) -> RSFArray:
    """Cross-correlate two RSF datasets along a 1-based RSF axis."""

    first = read_rsf(input1_path)
    second = read_rsf(input2_path)
    cube = Hypercube.from_header(first.header)
    axis = _validate_axis(axis, cube.ndim)
    second_axis = _filter_axis(second.header, axis, cube.ndim)
    _validate_sampling(first.header, second.header, axis, second_axis)

    result, out_len, crop_start = _apply_binary_operation(
        first.data,
        second.data,
        axis=axis,
        mode=mode,
        method=method,
        operation="correlate",
    )
    first_axis = cube.axis(axis)
    second_axis_obj = Hypercube.from_header(second.header).axis(second_axis)
    full_origin = first_axis.o - second_axis_obj.o - (second_axis_obj.n - 1) * first_axis.d
    header = _updated_axis_header(first.header, axis, out_len, full_origin + crop_start * first_axis.d)
    return write_rsf(output_path, result, header)


def autocorr(
    data: Any,
    *,
    axis: int = 1,
    mode: Literal["full", "same"] = "full",
    normalize: bool = False,
    max_lag: int | None = None,
    method: ConvMethod = "auto",
) -> np.ndarray:
    """Autocorrelate every trace along a 1-based RSF axis."""

    array = np.asarray(data)
    if array.ndim < 1 or array.ndim > 3:
        raise ConvolutionError("autocorr currently supports 1D, 2D, and 3D data")
    rsf_axis = _validate_axis(axis, array.ndim)
    normalized_mode = _normalize_autocorr_mode(mode)
    numpy_axis = array.ndim - rsf_axis
    result = _apply_unary_trace_operation(
        array,
        numpy_axis=numpy_axis,
        mode=normalized_mode,
        method=method,
        operation="correlate",
    )
    if normalize:
        result = _normalize_autocorr(result, input_n=array.shape[numpy_axis], mode=normalized_mode, numpy_axis=numpy_axis)
    indices, _ = _lag_selection(array.shape[numpy_axis], normalized_mode, max_lag)
    if indices is not None:
        result = np.take(result, indices, axis=numpy_axis)
    return np.ascontiguousarray(result)


def autocorr_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    axis: int = 1,
    mode: Literal["full", "same"] = "full",
    normalize: bool = False,
    max_lag: int | None = None,
    method: ConvMethod = "auto",
) -> RSFArray:
    """Autocorrelate RSF traces along one 1-based RSF axis."""

    rsf = read_rsf(input_path)
    cube = Hypercube.from_header(rsf.header)
    axis = _validate_axis(axis, cube.ndim)
    axis_obj = cube.axis(axis)
    normalized_mode = _normalize_autocorr_mode(mode)
    result = autocorr(
        rsf.data,
        axis=axis,
        mode=normalized_mode,
        normalize=normalize,
        max_lag=max_lag,
        method=method,
    )
    _, origin_lag = _lag_selection(axis_obj.n, normalized_mode, max_lag)
    header = _updated_axis_header(
        rsf.header,
        axis,
        result.shape[cube.ndim - axis],
        origin_lag * axis_obj.d,
    )
    header[f"label{axis}"] = "Lag"
    return write_rsf(output_path, result, header)


def circular_convolve(
    data: Any,
    kernel: Any,
    *,
    axis: int = 1,
) -> np.ndarray:
    """Circularly convolve data with a 1D kernel along a 1-based RSF axis."""

    array = np.asarray(data)
    if array.ndim < 1 or array.ndim > 3:
        raise ConvolutionError("circular_convolve currently supports 1D, 2D, and 3D data")
    rsf_axis = _validate_axis(axis, array.ndim)
    kernel_1d = _as_1d(np.asarray(kernel), "kernel")
    numpy_axis = array.ndim - rsf_axis
    n = array.shape[numpy_axis]
    if kernel_1d.size > n:
        raise ConvolutionError("circular convolution kernel length must not exceed the data axis length")

    moved = np.moveaxis(array, numpy_axis, -1)
    traces = moved.reshape((-1, n))
    padded = np.zeros(n, dtype=np.result_type(array, kernel_1d, np.float32))
    padded[: kernel_1d.size] = kernel_1d
    kernel_spectrum = np.fft.fft(padded)
    output = np.empty_like(traces, dtype=np.result_type(array, kernel_1d, np.complex64))
    for index, trace in enumerate(traces):
        values = np.fft.ifft(np.fft.fft(trace) * kernel_spectrum)
        if not (np.iscomplexobj(array) or np.iscomplexobj(kernel_1d)):
            values = values.real
        output[index] = values
    out_dtype = _output_dtype(array, kernel_1d, force_float=True)
    reshaped = output.reshape(moved.shape)
    if not (np.iscomplexobj(array) or np.iscomplexobj(kernel_1d)):
        reshaped = reshaped.real
    reshaped = reshaped.astype(out_dtype, copy=False)
    return np.ascontiguousarray(np.moveaxis(reshaped, -1, numpy_axis))


def cconv_rsf(
    input_path: str | Path,
    kernel_path: str | Path,
    output_path: str | Path,
    *,
    axis: int = 1,
) -> RSFArray:
    """Circularly convolve RSF data with a 1D kernel and preserve input shape."""

    data_rsf = read_rsf(input_path)
    kernel_rsf = read_rsf(kernel_path)
    cube = Hypercube.from_header(data_rsf.header)
    axis = _validate_axis(axis, cube.ndim)
    kernel_axis = _filter_axis(kernel_rsf.header, axis, cube.ndim)
    _validate_sampling(data_rsf.header, kernel_rsf.header, axis, kernel_axis)
    result = circular_convolve(data_rsf.data, kernel_rsf.data, axis=axis)
    return write_rsf(output_path, result, data_rsf.header.copy())


def envelope_correlation(
    a: Any,
    b: Any,
    *,
    axis: int = 1,
    mode: Literal["full", "same"] = "same",
    normalize: bool = True,
    method: ConvMethod = "auto",
) -> np.ndarray:
    """Correlate analytic-signal envelopes for two arrays or a 1D template."""

    first = np.asarray(a)
    second = np.asarray(b)
    if first.ndim < 1 or first.ndim > 3:
        raise ConvolutionError("envelope_correlation currently supports 1D, 2D, and 3D data")
    rsf_axis = _validate_axis(axis, first.ndim)
    normalized_mode = _normalize_autocorr_mode(mode)
    try:
        first_env = envelope(first, axis=rsf_axis)
        second_env = envelope(second, axis=1 if second.ndim == 1 else rsf_axis)
    except PreprocessingError as exc:
        raise ConvolutionError(str(exc)) from exc
    result, _, _ = _apply_binary_operation(
        first_env,
        second_env,
        axis=rsf_axis,
        mode=normalized_mode,
        method=method,
        operation="correlate",
    )
    if normalize:
        result = _normalize_pair_correlation(result, first_env, second_env, axis=rsf_axis)
    return np.ascontiguousarray(result)


def envcorr_rsf(
    input_path: str | Path,
    other_path: str | Path,
    output_path: str | Path,
    *,
    axis: int = 1,
    mode: Literal["full", "same"] = "same",
    normalize: bool = True,
    method: ConvMethod = "auto",
) -> RSFArray:
    """Compute envelope correlation for two RSF files."""

    first = read_rsf(input_path)
    second = read_rsf(other_path)
    cube = Hypercube.from_header(first.header)
    axis = _validate_axis(axis, cube.ndim)
    second_axis = _filter_axis(second.header, axis, cube.ndim)
    _validate_sampling(first.header, second.header, axis, second_axis)
    normalized_mode = _normalize_autocorr_mode(mode)
    result = envelope_correlation(
        first.data,
        second.data,
        axis=axis,
        mode=normalized_mode,
        normalize=normalize,
        method=method,
    )
    first_axis = cube.axis(axis)
    second_axis_obj = Hypercube.from_header(second.header).axis(second_axis)
    crop_start = _crop_start(first_axis.n, second_axis_obj.n, normalized_mode)
    full_origin = first_axis.o - second_axis_obj.o - (second_axis_obj.n - 1) * first_axis.d
    header = _updated_axis_header(first.header, axis, result.shape[cube.ndim - axis], full_origin + crop_start * first_axis.d)
    header[f"label{axis}"] = "Envelope lag"
    return write_rsf(output_path, result, header)


def xcorr_traces(
    data: np.ndarray,
    *,
    axis: int = -1,
    mode: ConvMode = "full",
    method: ConvMethod = "auto",
) -> np.ndarray:
    """Autocorrelate every trace along a NumPy axis."""

    array = np.asarray(data)
    if array.ndim < 1:
        raise ConvolutionError("xcorr_traces requires at least one dimension")
    numpy_axis = int(axis)
    if numpy_axis < 0:
        numpy_axis += array.ndim
    if numpy_axis < 0 or numpy_axis >= array.ndim:
        raise ConvolutionError(f"axis must be between {-array.ndim} and {array.ndim - 1}")

    return _apply_unary_trace_operation(
        array,
        numpy_axis=numpy_axis,
        mode=mode,
        method=method,
        operation="correlate",
    )


def xcorr_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    mode: ConvMode = "full",
    axis: int = 1,
    method: ConvMethod = "auto",
) -> RSFArray:
    """Autocorrelate each RSF trace along a 1-based RSF axis."""

    rsf = read_rsf(input_path)
    cube = Hypercube.from_header(rsf.header)
    axis = _validate_axis(axis, cube.ndim)
    axis_obj = cube.axis(axis)
    numpy_axis = cube.ndim - axis
    result = xcorr_traces(rsf.data, axis=numpy_axis, mode=mode, method=method)
    out_len = result.shape[numpy_axis]
    crop_start = _crop_start(axis_obj.n, axis_obj.n, _normalize_mode(mode))
    full_origin = -(axis_obj.n - 1) * axis_obj.d
    header = _updated_axis_header(rsf.header, axis, out_len, full_origin + crop_start * axis_obj.d)
    header[f"label{axis}"] = "Lag"
    return write_rsf(output_path, result, header)


def fft_convolve(
    a: np.ndarray,
    b: np.ndarray,
    mode: ConvMode = "full",
) -> np.ndarray:
    """Convolve two 1D arrays using FFT multiplication."""

    left = _as_1d(a, "a")
    right = _as_1d(b, "b")
    mode = _normalize_mode(mode)
    full_len = left.size + right.size - 1
    if full_len < 1:
        raise ConvolutionError("cannot convolve empty arrays")

    nfft = 1 << (full_len - 1).bit_length()
    spectrum = np.fft.fft(left, n=nfft) * np.fft.fft(right, n=nfft)
    full = np.fft.ifft(spectrum, n=nfft)[:full_len]
    if not (np.iscomplexobj(left) or np.iscomplexobj(right)):
        full = full.real
    return _crop_full(full, left.size, right.size, mode)


def _apply_binary_operation(
    data: np.ndarray,
    other: np.ndarray,
    *,
    axis: int,
    mode: ConvMode,
    method: ConvMethod,
    operation: Literal["convolve", "correlate"],
) -> tuple[np.ndarray, int, int]:
    array = np.asarray(data)
    kernel = np.asarray(other)
    if array.ndim < 1:
        raise ConvolutionError("input data must have at least one dimension")
    mode = _normalize_mode(mode)
    method = _normalize_method(method)
    numpy_axis = array.ndim - _validate_axis(axis, array.ndim)

    moved = np.moveaxis(array, numpy_axis, -1)
    trace_shape = moved.shape[:-1]
    traces = moved.reshape((-1, moved.shape[-1]))
    kernels = _broadcast_kernels(kernel, trace_shape, axis=axis, data_ndim=array.ndim)
    out_len = _mode_length(traces.shape[-1], kernels.shape[-1], mode)
    crop_start = _crop_start(traces.shape[-1], kernels.shape[-1], mode)
    out_dtype = _output_dtype(array, kernel, force_float=False)
    output = np.empty((traces.shape[0], out_len), dtype=out_dtype)

    for index, trace in enumerate(traces):
        output[index] = _trace_operation(
            trace,
            kernels[index],
            mode=mode,
            method=method,
            operation=operation,
        ).astype(out_dtype, copy=False)

    reshaped = output.reshape(trace_shape + (out_len,))
    result = np.moveaxis(reshaped, -1, numpy_axis)
    return np.ascontiguousarray(result), out_len, crop_start


def _apply_unary_trace_operation(
    data: np.ndarray,
    *,
    numpy_axis: int,
    mode: ConvMode,
    method: ConvMethod,
    operation: Literal["correlate"],
) -> np.ndarray:
    mode = _normalize_mode(mode)
    method = _normalize_method(method)
    moved = np.moveaxis(np.asarray(data), numpy_axis, -1)
    trace_shape = moved.shape[:-1]
    traces = moved.reshape((-1, moved.shape[-1]))
    out_len = _mode_length(traces.shape[-1], traces.shape[-1], mode)
    out_dtype = _output_dtype(data, data, force_float=False)
    output = np.empty((traces.shape[0], out_len), dtype=out_dtype)
    for index, trace in enumerate(traces):
        output[index] = _trace_operation(
            trace,
            trace,
            mode=mode,
            method=method,
            operation=operation,
        ).astype(out_dtype, copy=False)
    reshaped = output.reshape(trace_shape + (out_len,))
    return np.ascontiguousarray(np.moveaxis(reshaped, -1, numpy_axis))


def _trace_operation(
    trace: np.ndarray,
    kernel: np.ndarray,
    *,
    mode: ConvMode,
    method: ConvMethod,
    operation: Literal["convolve", "correlate"],
) -> np.ndarray:
    trace = _as_1d(trace, "trace")
    kernel = _as_1d(kernel, "kernel")
    selected = _select_method(trace.size, kernel.size, method)
    if operation == "convolve":
        return np.convolve(trace, kernel, mode=mode) if selected == "direct" else fft_convolve(trace, kernel, mode=mode)
    corr_kernel = np.conjugate(kernel[::-1])
    if selected == "direct":
        return np.correlate(trace, kernel, mode=mode)
    return fft_convolve(trace, corr_kernel, mode=mode)


def _normalize_autocorr(
    result: np.ndarray,
    *,
    input_n: int,
    mode: ConvMode,
    numpy_axis: int,
) -> np.ndarray:
    _, origin_lag = _lag_selection(input_n, mode, None)
    zero_index = -origin_lag
    if zero_index < 0 or zero_index >= result.shape[numpy_axis]:
        raise ConvolutionError("zero lag is not present in autocorrelation output")
    zero = np.take(result, zero_index, axis=numpy_axis)
    shape = list(result.shape)
    shape[numpy_axis] = 1
    denom = zero.reshape(shape)
    return np.divide(result, denom, out=np.zeros_like(result), where=np.abs(denom) > 0)


def _normalize_pair_correlation(
    result: np.ndarray,
    first: np.ndarray,
    second: np.ndarray,
    *,
    axis: int,
) -> np.ndarray:
    first_array = np.asarray(first, dtype=np.float64)
    second_array = np.asarray(second, dtype=np.float64)
    numpy_axis = first_array.ndim - _validate_axis(axis, first_array.ndim)
    moved_first = np.moveaxis(first_array, numpy_axis, -1)
    trace_shape = moved_first.shape[:-1]
    traces = moved_first.reshape((-1, moved_first.shape[-1]))
    kernels = _broadcast_kernels(second_array, trace_shape, axis=axis, data_ndim=first_array.ndim)
    denom = np.sqrt(np.sum(traces * traces, axis=1) * np.sum(kernels * kernels, axis=1))

    moved_result = np.moveaxis(result, numpy_axis, -1)
    flat_result = moved_result.reshape((-1, moved_result.shape[-1]))
    normalized = np.divide(
        flat_result,
        denom[:, np.newaxis],
        out=np.zeros_like(flat_result),
        where=denom[:, np.newaxis] > 0,
    )
    reshaped = normalized.reshape(moved_result.shape)
    return np.ascontiguousarray(np.moveaxis(reshaped, -1, numpy_axis).astype(result.dtype, copy=False))


def _lag_selection(
    input_n: int,
    mode: ConvMode,
    max_lag: int | None,
) -> tuple[np.ndarray | None, int]:
    mode = _normalize_mode(mode)
    out_len = _mode_length(input_n, input_n, mode)
    crop_start = _crop_start(input_n, input_n, mode)
    origin_lag = -(input_n - 1) + crop_start
    if max_lag is None:
        return None, origin_lag
    lag = int(max_lag)
    if lag < 0:
        raise ConvolutionError("max_lag= must be nonnegative")
    lags = origin_lag + np.arange(out_len)
    indices = np.flatnonzero(np.abs(lags) <= lag)
    if indices.size == 0:
        raise ConvolutionError("max_lag= selection removed all lag samples")
    return indices, int(lags[indices[0]])


def _broadcast_kernels(
    kernel: np.ndarray,
    trace_shape: tuple[int, ...],
    *,
    axis: int,
    data_ndim: int,
) -> np.ndarray:
    squeezed = np.asarray(kernel)
    if squeezed.ndim == 1:
        return np.broadcast_to(squeezed, (int(np.prod(trace_shape, dtype=np.int64)), squeezed.size))
    if squeezed.ndim != data_ndim:
        raise ConvolutionError(
            "filter must be either 1D or have the same dimensionality as the input"
        )

    numpy_axis = data_ndim - axis
    moved = np.moveaxis(squeezed, numpy_axis, -1)
    if moved.shape[:-1] != trace_shape:
        raise ConvolutionError(
            f"non-convolution axes mismatch: filter shape {squeezed.shape} is not compatible with trace shape {trace_shape}"
        )
    return moved.reshape((-1, moved.shape[-1]))


def _updated_axis_header(header: RSFHeader, axis: int, n: int, origin: float) -> RSFHeader:
    cube = Hypercube.from_header(header)
    axis_obj = cube.axis(axis)
    return cube.update_axis(axis, n=n, o=origin, d=axis_obj.d).to_header(header.copy())


def _filter_axis(filter_header: RSFHeader, data_axis: int, data_ndim: int) -> int:
    filter_ndim = len(filter_header.dimensions)
    if filter_ndim == 1:
        return 1
    if filter_ndim != data_ndim:
        raise ConvolutionError(
            f"filter dimensionality {filter_ndim} must be 1 or match input dimensionality {data_ndim}"
        )
    return data_axis


def _validate_sampling(
    first: RSFHeader,
    second: RSFHeader,
    first_axis: int,
    second_axis: int,
) -> None:
    d1 = float(first.get(f"d{first_axis}", 1.0))
    d2 = float(second.get(f"d{second_axis}", 1.0))
    if not np.isclose(d1, d2, rtol=1e-6, atol=1e-12):
        raise ConvolutionError(
            f"sampling mismatch: d{first_axis}={d1:g} and filter d{second_axis}={d2:g}"
        )


def _output_dtype(a: np.ndarray, b: np.ndarray, *, force_float: bool) -> np.dtype:
    left = np.asarray(a).dtype
    right = np.asarray(b).dtype
    if np.issubdtype(left, np.complexfloating) or np.issubdtype(right, np.complexfloating):
        return np.dtype("complex64")
    if left == np.dtype("float64") or right == np.dtype("float64"):
        return np.dtype("float64")
    if force_float or np.issubdtype(left, np.floating) or np.issubdtype(right, np.floating):
        return np.dtype("float32")
    return np.dtype("float32")


def _select_method(n: int, m: int, method: ConvMethod) -> Literal["direct", "fft"]:
    method = _normalize_method(method)
    if method != "auto":
        return method
    return "fft" if n * m > 4096 else "direct"


def _crop_full(full: np.ndarray, n: int, m: int, mode: ConvMode) -> np.ndarray:
    mode = _normalize_mode(mode)
    start = _crop_start(n, m, mode)
    length = _mode_length(n, m, mode)
    return full[start : start + length]


def _crop_start(n: int, m: int, mode: ConvMode) -> int:
    if mode == "full":
        return 0
    if mode == "same":
        return (n + m - 1 - max(n, m)) // 2
    if mode == "valid":
        return min(n, m) - 1
    raise ConvolutionError(f"unsupported mode {mode!r}")


def _mode_length(n: int, m: int, mode: ConvMode) -> int:
    if n < 1 or m < 1:
        raise ConvolutionError("input traces and kernels must be non-empty")
    if mode == "full":
        return n + m - 1
    if mode == "same":
        return max(n, m)
    if mode == "valid":
        return max(n, m) - min(n, m) + 1
    raise ConvolutionError(f"unsupported mode {mode!r}")


def _normalize_mode(mode: str) -> ConvMode:
    normalized = str(mode).strip().lower()
    if normalized in {"full", "same", "valid"}:
        return normalized  # type: ignore[return-value]
    raise ConvolutionError("mode= must be full, same, or valid")


def _normalize_autocorr_mode(mode: str) -> Literal["full", "same"]:
    normalized = str(mode).strip().lower()
    if normalized in {"full", "same"}:
        return normalized  # type: ignore[return-value]
    raise ConvolutionError("mode= must be full or same")


def _normalize_method(method: str) -> ConvMethod:
    normalized = str(method).strip().lower()
    if normalized in {"auto", "direct", "fft"}:
        return normalized  # type: ignore[return-value]
    raise ConvolutionError("method= must be auto, direct, or fft")


def _validate_axis(axis: int, ndim: int) -> int:
    value = int(axis)
    if value < 1 or value > ndim:
        raise ConvolutionError(f"axis must be between 1 and {ndim}, got {axis}")
    return value


def _as_1d(values: np.ndarray, name: str) -> np.ndarray:
    array = np.asarray(values)
    if array.ndim != 1:
        raise ConvolutionError(f"{name} must be 1D")
    if array.size < 1:
        raise ConvolutionError(f"{name} must be non-empty")
    return array
