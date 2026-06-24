"""Otsu histogram threshold aligned with ``system/generic/Motsu.c``."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from pymadagascar.io.rsf import read_rsf


class OtsuError(ValueError):
    """Raised when Otsu threshold input is invalid."""


def otsu_threshold(
    histogram: Any,
    *,
    o1: float = 0.0,
    d1: float = 1.0,
) -> float:
    """Return the Otsu threshold for a one-dimensional integer histogram."""

    hist = np.asarray(histogram)
    if hist.ndim != 1:
        raise OtsuError("otsu_threshold expects a 1D histogram")
    if not np.issubdtype(hist.dtype, np.integer):
        raise OtsuError("otsu_threshold requires integer histogram samples")
    if np.any(hist < 0):
        raise OtsuError("histogram counts must be nonnegative")
    counts = hist.astype(np.int64, copy=False)
    total = int(np.sum(counts))
    if total <= 0:
        raise OtsuError("histogram must contain at least one sample")

    indices = np.arange(counts.size, dtype=np.int64)
    total_weighted = int(np.sum(indices * counts))
    weight1 = 0
    sum1 = 0
    threshold_index = 0
    max_variance = -1.0

    for index, count in enumerate(counts):
        weight1 += int(count)
        if weight1 == 0:
            continue
        weight2 = total - weight1
        if weight2 == 0:
            break
        sum1 += index * int(count)
        mean1 = float(sum1) / float(weight1)
        mean2 = float(total_weighted - sum1) / float(weight2)
        variance = float(weight1 * weight2) * (mean1 - mean2) * (mean1 - mean2)
        if variance > max_variance:
            max_variance = variance
            threshold_index = index

    return float(o1) + (float(threshold_index) + 0.5) * float(d1)


def otsu_rsf(input_path: str | Path) -> float:
    """Read an integer histogram RSF and return its Otsu threshold."""

    rsf = read_rsf(input_path)
    data = np.asarray(rsf.data)
    if data.ndim != 1:
        raise OtsuError("sfotsu expects a 1D histogram RSF input")
    o1 = float(rsf.header.get("o1", 0.0))
    d1 = float(rsf.header.get("d1", 1.0))
    return otsu_threshold(data, o1=o1, d1=d1)


__all__ = ["OtsuError", "otsu_rsf", "otsu_threshold"]
