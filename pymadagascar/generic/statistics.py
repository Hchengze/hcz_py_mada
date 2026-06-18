"""Small-data robust statistics and non-finite sample handling."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal
import warnings

import numpy as np

from pymadagascar.core.axis import Axis
from pymadagascar.core.hypercube import Hypercube
from pymadagascar.io.rsf import RSFArray, RSFHeader, read_rsf, write_rsf


NanPolicy = Literal["propagate", "omit", "raise"]
MaskMode = Literal["nan", "inf", "nonfinite", "finite"]
FillMode = Literal["nan", "inf", "nonfinite"]


class StatisticsError(ValueError):
    """Raised when a statistics or non-finite handling request is invalid."""


def mean(
    data: Any,
    axis: int | None = None,
    nan_policy: NanPolicy = "propagate",
) -> np.ndarray:
    """Return a global or axis-wise arithmetic mean as float64."""

    return _reduce(data, "mean", axis=axis, nan_policy=nan_policy)


def rms(
    data: Any,
    axis: int | None = None,
    nan_policy: NanPolicy = "propagate",
) -> np.ndarray:
    """Return ``sqrt(mean(x**2))`` globally or along one RSF axis."""

    return _reduce(data, "rms", axis=axis, nan_policy=nan_policy)


def variance(
    data: Any,
    axis: int | None = None,
    *,
    ddof: int = 0,
    nan_policy: NanPolicy = "propagate",
) -> np.ndarray:
    """Return global or axis-wise variance as float64."""

    return _reduce(data, "var", axis=axis, nan_policy=nan_policy, ddof=ddof)


def std(
    data: Any,
    axis: int | None = None,
    *,
    ddof: int = 0,
    nan_policy: NanPolicy = "propagate",
) -> np.ndarray:
    """Return global or axis-wise standard deviation as float64."""

    return _reduce(data, "std", axis=axis, nan_policy=nan_policy, ddof=ddof)


def median(
    data: Any,
    axis: int | None = None,
    nan_policy: NanPolicy = "propagate",
) -> np.ndarray:
    """Return a global or axis-wise median as float64."""

    return _reduce(data, "median", axis=axis, nan_policy=nan_policy)


def range_stats(
    data: Any,
    axis: int | None = None,
    nan_policy: NanPolicy = "propagate",
) -> np.ndarray:
    """Return min/max pairs globally or along one RSF axis.

    Global output has shape ``(2,)``. Axis-wise output removes the selected
    source axis and appends a two-sample NumPy field axis, which is RSF axis 1.
    """

    array = _coerce_real_array(data, operation="range")
    policy = _normalize_nan_policy(nan_policy)
    numpy_axis = _numpy_axis(axis, array.ndim)
    _raise_for_nan(array, policy)
    working = array.astype(np.float64, copy=False)
    minimum = _call_reducer(working, "min", numpy_axis, policy)
    maximum = _call_reducer(working, "max", numpy_axis, policy)
    if numpy_axis is None:
        result = np.asarray([minimum, maximum], dtype=np.float64)
    else:
        result = np.stack((minimum, maximum), axis=-1).astype(np.float64, copy=False)
    return np.ascontiguousarray(result)


def stat_rsf(
    input_path: str | Path,
    output_path: str | Path,
    stat: str,
    *,
    axis: int | None = None,
    nan_policy: NanPolicy = "propagate",
    ddof: int = 0,
) -> RSFArray:
    """Write a global or axis-wise statistic to a new RSF dataset."""

    normalized = str(stat).strip().lower()
    operations = {
        "mean": mean,
        "rms": rms,
        "var": variance,
        "variance": variance,
        "std": std,
        "median": median,
        "range": range_stats,
    }
    operation = operations.get(normalized)
    if operation is None:
        raise StatisticsError("stat must be mean, rms, var, std, median, or range")

    rsf = read_rsf(input_path)
    kwargs: dict[str, Any] = {"axis": axis, "nan_policy": nan_policy}
    if normalized in {"var", "variance", "std"}:
        kwargs["ddof"] = ddof
    result = operation(rsf.data, **kwargs)
    header = _stat_header(
        rsf.header,
        stat="var" if normalized == "variance" else normalized,
        axis=axis,
        nan_policy=nan_policy,
        ddof=ddof,
    )
    return write_rsf(output_path, result, header)


def mean_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    axis: int | None = None,
    nan_policy: NanPolicy = "propagate",
) -> RSFArray:
    """Write a global or axis-wise arithmetic mean."""

    return stat_rsf(input_path, output_path, "mean", axis=axis, nan_policy=nan_policy)


def rms_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    axis: int | None = None,
    nan_policy: NanPolicy = "propagate",
) -> RSFArray:
    """Write a global or axis-wise RMS statistic."""

    return stat_rsf(input_path, output_path, "rms", axis=axis, nan_policy=nan_policy)


def var_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    axis: int | None = None,
    ddof: int = 0,
    nan_policy: NanPolicy = "propagate",
) -> RSFArray:
    """Write a global or axis-wise variance."""

    return stat_rsf(
        input_path,
        output_path,
        "var",
        axis=axis,
        nan_policy=nan_policy,
        ddof=ddof,
    )


def std_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    axis: int | None = None,
    ddof: int = 0,
    nan_policy: NanPolicy = "propagate",
) -> RSFArray:
    """Write a global or axis-wise standard deviation."""

    return stat_rsf(
        input_path,
        output_path,
        "std",
        axis=axis,
        nan_policy=nan_policy,
        ddof=ddof,
    )


def median_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    axis: int | None = None,
    nan_policy: NanPolicy = "propagate",
) -> RSFArray:
    """Write a global or axis-wise median."""

    return stat_rsf(input_path, output_path, "median", axis=axis, nan_policy=nan_policy)


def range_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    axis: int | None = None,
    nan_policy: NanPolicy = "propagate",
) -> RSFArray:
    """Write min/max pairs globally or along one RSF axis."""

    return stat_rsf(input_path, output_path, "range", axis=axis, nan_policy=nan_policy)


def isnan_mask(data: Any, mode: MaskMode = "nan") -> np.ndarray:
    """Return a boolean mask for NaN, Inf, non-finite, or finite samples."""

    array = _coerce_numeric_array(data)
    normalized = _normalize_mask_mode(mode)
    if normalized == "nan":
        mask = np.isnan(array)
    elif normalized == "inf":
        mask = np.isinf(array)
    elif normalized == "nonfinite":
        mask = ~np.isfinite(array)
    else:
        mask = np.isfinite(array)
    return np.ascontiguousarray(mask, dtype=np.bool_)


def finite_mask(data: Any) -> np.ndarray:
    """Return a boolean mask whose true samples are finite."""

    return isnan_mask(data, mode="finite")


def fillnan(
    data: Any,
    value: float | complex = 0.0,
    mode: FillMode = "nan",
) -> np.ndarray:
    """Replace selected non-finite samples while preserving input dtype."""

    array = _coerce_numeric_array(data)
    normalized = _normalize_fill_mode(mode)
    replacement = complex(value) if np.iscomplexobj(array) else _real_replacement(value)
    mask = isnan_mask(array, mode=normalized)
    result = np.array(array, copy=True)
    result[mask] = replacement
    return np.ascontiguousarray(result)


def isnan_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    mode: MaskMode = "nan",
    dtype: str = "int32",
) -> RSFArray:
    """Write a shape-preserving 0/1 non-finite mask."""

    if str(dtype).strip().lower() not in {"int32", "int"}:
        raise StatisticsError("RSF mask dtype must be int32")
    rsf = read_rsf(input_path)
    normalized = _normalize_mask_mode(mode)
    result = isnan_mask(rsf.data, mode=normalized).astype(np.int32)
    header = rsf.header.copy()
    header["mask_mode"] = normalized
    header["label"] = f"{normalized} mask"
    return write_rsf(output_path, result, header)


def fillnan_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    value: float | complex = 0.0,
    mode: FillMode = "nan",
) -> RSFArray:
    """Write a shape-preserving dataset with selected non-finite samples replaced."""

    rsf = read_rsf(input_path)
    normalized = _normalize_fill_mode(mode)
    result = fillnan(rsf.data, value=value, mode=normalized)
    header = rsf.header.copy()
    header["fill_mode"] = normalized
    header["fill_value"] = value
    return write_rsf(output_path, result, header)


def _reduce(
    data: Any,
    stat: str,
    *,
    axis: int | None,
    nan_policy: NanPolicy,
    ddof: int = 0,
) -> np.ndarray:
    array = _coerce_real_array(data, operation=stat)
    policy = _normalize_nan_policy(nan_policy)
    numpy_axis = _numpy_axis(axis, array.ndim)
    ddof = _normalize_ddof(ddof)
    _raise_for_nan(array, policy)
    working = array.astype(np.float64, copy=False)

    if stat == "rms":
        squared = np.square(working)
        result = _call_reducer(squared, "mean", numpy_axis, policy)
        result = np.sqrt(result)
    else:
        result = _call_reducer(working, stat, numpy_axis, policy, ddof=ddof)
    return _as_stat_array(result)


def _call_reducer(
    array: np.ndarray,
    stat: str,
    axis: int | None,
    nan_policy: NanPolicy,
    *,
    ddof: int = 0,
) -> np.ndarray | np.generic | float:
    prefix = "nan" if nan_policy == "omit" else ""
    reducer = getattr(np, prefix + stat)
    kwargs: dict[str, Any] = {"axis": axis}
    if stat in {"var", "std"}:
        kwargs["ddof"] = ddof
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        return reducer(array, **kwargs)


def _as_stat_array(result: Any) -> np.ndarray:
    array = np.asarray(result, dtype=np.float64)
    if array.ndim == 0:
        array = array.reshape(1)
    return np.ascontiguousarray(array)


def _coerce_numeric_array(data: Any) -> np.ndarray:
    array = np.asarray(data)
    if array.ndim < 1:
        raise StatisticsError("input must have at least one dimension")
    if array.size == 0:
        raise StatisticsError("input must contain at least one sample")
    if array.dtype.kind not in {"f", "i", "u", "c"}:
        raise StatisticsError("input must contain numeric samples")
    return array


def _coerce_real_array(data: Any, *, operation: str) -> np.ndarray:
    array = _coerce_numeric_array(data)
    if np.iscomplexobj(array):
        raise StatisticsError(f"{operation} does not support complex input")
    return array


def _numpy_axis(axis: int | None, ndim: int) -> int | None:
    if axis in {None, 0}:
        return None
    rsf_axis = int(axis)
    if rsf_axis < 1 or rsf_axis > ndim:
        raise StatisticsError(f"axis must be between 1 and {ndim}, got {rsf_axis}")
    return ndim - rsf_axis


def _normalize_nan_policy(value: str) -> NanPolicy:
    normalized = str(value).strip().lower()
    if normalized not in {"propagate", "omit", "raise"}:
        raise StatisticsError("nan_policy must be propagate, omit, or raise")
    return normalized  # type: ignore[return-value]


def _normalize_ddof(value: int) -> int:
    ddof = int(value)
    if ddof < 0:
        raise StatisticsError("ddof must be non-negative")
    return ddof


def _raise_for_nan(array: np.ndarray, policy: NanPolicy) -> None:
    if policy == "raise" and bool(np.any(np.isnan(array))):
        raise StatisticsError("input contains NaN samples")


def _normalize_mask_mode(value: str) -> MaskMode:
    normalized = str(value).strip().lower()
    if normalized not in {"nan", "inf", "nonfinite", "finite"}:
        raise StatisticsError("mode must be nan, inf, nonfinite, or finite")
    return normalized  # type: ignore[return-value]


def _normalize_fill_mode(value: str) -> FillMode:
    normalized = str(value).strip().lower()
    if normalized not in {"nan", "inf", "nonfinite"}:
        raise StatisticsError("mode must be nan, inf, or nonfinite")
    return normalized  # type: ignore[return-value]


def _real_replacement(value: float | complex) -> float:
    converted = complex(value)
    if converted.imag != 0.0:
        raise StatisticsError("complex fill value requires complex input")
    return float(converted.real)


def _stat_header(
    source: RSFHeader,
    *,
    stat: str,
    axis: int | None,
    nan_policy: NanPolicy,
    ddof: int,
) -> RSFHeader:
    cube = Hypercube.from_header(source)
    label = {
        "mean": "Mean",
        "rms": "RMS",
        "var": "Variance",
        "std": "Standard deviation",
        "median": "Median",
        "range": "Range field",
    }[stat]

    if stat == "range":
        remaining = [] if axis in {None, 0} else _remaining_axes(cube, int(axis))
        header = Hypercube([Axis(n=2, label=label), *remaining]).to_header(source)
        header["range_fields"] = "min,max"
    elif axis in {None, 0}:
        header = Hypercube([Axis(n=1, label=label)]).to_header(source)
    else:
        remaining = _remaining_axes(cube, int(axis))
        axes = remaining or [Axis(n=1, label=label)]
        header = Hypercube(axes).to_header(source)

    header["statistic"] = stat
    header["statistic_axis"] = "global" if axis in {None, 0} else int(axis)
    header["nan_policy"] = nan_policy
    if stat in {"var", "std"}:
        header["ddof"] = ddof
    return header


def _remaining_axes(cube: Hypercube, axis: int) -> list[Axis]:
    if axis < 1 or axis > cube.ndim:
        raise StatisticsError(f"axis must be between 1 and {cube.ndim}, got {axis}")
    return [item for index, item in enumerate(cube.axes, start=1) if index != axis]


__all__ = [
    "StatisticsError",
    "fillnan",
    "fillnan_rsf",
    "finite_mask",
    "isnan_mask",
    "isnan_rsf",
    "mean",
    "mean_rsf",
    "median",
    "median_rsf",
    "range_rsf",
    "range_stats",
    "rms",
    "rms_rsf",
    "stat_rsf",
    "std",
    "std_rsf",
    "var_rsf",
    "variance",
]
