"""Matplotlib replacement for the common sfgrey workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import numpy as np

from pymadagascar.io.rsf import RSFHeader

from ._common import (
    as_2d,
    axis_label,
    axis_values,
    clip_limits,
    coerce_header,
    pyplot,
    save_figure,
)


def grey(
    data: Any,
    header: RSFHeader | Mapping[str, Any] | None = None,
    *,
    output_path: str | Path | None = None,
    title: str | None = None,
    clip: float | None = None,
    pclip: float | None = 99.0,
    transpose: bool = False,
    cmap: str = "gray",
    colorbar: bool = True,
    figsize: tuple[float, float] = (6.0, 4.5),
) -> Any:
    """Plot a 2D RSF panel as a Matplotlib image.

    The input follows pymadagascar's NumPy convention: axis 1 (``n1``) is the
    last NumPy dimension and axis 2 (``n2``) is the first NumPy dimension.
    """

    rsf_header = coerce_header(header)
    panel = as_2d(data, "grey")
    if transpose:
        panel = panel.T

    limits = clip_limits(panel, clip, pclip)
    vmin = vmax = None
    if limits is not None:
        vmin, vmax = limits

    x = axis_values(rsf_header, 1, panel.shape[1] if not transpose else panel.shape[0])
    y = axis_values(rsf_header, 2, panel.shape[0] if not transpose else panel.shape[1])
    extent = _extent(x, y, transpose)

    plt = pyplot()
    fig, ax = plt.subplots(figsize=figsize)
    image = ax.imshow(
        panel,
        cmap=cmap,
        origin="upper",
        aspect="auto",
        extent=extent,
        vmin=vmin,
        vmax=vmax,
    )
    ax.set_xlabel(axis_label(rsf_header, 1 if not transpose else 2, "Axis 1"))
    ax.set_ylabel(axis_label(rsf_header, 2 if not transpose else 1, "Axis 2"))
    if title:
        ax.set_title(title)
    if colorbar:
        fig.colorbar(image, ax=ax)
    return save_figure(fig, output_path)


def _extent(x: np.ndarray, y: np.ndarray, transpose: bool) -> tuple[float, float, float, float]:
    if not transpose:
        x0, x1 = _edge_range(x)
        y0, y1 = _edge_range(y)
    else:
        x0, x1 = _edge_range(y)
        y0, y1 = _edge_range(x)
    return x0, x1, y1, y0


def _edge_range(values: np.ndarray) -> tuple[float, float]:
    if values.size == 1:
        return float(values[0] - 0.5), float(values[0] + 0.5)
    step = float(values[1] - values[0])
    return float(values[0] - 0.5 * step), float(values[-1] + 0.5 * step)
