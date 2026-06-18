"""Matplotlib replacement for the common sfwiggle workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import numpy as np

from pymadagascar.io.rsf import RSFHeader

from ._common import (
    PlotError,
    as_2d,
    axis_label,
    axis_values,
    clip_limits,
    coerce_header,
    pyplot,
    save_figure,
)


def wiggle(
    data: Any,
    header: RSFHeader | Mapping[str, Any] | None = None,
    *,
    output_path: str | Path | None = None,
    title: str | None = None,
    clip: float | None = None,
    pclip: float | None = 98.0,
    transpose: bool = False,
    scale: float = 0.75,
    fill: bool = True,
    color: str = "black",
    linewidth: float = 0.8,
    figsize: tuple[float, float] = (7.0, 5.0),
) -> Any:
    """Plot a 2D RSF panel as seismic wiggle traces."""

    if scale <= 0:
        raise PlotError("scale= must be positive")

    rsf_header = coerce_header(header)
    panel = as_2d(data, "wiggle")
    x1 = axis_values(rsf_header, 1, panel.shape[1])
    x2 = axis_values(rsf_header, 2, panel.shape[0])
    spacing = _trace_spacing(x2)
    limits = clip_limits(panel, clip, pclip)
    zclip = limits[1] if limits is not None else _max_abs(panel)
    gain = 0.0 if zclip == 0.0 else scale * spacing / zclip

    plt = pyplot()
    fig, ax = plt.subplots(figsize=figsize)
    for itrace, trace_position in enumerate(x2):
        trace = np.asarray(panel[itrace], dtype=np.float64)
        if limits is not None:
            trace = np.clip(trace, limits[0], limits[1])
        offset = trace_position + trace * gain

        if transpose:
            ax.plot(offset, x1, color=color, linewidth=linewidth)
            if fill:
                ax.fill_betweenx(x1, trace_position, offset, where=offset >= trace_position, color=color, alpha=0.25)
        else:
            ax.plot(x1, offset, color=color, linewidth=linewidth)
            if fill:
                ax.fill_between(x1, trace_position, offset, where=offset >= trace_position, color=color, alpha=0.25)

    if transpose:
        ax.set_xlabel(axis_label(rsf_header, 2, "Axis 2"))
        ax.set_ylabel(axis_label(rsf_header, 1, "Axis 1"))
        ax.invert_yaxis()
    else:
        ax.set_xlabel(axis_label(rsf_header, 1, "Axis 1"))
        ax.set_ylabel(axis_label(rsf_header, 2, "Axis 2"))

    if title:
        ax.set_title(title)
    ax.grid(True, linewidth=0.3, alpha=0.25)
    return save_figure(fig, output_path)


def _trace_spacing(values: np.ndarray) -> float:
    if values.size < 2:
        return 1.0
    diffs = np.diff(values)
    finite = np.abs(diffs[np.isfinite(diffs)])
    if finite.size == 0:
        return 1.0
    spacing = float(np.median(finite))
    return spacing if spacing > 0 else 1.0


def _max_abs(data: np.ndarray) -> float:
    finite = np.abs(data[np.isfinite(data)])
    if finite.size == 0:
        raise PlotError("cannot scale wiggle plot from data with no finite samples")
    return float(np.max(finite))
