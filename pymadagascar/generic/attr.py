"""RSF data attribute statistics."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from pymadagascar.io.rsf import read_rsf


def attr_rsf(path: str | Path) -> dict[str, Any]:
    """Return basic statistics for an RSF binary payload."""

    rsf = read_rsf(path)
    data = np.asarray(rsf.data)
    values = np.abs(data) if np.iscomplexobj(data) else data
    values = np.asarray(values, dtype=np.float64)
    nan_mask = np.isnan(values)
    valid = values[~nan_mask]
    total = int(values.size)
    nan_count = int(np.count_nonzero(nan_mask))
    nonzero_count = int(np.count_nonzero(values[~nan_mask]))

    if valid.size:
        min_value = float(np.min(valid))
        max_value = float(np.max(valid))
        mean = float(np.mean(valid))
        rms = float(np.sqrt(np.mean(valid * valid)))
        variance = float(np.var(valid, ddof=1)) if valid.size > 1 else 0.0
    else:
        min_value = max_value = mean = rms = variance = float("nan")

    return {
        "path": Path(path).expanduser(),
        "shape": data.shape,
        "rsf_dimensions": rsf.header.dimensions,
        "dtype": data.dtype,
        "size": total,
        "valid_count": int(valid.size),
        "nan_count": nan_count,
        "nonzero_count": nonzero_count,
        "min": min_value,
        "max": max_value,
        "mean": mean,
        "rms": rms,
        "variance": variance,
    }


def format_attr(stats: dict[str, Any]) -> str:
    """Format ``attr_rsf`` output as command-line text."""

    shape = "x".join(str(size) for size in stats["shape"])
    return "\n".join(
        [
            f"path: {stats['path']}",
            f"shape: {shape}",
            f"dtype: {stats['dtype']}",
            f"min: {stats['min']:.7g}",
            f"max: {stats['max']:.7g}",
            f"mean: {stats['mean']:.7g}",
            f"rms: {stats['rms']:.7g}",
            f"variance: {stats['variance']:.7g}",
            f"nonzero_count: {stats['nonzero_count']}",
            f"nan_count: {stats['nan_count']}",
            f"samples: {stats['size']}",
        ]
    )
