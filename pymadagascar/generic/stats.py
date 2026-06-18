"""Min/max statistics for RSF arrays."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import warnings

import numpy as np

from pymadagascar.core.hypercube import Hypercube
from pymadagascar.io.rsf import read_rsf


class StatError(ValueError):
    """Raised when an RSF statistic request is unsupported."""


@dataclass(frozen=True)
class StatResult:
    """Result from a min/max statistic."""

    name: str
    value: float | np.ndarray
    index: tuple[int, ...] | None
    axis: int | None
    shape: tuple[int, ...]
    dtype: np.dtype
    nan_policy: str


def min_rsf(
    path: str | Path,
    *,
    axis: int | None = None,
    nan_policy: str = "propagate",
    complex_policy: str = "reject",
) -> StatResult:
    """Return the minimum of an RSF dataset."""

    return minmax_rsf(
        path,
        kind="min",
        axis=axis,
        nan_policy=nan_policy,
        complex_policy=complex_policy,
    )


def max_rsf(
    path: str | Path,
    *,
    axis: int | None = None,
    nan_policy: str = "propagate",
    complex_policy: str = "reject",
) -> StatResult:
    """Return the maximum of an RSF dataset."""

    return minmax_rsf(
        path,
        kind="max",
        axis=axis,
        nan_policy=nan_policy,
        complex_policy=complex_policy,
    )


def minmax_rsf(
    path: str | Path,
    *,
    kind: str = "min",
    axis: int | None = None,
    nan_policy: str = "propagate",
    complex_policy: str = "reject",
) -> StatResult:
    """Return a global or axis-wise min/max statistic for an RSF dataset.

    ``axis`` uses 1-based RSF axis numbering. With ``axis=None`` or ``axis=0``
    the result is global and includes a 0-based NumPy index for scalar data.
    Complex input is rejected by default; pass ``complex_policy="abs"`` to
    compute statistics on magnitudes.
    """

    operation = _normalize_kind(kind)
    nan_policy = _normalize_nan_policy(nan_policy)
    rsf = read_rsf(path)
    data = np.asarray(rsf.data)
    work = _normalize_complex(data, complex_policy=complex_policy)

    if work.dtype.kind not in {"f", "i", "u"}:
        raise StatError("min/max statistics support real float or integer RSF data")

    if axis == 0:
        axis = None

    if axis is None:
        value, index = _global_stat(work, operation, nan_policy)
    else:
        cube = Hypercube.from_header(rsf.header)
        axis = _validate_axis(axis, cube.ndim)
        value = _axis_stat(work, operation, nan_policy, _numpy_axis(axis, cube.ndim))
        index = None

    return StatResult(
        name=operation,
        value=value,
        index=index,
        axis=axis,
        shape=data.shape,
        dtype=data.dtype,
        nan_policy=nan_policy,
    )


def format_stat(result: StatResult) -> str:
    """Format ``StatResult`` as deterministic key=value CLI text."""

    lines = [
        f"stat={result.name}",
        f"axis={'global' if result.axis is None else result.axis}",
        f"dtype={result.dtype}",
        f"nan_policy={result.nan_policy}",
    ]
    value = result.value
    if np.ndim(value) == 0:
        lines.append(f"value={_format_number(float(value))}")
        if result.index is not None:
            lines.append("index=" + ",".join(str(item) for item in result.index))
    else:
        array = np.asarray(value)
        lines.append("shape=" + "x".join(str(size) for size in array.shape))
        values = ",".join(_format_number(float(item)) for item in array.ravel())
        lines.append(f"values={values}")
    return "\n".join(lines)


def _global_stat(
    data: np.ndarray,
    kind: str,
    nan_policy: str,
) -> tuple[float, tuple[int, ...] | None]:
    if nan_policy == "omit":
        valid = ~np.isnan(data)
        if not np.any(valid):
            return float("nan"), None
        fill = np.inf if kind == "min" else -np.inf
        work = np.where(valid, data, fill)
    else:
        work = data

    if kind == "min":
        value = np.min(work)
        flat_index = int(np.argmin(work))
    else:
        value = np.max(work)
        flat_index = int(np.argmax(work))
    index = tuple(int(item) for item in np.unravel_index(flat_index, work.shape))
    return float(value), index


def _axis_stat(data: np.ndarray, kind: str, nan_policy: str, np_axis: int) -> np.ndarray:
    if kind == "min":
        reducer = np.nanmin if nan_policy == "omit" else np.min
    else:
        reducer = np.nanmax if nan_policy == "omit" else np.max

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        return np.asarray(reducer(data, axis=np_axis))


def _normalize_kind(kind: str) -> str:
    normalized = str(kind).strip().lower()
    if normalized not in {"min", "max"}:
        raise StatError("kind must be 'min' or 'max'")
    return normalized


def _normalize_nan_policy(policy: str) -> str:
    normalized = str(policy).strip().lower()
    if normalized not in {"propagate", "omit"}:
        raise StatError("nan_policy must be 'propagate' or 'omit'")
    return normalized


def _normalize_complex(data: np.ndarray, *, complex_policy: str) -> np.ndarray:
    normalized = str(complex_policy).strip().lower()
    if np.iscomplexobj(data):
        if normalized == "reject":
            raise StatError("complex input is unsupported; pass complex_policy=abs to use magnitudes")
        if normalized == "abs":
            return np.abs(data)
        raise StatError("complex_policy must be 'reject' or 'abs'")
    if normalized not in {"reject", "abs"}:
        raise StatError("complex_policy must be 'reject' or 'abs'")
    return data


def _validate_axis(axis: int, ndim: int) -> int:
    value = int(axis)
    if value < 1 or value > ndim:
        raise StatError(f"axis must be between 1 and {ndim}, got {axis}")
    return value


def _numpy_axis(axis: int, ndim: int) -> int:
    return ndim - axis


def _format_number(value: float) -> str:
    return f"{value:.9g}"
