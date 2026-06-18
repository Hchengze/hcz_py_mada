"""Small-data unary transforms and distribution quality-control helpers."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any, Literal
import warnings

import numpy as np

from pymadagascar.core.hypercube import Hypercube
from pymadagascar.io.rsf import RSFArray, RSFHeader, read_rsf, write_rsf


InvalidPolicy = Literal["nan", "raise"]
NanPolicy = Literal["propagate", "omit"]


class UnaryMathError(ValueError):
    """Raised when a unary transform or distribution request is invalid."""


def absolute(data: Any) -> np.ndarray:
    """Return sample magnitudes, including real magnitudes for complex input."""

    array = _coerce_numeric_array(data)
    result = np.abs(array)
    return np.ascontiguousarray(result.astype(_real_output_dtype(array), copy=False))


def sign(data: Any) -> np.ndarray:
    """Return -1, 0, or 1 for real samples."""

    array = _coerce_real_array(data, operation="sign")
    result = np.sign(array)
    return np.ascontiguousarray(result.astype(_real_output_dtype(array), copy=False))


def sqrt(data: Any, *, invalid: InvalidPolicy = "nan") -> np.ndarray:
    """Return the real square root with configurable negative-input handling."""

    array = _coerce_real_array(data, operation="sqrt")
    policy = _normalize_invalid(invalid)
    _raise_if_invalid(array < 0.0, policy, "sqrt input contains negative samples")
    with np.errstate(invalid="ignore"):
        result = np.sqrt(array.astype(_real_output_dtype(array), copy=False))
    return np.ascontiguousarray(result)


def log(
    data: Any,
    *,
    base: str | float = "e",
    invalid: InvalidPolicy = "nan",
) -> np.ndarray:
    """Return a real logarithm; zero maps to ``-inf`` and negatives are invalid."""

    array = _coerce_real_array(data, operation="log")
    policy = _normalize_invalid(invalid)
    _raise_if_invalid(array < 0.0, policy, "log input contains negative samples")
    denominator = _log_base_denominator(base)
    with np.errstate(divide="ignore", invalid="ignore"):
        result = np.log(array.astype(_real_output_dtype(array), copy=False))
        if denominator != 1.0:
            result = result / denominator
    return np.ascontiguousarray(result.astype(_real_output_dtype(array), copy=False))


def exp(data: Any) -> np.ndarray:
    """Return the real exponential, allowing NumPy overflow to ``inf``."""

    array = _coerce_real_array(data, operation="exp")
    with np.errstate(over="ignore", invalid="ignore"):
        result = np.exp(array.astype(_real_output_dtype(array), copy=False))
    return np.ascontiguousarray(result)


def power(data: Any, exponent: float) -> np.ndarray:
    """Raise real samples to a scalar exponent using NumPy real-domain rules."""

    array = _coerce_real_array(data, operation="power")
    exponent = float(exponent)
    if not np.isfinite(exponent):
        raise UnaryMathError("exponent must be finite")
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        result = np.power(
            array.astype(_real_output_dtype(array), copy=False),
            exponent,
        )
    return np.ascontiguousarray(result.astype(_real_output_dtype(array), copy=False))


def histogram(
    data: Any,
    bins: int = 10,
    range: tuple[float, float] | None = None,
    density: bool = False,
) -> np.ndarray:
    """Return a ``(bins, 2)`` table of bin centers and count/density values.

    Non-finite samples are omitted. Complex input is rejected.
    """

    array = _coerce_real_array(data, operation="histogram")
    bins = _normalize_bins(bins)
    finite = np.asarray(array, dtype=np.float64).ravel()
    finite = finite[np.isfinite(finite)]
    if finite.size == 0:
        raise UnaryMathError("histogram requires at least one finite sample")
    value_range = _normalize_range(range, finite)
    counts, edges = np.histogram(finite, bins=bins, range=value_range, density=bool(density))
    centers = 0.5 * (edges[:-1] + edges[1:])
    return np.ascontiguousarray(np.column_stack((centers, counts)), dtype=np.float64)


def quantile(
    data: Any,
    q: float | Sequence[float],
    axis: int | None = None,
    *,
    nan_policy: NanPolicy = "propagate",
) -> np.ndarray:
    """Return quantiles globally or along one 1-based RSF axis.

    Global output is always one-dimensional. Axis-wise output replaces the
    selected axis with a quantile axis, including for a single quantile.
    """

    array = _coerce_real_array(data, operation="quantile")
    quantiles = _normalize_quantiles(q)
    policy = _normalize_nan_policy(nan_policy)
    reducer = np.nanquantile if policy == "omit" else np.quantile

    if axis in {None, 0}:
        numpy_axis = None
    else:
        rsf_axis = _validate_axis(int(axis), array.ndim)
        numpy_axis = array.ndim - rsf_axis

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        result = np.asarray(reducer(array, quantiles, axis=numpy_axis), dtype=np.float64)
    if numpy_axis is None:
        return np.ascontiguousarray(result.reshape(quantiles.size))
    return np.ascontiguousarray(np.moveaxis(result, 0, numpy_axis))


def unary_rsf(
    input_path: str | Path,
    output_path: str | Path,
    op: str,
    **kwargs: Any,
) -> RSFArray:
    """Apply one supported unary operation while preserving ordinary metadata."""

    operations = {
        "abs": absolute,
        "absolute": absolute,
        "sign": sign,
        "sqrt": sqrt,
        "log": log,
        "exp": exp,
        "pow": power,
        "power": power,
    }
    normalized = str(op).strip().lower()
    operation = operations.get(normalized)
    if operation is None:
        raise UnaryMathError("op must be abs, sign, sqrt, log, exp, or pow")
    rsf = read_rsf(input_path)
    result = operation(rsf.data, **kwargs)
    return write_rsf(output_path, result, rsf.header.copy())


def abs_rsf(input_path: str | Path, output_path: str | Path) -> RSFArray:
    """Write sample magnitudes to a new RSF file."""

    return unary_rsf(input_path, output_path, "abs")


def sign_rsf(input_path: str | Path, output_path: str | Path) -> RSFArray:
    """Write real sample signs to a new RSF file."""

    return unary_rsf(input_path, output_path, "sign")


def sqrt_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    invalid: InvalidPolicy = "nan",
) -> RSFArray:
    """Write real square roots to a new RSF file."""

    return unary_rsf(input_path, output_path, "sqrt", invalid=invalid)


def log_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    base: str | float = "e",
    invalid: InvalidPolicy = "nan",
) -> RSFArray:
    """Write real logarithms to a new RSF file."""

    return unary_rsf(input_path, output_path, "log", base=base, invalid=invalid)


def exp_rsf(input_path: str | Path, output_path: str | Path) -> RSFArray:
    """Write real exponentials to a new RSF file."""

    return unary_rsf(input_path, output_path, "exp")


def pow_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    exponent: float,
) -> RSFArray:
    """Write a scalar sample-wise power transform to a new RSF file."""

    return unary_rsf(input_path, output_path, "pow", exponent=exponent)


def histogram_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    bins: int = 10,
    min_value: float | None = None,
    max_value: float | None = None,
    density: bool = False,
) -> RSFArray:
    """Write a two-column bin-center/count-or-density histogram table."""

    rsf = read_rsf(input_path)
    value_range = _range_from_limits(min_value, max_value, rsf.data)
    result = histogram(rsf.data, bins=bins, range=value_range, density=density)
    bin_width = float(result[1, 0] - result[0, 0]) if result.shape[0] > 1 else 1.0
    header = RSFHeader(
        {
            "n1": 2,
            "o1": 0.0,
            "d1": 1.0,
            "label1": "Histogram field",
            "n2": result.shape[0],
            "o2": float(result[0, 0]),
            "d2": bin_width,
            "label2": "Bin center",
            "histogram_fields": "center,value",
            "histogram_value": "density" if density else "count",
            "source_label": rsf.header.get("label", ""),
            "source_unit": rsf.header.get("unit", ""),
        }
    )
    return write_rsf(output_path, result, header)


def quantile_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    q: float | Sequence[float],
    axis: int | None = None,
    nan_policy: NanPolicy = "propagate",
) -> RSFArray:
    """Write global or axis-wise quantiles with an explicit quantile axis."""

    rsf = read_rsf(input_path)
    quantiles = _normalize_quantiles(q)
    result = quantile(rsf.data, quantiles, axis=axis, nan_policy=nan_policy)
    quantile_header = _quantile_axis_metadata(quantiles)

    if axis in {None, 0}:
        header = RSFHeader(
            {
                "n1": quantiles.size,
                **quantile_header,
                "quantiles": _format_quantiles(quantiles),
                "quantile_source": "global",
                "nan_policy": nan_policy,
            }
        )
    else:
        cube = Hypercube.from_header(rsf.header)
        rsf_axis = _validate_axis(int(axis), cube.ndim)
        header = cube.update_axis(
            rsf_axis,
            n=quantiles.size,
            o=quantile_header["o1"],
            d=quantile_header["d1"],
            label=quantile_header["label1"],
            unit=None,
        ).to_header(rsf.header)
        header["quantiles"] = _format_quantiles(quantiles)
        header["quantile_axis"] = rsf_axis
        header["nan_policy"] = nan_policy
    return write_rsf(output_path, result, header)


def _coerce_numeric_array(data: Any) -> np.ndarray:
    array = np.asarray(data)
    if array.ndim < 1:
        raise UnaryMathError("input must have at least one dimension")
    if array.dtype.kind not in {"f", "i", "u", "c"}:
        raise UnaryMathError("input must contain numeric samples")
    return array


def _coerce_real_array(data: Any, *, operation: str) -> np.ndarray:
    array = _coerce_numeric_array(data)
    if np.iscomplexobj(array):
        raise UnaryMathError(f"{operation} does not support complex input")
    return array


def _real_output_dtype(data: np.ndarray) -> np.dtype[Any]:
    dtype = np.asarray(data).dtype
    if dtype in {np.dtype("float64"), np.dtype("complex128")}:
        return np.dtype("float64")
    return np.dtype("float32")


def _normalize_invalid(value: str) -> InvalidPolicy:
    normalized = str(value).strip().lower()
    if normalized not in {"nan", "raise"}:
        raise UnaryMathError("invalid must be 'nan' or 'raise'")
    return normalized  # type: ignore[return-value]


def _raise_if_invalid(mask: np.ndarray, policy: InvalidPolicy, message: str) -> None:
    if policy == "raise" and bool(np.any(mask)):
        raise UnaryMathError(message)


def _log_base_denominator(base: str | float) -> float:
    if isinstance(base, str) and base.strip().lower() in {"e", "natural"}:
        return 1.0
    try:
        value = float(base)
    except (TypeError, ValueError) as exc:
        raise UnaryMathError("base must be e or a positive number other than 1") from exc
    if not np.isfinite(value) or value <= 0.0 or value == 1.0:
        raise UnaryMathError("base must be e or a positive number other than 1")
    return float(np.log(value))


def _normalize_bins(value: int) -> int:
    bins = int(value)
    if bins < 1:
        raise UnaryMathError("bins must be positive")
    return bins


def _normalize_range(
    value: tuple[float, float] | None,
    finite: np.ndarray,
) -> tuple[float, float]:
    if value is None:
        lower = float(np.min(finite))
        upper = float(np.max(finite))
        if lower == upper:
            delta = max(abs(lower) * 0.5, 0.5)
            return lower - delta, upper + delta
        return lower, upper
    if len(value) != 2:
        raise UnaryMathError("histogram range must contain two values")
    lower, upper = float(value[0]), float(value[1])
    if not np.isfinite(lower) or not np.isfinite(upper) or lower >= upper:
        raise UnaryMathError("histogram range must be finite with min < max")
    return lower, upper


def _range_from_limits(
    min_value: float | None,
    max_value: float | None,
    data: np.ndarray,
) -> tuple[float, float] | None:
    if min_value is None and max_value is None:
        return None
    finite = np.asarray(data)
    if np.iscomplexobj(finite):
        raise UnaryMathError("histogram does not support complex input")
    finite = finite[np.isfinite(finite)]
    if finite.size == 0:
        raise UnaryMathError("histogram requires at least one finite sample")
    lower = float(np.min(finite)) if min_value is None else float(min_value)
    upper = float(np.max(finite)) if max_value is None else float(max_value)
    return _normalize_range((lower, upper), finite)


def _normalize_quantiles(q: float | Sequence[float]) -> np.ndarray:
    if np.isscalar(q):
        result = np.asarray([q], dtype=np.float64)
    else:
        result = np.asarray(list(q), dtype=np.float64)
    if result.ndim != 1 or result.size == 0:
        raise UnaryMathError("q must contain one or more quantiles")
    if np.any(~np.isfinite(result)) or np.any((result < 0.0) | (result > 1.0)):
        raise UnaryMathError("q values must be finite and between 0 and 1")
    return result


def _normalize_nan_policy(value: str) -> NanPolicy:
    normalized = str(value).strip().lower()
    if normalized not in {"propagate", "omit"}:
        raise UnaryMathError("nan_policy must be 'propagate' or 'omit'")
    return normalized  # type: ignore[return-value]


def _validate_axis(axis: int, ndim: int) -> int:
    if axis < 1 or axis > ndim:
        raise UnaryMathError(f"axis must be between 1 and {ndim}, got {axis}")
    return axis


def _quantile_axis_metadata(quantiles: np.ndarray) -> dict[str, float | str]:
    if quantiles.size == 1:
        return {"o1": float(quantiles[0]), "d1": 1.0, "label1": "Quantile"}
    differences = np.diff(quantiles)
    if np.allclose(differences, differences[0]):
        return {
            "o1": float(quantiles[0]),
            "d1": float(differences[0]),
            "label1": "Quantile",
        }
    return {"o1": 0.0, "d1": 1.0, "label1": "Quantile index"}


def _format_quantiles(quantiles: np.ndarray) -> str:
    return ",".join(f"{float(value):.9g}" for value in quantiles)
