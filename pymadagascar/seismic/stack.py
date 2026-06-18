"""Stack RSF seismic gathers along a selected axis."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from pymadagascar.core.hypercube import Hypercube
from pymadagascar.io.rsf import RSFArray, read_rsf, write_rsf

from ._utils import header_without_axis, numpy_axis, output_dtype, validate_rsf_axis


class StackError(ValueError):
    """Raised when stack parameters are invalid."""


def stack_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    axis: int = 2,
    mode: str = "mean",
    nonzero: bool = True,
) -> RSFArray:
    """Stack an RSF dataset over one 1-based RSF axis.

    ``mode="mean"`` divides by fold. With ``nonzero=True`` the fold counts
    only nonzero samples, matching Madagascar ``sfstack``'s default behavior.
    """

    rsf = read_rsf(input_path)
    cube = Hypercube.from_header(rsf.header)
    axis = validate_rsf_axis(axis, cube.ndim)
    operation = _normalize_mode(mode)
    np_axis = numpy_axis(axis, cube.ndim)
    dtype = output_dtype(rsf.data)
    data = np.asarray(rsf.data, dtype=dtype)

    if operation == "sum":
        result = np.sum(data, axis=np_axis, dtype=np.complex128 if np.iscomplexobj(data) else np.float64)
    elif operation == "mean":
        result = _mean_stack(data, axis=np_axis, nonzero=nonzero)
    elif operation == "rms":
        if np.iscomplexobj(data):
            raise StackError("mode=rms requires real-valued input")
        result = _rms_stack(data, axis=np_axis, nonzero=nonzero)
    else:
        raise StackError("mode= must be mean, sum, or rms")

    output = np.asarray(result, dtype=dtype)
    if output.ndim == 0:
        output = output.reshape((1,))
    header = header_without_axis(rsf.header, axis)
    return write_rsf(output_path, np.ascontiguousarray(output), header)


def stack_along_axis(
    data: np.ndarray,
    *,
    axis: int = 1,
    statistic: str = "sum",
    nonzero: bool = False,
) -> np.ndarray:
    """Stack an in-memory array over one 1-based RSF axis."""

    array = np.asarray(data)
    if array.ndim < 1:
        raise StackError("stack_along_axis requires at least 1D input")
    axis = validate_rsf_axis(axis, array.ndim)
    np_axis = numpy_axis(axis, array.ndim)
    operation = _normalize_statistic(statistic)
    dtype = output_dtype(array)
    values = np.asarray(array, dtype=dtype)

    if operation == "sum":
        result = np.sum(values, axis=np_axis, dtype=np.complex128 if np.iscomplexobj(values) else np.float64)
    elif operation == "mean":
        result = _mean_stack(values, axis=np_axis, nonzero=nonzero)
    elif operation == "rms":
        if np.iscomplexobj(values):
            raise StackError("statistic=rms requires real-valued input")
        result = _rms_stack(values, axis=np_axis, nonzero=nonzero)
    elif operation == "count_nonzero":
        result = np.count_nonzero(values, axis=np_axis)
    else:  # pragma: no cover - guarded by _normalize_statistic.
        raise StackError("unsupported statistic")

    output = np.asarray(result, dtype=dtype)
    if output.ndim == 0:
        output = output.reshape((1,))
    return np.ascontiguousarray(output)


def stacks_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    axis: int = 1,
    statistic: str = "sum",
    nonzero: bool = False,
) -> RSFArray:
    """Stack an RSF dataset over one axis using a small statistic subset."""

    rsf = read_rsf(input_path)
    cube = Hypercube.from_header(rsf.header)
    axis = validate_rsf_axis(axis, cube.ndim)
    result = stack_along_axis(rsf.data, axis=axis, statistic=statistic, nonzero=nonzero)
    header = header_without_axis(rsf.header, axis)
    header["stack_statistic"] = _normalize_statistic(statistic)
    return write_rsf(output_path, result, header)


def _mean_stack(data: np.ndarray, *, axis: int, nonzero: bool) -> np.ndarray:
    if not nonzero:
        return np.mean(data, axis=axis)
    live = np.abs(data) != 0.0
    summed = np.sum(np.where(live, data, 0.0), axis=axis)
    fold = np.sum(live, axis=axis)
    return np.divide(summed, fold, out=np.zeros_like(summed), where=fold > 0)


def _rms_stack(data: np.ndarray, *, axis: int, nonzero: bool) -> np.ndarray:
    live = data != 0.0 if nonzero else np.ones_like(data, dtype=bool)
    power = np.sum(np.where(live, data * data, 0.0), axis=axis)
    fold = np.sum(live, axis=axis)
    return np.sqrt(np.divide(power, fold, out=np.zeros_like(power), where=fold > 0))


def _normalize_mode(mode: str) -> str:
    normalized = str(mode).strip().lower()
    aliases = {"avg": "mean", "average": "mean", "stack": "mean"}
    normalized = aliases.get(normalized, normalized)
    if normalized not in {"mean", "sum", "rms"}:
        raise StackError("mode= must be mean, sum, or rms")
    return normalized


def _normalize_statistic(statistic: str) -> str:
    normalized = str(statistic).strip().lower()
    aliases = {"avg": "mean", "average": "mean", "count": "count_nonzero", "fold": "count_nonzero"}
    normalized = aliases.get(normalized, normalized)
    if normalized not in {"mean", "sum", "rms", "count_nonzero"}:
        raise StackError("statistic= must be mean, sum, rms, or count_nonzero")
    return normalized
