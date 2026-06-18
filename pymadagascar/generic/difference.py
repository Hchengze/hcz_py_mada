"""Small whole-dataset difference metrics for RSF quality control."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import numpy as np

from pymadagascar.io.rsf import RSFArray, RSFHeader, read_rsf, write_rsf


DifferenceMetric = Literal["sum_square", "rms", "max_abs"]


class DifferenceError(ValueError):
    """Raised when two datasets cannot be compared."""


def difference_metric(
    data: Any,
    match: Any,
    *,
    metric: DifferenceMetric = "sum_square",
) -> float:
    """Return a scalar difference metric for two same-shape numeric arrays."""

    left = np.asarray(data)
    right = np.asarray(match)
    if left.shape != right.shape:
        raise DifferenceError(f"shape mismatch: {left.shape} != {right.shape}")
    if left.size == 0:
        raise DifferenceError("difference metric requires non-empty input")
    if not np.issubdtype(left.dtype, np.number) or not np.issubdtype(right.dtype, np.number):
        raise DifferenceError("difference metric requires numeric input")

    normalized = _normalize_metric(metric)
    delta = np.asarray(left, dtype=np.complex128 if np.iscomplexobj(left) or np.iscomplexobj(right) else np.float64)
    delta = delta - np.asarray(right, dtype=delta.dtype)
    amplitudes = np.abs(delta)
    if normalized == "sum_square":
        return float(np.sum(amplitudes * amplitudes, dtype=np.float64))
    if normalized == "rms":
        return float(np.sqrt(np.mean(amplitudes * amplitudes, dtype=np.float64)))
    return float(np.max(amplitudes))


def diff_rsf(
    input_path: str | Path,
    match_path: str | Path,
    output_path: str | Path,
    *,
    metric: DifferenceMetric = "sum_square",
) -> RSFArray:
    """Compare two RSF datasets and write a one-sample metric RSF."""

    left = read_rsf(input_path)
    right = read_rsf(match_path)
    value = difference_metric(left.data, right.data, metric=metric)
    normalized = _normalize_metric(metric)
    header = RSFHeader(
        {
            "n1": 1,
            "o1": 0.0,
            "d1": 1.0,
            "label1": "Difference",
            "difference_metric": normalized,
        }
    )
    return write_rsf(output_path, np.asarray([value], dtype=np.float64), header)


def _normalize_metric(value: str) -> DifferenceMetric:
    normalized = str(value).strip().lower()
    aliases = {"sumsq": "sum_square", "l2": "sum_square", "max": "max_abs"}
    normalized = aliases.get(normalized, normalized)
    if normalized not in {"sum_square", "rms", "max_abs"}:
        raise DifferenceError("metric= must be sum_square, rms, or max_abs")
    return normalized  # type: ignore[return-value]


__all__ = ["DifferenceError", "difference_metric", "diff_rsf"]
