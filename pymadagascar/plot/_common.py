"""Shared Matplotlib plotting helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import numpy as np

from pymadagascar.io.rsf import RSFHeader


class PlotError(ValueError):
    """Raised when plotting parameters are invalid."""


def pyplot():
    """Import pyplot with a non-interactive backend."""

    import matplotlib

    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt

    return plt


def coerce_header(header: RSFHeader | Mapping[str, Any] | None) -> RSFHeader | None:
    if header is None:
        return None
    if isinstance(header, RSFHeader):
        return header
    return RSFHeader(header)


def axis_values(header: RSFHeader | None, axis: int, n: int) -> np.ndarray:
    if header is None:
        o = 0.0
        d = 1.0
    else:
        o = float(header.get(f"o{axis}", 0.0))
        d = float(header.get(f"d{axis}", 1.0))
    return o + d * np.arange(n, dtype=np.float64)


def axis_label(header: RSFHeader | None, axis: int, fallback: str) -> str:
    if header is None:
        return fallback
    label = header.get(f"label{axis}", fallback)
    unit = header.get(f"unit{axis}")
    return f"{label} ({unit})" if unit else str(label)


def clip_limits(data: np.ndarray, clip: float | None, pclip: float | None) -> tuple[float, float] | None:
    if clip is not None:
        if clip <= 0:
            raise PlotError("clip= must be positive")
        return -float(clip), float(clip)
    if pclip is None:
        return None
    if pclip <= 0 or pclip > 100:
        raise PlotError("pclip= must be > 0 and <= 100")
    finite = np.asarray(data)[np.isfinite(data)]
    if finite.size == 0:
        raise PlotError("cannot estimate pclip from data with no finite samples")
    limit = float(np.percentile(np.abs(finite), pclip))
    if limit <= 0:
        return None
    return -limit, limit


def save_figure(fig: Any, output_path: str | Path | None) -> Any:
    if output_path is None:
        return fig
    path = Path(output_path).expanduser()
    suffix = path.suffix.lower()
    if suffix not in {".png", ".pdf"}:
        raise PlotError("out= must end with .png or .pdf")
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight", dpi=150)
    return fig


def as_1d(data: Any) -> np.ndarray:
    array = np.asarray(data)
    array = np.squeeze(array)
    if array.ndim != 1:
        raise PlotError(f"graph expects 1D data after squeeze, got shape {array.shape}")
    if np.iscomplexobj(array):
        raise PlotError("graph expects real-valued data")
    return np.asarray(array, dtype=np.float64)


def as_2d(data: Any, name: str) -> np.ndarray:
    array = np.asarray(data)
    array = np.squeeze(array)
    if array.ndim != 2:
        raise PlotError(f"{name} expects 2D data after squeeze, got shape {array.shape}")
    if np.iscomplexobj(array):
        raise PlotError(f"{name} expects real-valued data")
    return np.asarray(array, dtype=np.float64)
