"""Reverse RSF data along one or more axes."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import numpy as np

from pymadagascar.core.hypercube import Hypercube
from pymadagascar.io.rsf import RSFArray, RSFHeader, read_rsf, write_rsf


class ReverseError(ValueError):
    """Raised when a reverse operation is invalid."""


def reverse_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    axis: int | Sequence[int] = 1,
    update_header: bool = True,
) -> RSFArray:
    """Reverse data along 1-based RSF axes and optionally update ``o#``/``d#``."""

    rsf = read_rsf(input_path)
    cube = Hypercube.from_header(rsf.header)
    axes = _normalize_axes(axis, cube.ndim)

    result = np.asarray(rsf.data)
    for rsf_axis in axes:
        result = np.flip(result, axis=cube.ndim - rsf_axis)

    header = rsf.header.copy()
    if update_header:
        _update_reversed_axes(header, cube, axes)
    return write_rsf(output_path, np.ascontiguousarray(result), header)


def _normalize_axes(axis: int | Sequence[int], ndim: int) -> tuple[int, ...]:
    if isinstance(axis, int):
        axes = (axis,)
    else:
        axes = tuple(int(value) for value in axis)
    if len(set(axes)) != len(axes):
        raise ReverseError("axis selection must not contain duplicates")
    for value in axes:
        if value < 1 or value > ndim:
            raise ReverseError(f"axis must be between 1 and {ndim}, got {value}")
    return axes


def _update_reversed_axes(header: RSFHeader, cube: Hypercube, axes: tuple[int, ...]) -> None:
    for rsf_axis in axes:
        axis = cube.axis(rsf_axis)
        header[f"o{rsf_axis}"] = axis.o + (axis.n - 1) * axis.d
        header[f"d{rsf_axis}"] = -axis.d
