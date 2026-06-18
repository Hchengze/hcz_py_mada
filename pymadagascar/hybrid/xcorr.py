"""Hybrid batch cross-correlation kernels."""

from __future__ import annotations

from typing import Any, Literal

import numpy as np

from . import array_ops


XcorrMode = Literal["full", "same", "valid"]
_LAST_BACKEND = "numpy"


def batch_xcorr_cpp(data: Any, *, axis: int = -1, mode: XcorrMode = "full") -> np.ndarray:
    """Autocorrelate every trace along an axis with C++ when available.

    The optional C++ kernel operates on a contiguous 2D trace matrix. This
    wrapper keeps the public API NumPy-like: it accepts arbitrary-dimensional
    arrays, supports non-contiguous inputs, and falls back to a pure NumPy
    reference loop when the extension is unavailable or disabled.
    """

    global _LAST_BACKEND
    normalized_mode = _normalize_mode(mode)
    array = np.asarray(data)
    numpy_axis = _normalize_axis(axis, array.ndim)
    moved = np.moveaxis(array, numpy_axis, -1)
    trace_shape = moved.shape[:-1]
    nsamples = moved.shape[-1]
    if nsamples < 1:
        raise ValueError("traces must have at least one sample")
    traces = np.ascontiguousarray(moved.reshape((-1, nsamples)))

    core = array_ops._load_core()
    if core is not None and traces.dtype in (np.dtype("float32"), np.dtype("float64")):
        _LAST_BACKEND = "cpp"
        result_2d = np.asarray(core.batch_xcorr_cpp(traces, normalized_mode))
    else:
        _LAST_BACKEND = "numpy"
        result_2d = _batch_xcorr_numpy(traces, mode=normalized_mode)

    out_len = _mode_length(nsamples, normalized_mode)
    reshaped = result_2d.reshape(trace_shape + (out_len,))
    return np.ascontiguousarray(np.moveaxis(reshaped, -1, numpy_axis))


def xcorr_backend_name() -> str:
    """Return the backend that would be used for float32/float64 xcorr data."""

    return "cpp" if array_ops.cpp_available() else "numpy"


def last_xcorr_backend() -> str:
    """Return the backend used by the most recent batch_xcorr_cpp call."""

    return _LAST_BACKEND


def _batch_xcorr_numpy(traces: np.ndarray, *, mode: XcorrMode = "full") -> np.ndarray:
    """Pure NumPy reference implementation for a 2D trace matrix."""

    normalized_mode = _normalize_mode(mode)
    matrix = np.asarray(traces)
    if matrix.ndim != 2:
        raise ValueError("_batch_xcorr_numpy expects a 2D trace matrix")
    if matrix.shape[1] < 1:
        raise ValueError("traces must have at least one sample")
    output = np.empty((matrix.shape[0], _mode_length(matrix.shape[1], normalized_mode)), dtype=matrix.dtype)
    for index, trace in enumerate(matrix):
        output[index] = np.correlate(trace, trace, mode=normalized_mode)
    return output


def _reset_xcorr_for_tests() -> None:
    global _LAST_BACKEND
    _LAST_BACKEND = "numpy"
    array_ops._reset_core_for_tests()


def _normalize_axis(axis: int, ndim: int) -> int:
    if ndim < 1:
        raise ValueError("batch_xcorr_cpp requires at least one dimension")
    value = int(axis)
    if value < 0:
        value += ndim
    if value < 0 or value >= ndim:
        raise ValueError(f"axis must be between {-ndim} and {ndim - 1}")
    return value


def _normalize_mode(mode: str) -> XcorrMode:
    normalized = str(mode).strip().lower()
    if normalized in {"full", "same", "valid"}:
        return normalized  # type: ignore[return-value]
    raise ValueError("mode must be full, same, or valid")


def _mode_length(n: int, mode: XcorrMode) -> int:
    if n < 1:
        raise ValueError("traces must have at least one sample")
    if mode == "full":
        return 2 * n - 1
    if mode == "same":
        return n
    if mode == "valid":
        return 1
    raise ValueError(f"unsupported mode {mode!r}")
