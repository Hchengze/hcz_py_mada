"""Matplotlib replacement for the common sfgraph workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import numpy as np

from pymadagascar.io.rsf import RSFHeader

from ._common import (
    as_1d,
    axis_label,
    axis_values,
    clip_limits,
    coerce_header,
    pyplot,
    save_figure,
)


def graph(
    data: Any,
    header: RSFHeader | Mapping[str, Any] | None = None,
    *,
    output_path: str | Path | None = None,
    title: str | None = None,
    clip: float | None = None,
    pclip: float | None = None,
    transpose: bool = False,
    color: str = "C0",
    linewidth: float = 1.5,
    figsize: tuple[float, float] = (6.0, 4.0),
) -> Any:
    """Plot a 1D RSF trace as a Matplotlib line graph."""

    rsf_header = coerce_header(header)
    trace = as_1d(data)
    x = axis_values(rsf_header, 1, trace.size)

    plt = pyplot()
    fig, ax = plt.subplots(figsize=figsize)
    if transpose:
        ax.plot(trace, x, color=color, linewidth=linewidth)
        ax.set_xlabel("Amplitude")
        ax.set_ylabel(axis_label(rsf_header, 1, "Axis 1"))
        limits = clip_limits(trace, clip, pclip)
        if limits is not None:
            ax.set_xlim(*limits)
    else:
        ax.plot(x, trace, color=color, linewidth=linewidth)
        ax.set_xlabel(axis_label(rsf_header, 1, "Axis 1"))
        ax.set_ylabel("Amplitude")
        limits = clip_limits(trace, clip, pclip)
        if limits is not None:
            ax.set_ylim(*limits)

    if title:
        ax.set_title(title)
    ax.grid(True, linewidth=0.4, alpha=0.4)
    return save_figure(fig, output_path)
