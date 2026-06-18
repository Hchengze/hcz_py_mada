"""Spray and tile RSF datasets along regular axes."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from pymadagascar.core.axis import Axis
from pymadagascar.core.hypercube import Hypercube
from pymadagascar.io.rsf import RSFArray, read_rsf, write_rsf


class SprayError(ValueError):
    """Raised when spray or tile parameters are invalid."""


def spray_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    axis: int = 2,
    n: int,
    o: float = 0.0,
    d: float = 1.0,
    label: str | None = None,
    unit: str | None = None,
) -> RSFArray:
    """Insert a new 1-based RSF axis and duplicate data along it."""

    rsf = read_rsf(input_path)
    cube = Hypercube.from_header(rsf.header)
    if axis < 1 or axis > cube.ndim + 1:
        raise SprayError(f"axis must be between 1 and {cube.ndim + 1}")
    if n < 1:
        raise SprayError("n= must be >= 1")

    numpy_axis = cube.ndim - axis + 1
    output = np.repeat(np.expand_dims(rsf.data, axis=numpy_axis), repeats=n, axis=numpy_axis)
    new_axis = Axis(n=n, o=o, d=d, label=label, unit=unit, index=axis)
    axes = list(cube.axes)
    axes.insert(axis - 1, new_axis)
    output_header = Hypercube(axes).to_header(rsf.header)
    return write_rsf(output_path, np.ascontiguousarray(output), output_header)


def tile_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    axis: int = 2,
    repeat: int,
) -> RSFArray:
    """Repeat an existing RSF axis by tiling complete axis blocks."""

    rsf = read_rsf(input_path)
    cube = Hypercube.from_header(rsf.header)
    if axis < 1 or axis > cube.ndim:
        raise SprayError(f"axis must be between 1 and {cube.ndim}")
    if repeat < 1:
        raise SprayError("repeat= must be >= 1")

    numpy_axis = cube.ndim - axis
    output = np.concatenate([rsf.data] * repeat, axis=numpy_axis)
    axis_obj = cube.axis(axis)
    output_header = cube.update_axis(axis, n=axis_obj.n * repeat).to_header(rsf.header)
    return write_rsf(output_path, np.ascontiguousarray(output), output_header)
