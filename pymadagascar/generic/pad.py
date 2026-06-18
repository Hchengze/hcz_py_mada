"""Padding and dimensional extension helpers for RSF datasets."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np

from pymadagascar.core.axis import Axis
from pymadagascar.core.hypercube import Hypercube
from pymadagascar.io.rsf import RSFArray, SF_MAX_DIM, read_rsf, write_rsf


class PadError(ValueError):
    """Raised when padding or dimensional extension parameters are invalid."""


def pad_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    n: Mapping[int, int] | None = None,
    beg: Mapping[int, int] | None = None,
    end: Mapping[int, int] | None = None,
    value: float = 0.0,
) -> RSFArray:
    """Pad an RSF dataset using 1-based RSF axis numbers.

    ``beg`` and ``end`` are sample counts to add before and after each axis.
    ``n`` requests an output axis length and therefore determines ``end`` after
    accounting for the input length and ``beg``. This mirrors Madagascar's
    documented ``n#``/``n#out`` padding style.
    """

    rsf = read_rsf(input_path)
    cube = Hypercube.from_header(rsf.header)
    n_map = _normalize_axis_map(n, "n")
    beg_map = _normalize_axis_map(beg, "beg")
    end_map = _normalize_axis_map(end, "end")
    output_ndim = _output_ndim(cube.ndim, n_map, beg_map, end_map)

    axes = _extended_axes(cube, output_ndim)
    beg_values: list[int] = []
    end_values: list[int] = []
    output_axes: list[Axis] = []
    for axis_number, axis_obj in enumerate(axes, start=1):
        before = beg_map.get(axis_number, 0)
        after = end_map.get(axis_number, 0)
        if before < 0:
            raise PadError(f"beg{axis_number}= must be non-negative")
        if after < 0:
            raise PadError(f"end{axis_number}= must be non-negative")

        if axis_number in n_map:
            requested = _normalize_requested_n(n_map[axis_number], axis_obj.n)
            after = requested - axis_obj.n - before
            if after < 0:
                raise PadError(
                    f"n{axis_number}= is too small for input n={axis_obj.n} and beg{axis_number}={before}"
                )
        new_n = axis_obj.n + before + after
        beg_values.append(before)
        end_values.append(after)
        output_axes.append(
            axis_obj.copy(
                n=new_n,
                o=axis_obj.o - before * axis_obj.d,
            )
        )

    extended_cube = Hypercube(axes)
    array = np.asarray(rsf.data).reshape(extended_cube.numpy_shape)
    pad_width = [(0, 0)] * output_ndim
    for axis_number, (before, after) in enumerate(zip(beg_values, end_values), start=1):
        pad_width[output_ndim - axis_number] = (before, after)

    padded = np.pad(
        array,
        pad_width,
        mode="constant",
        constant_values=value,
    )
    output_header = Hypercube(output_axes).to_header(rsf.header)
    return write_rsf(output_path, np.ascontiguousarray(padded.astype(rsf.data.dtype)), output_header)


def _normalize_axis_map(values: Mapping[int, int] | None, name: str) -> dict[int, int]:
    normalized: dict[int, int] = {}
    for axis, value in (values or {}).items():
        axis_number = int(axis)
        if axis_number < 1 or axis_number > SF_MAX_DIM:
            raise PadError(f"{name} axis must be between 1 and {SF_MAX_DIM}, got {axis_number}")
        normalized[axis_number] = int(value)
    return normalized


def _output_ndim(
    ndim: int,
    *maps: Mapping[int, Any],
) -> int:
    highest = ndim
    for axis_map in maps:
        if axis_map:
            highest = max(highest, max(axis_map))
    if highest > SF_MAX_DIM:
        raise PadError(f"RSF supports at most {SF_MAX_DIM} axes")
    return highest


def _extended_axes(cube: Hypercube, output_ndim: int) -> list[Axis]:
    axes = list(cube.axes)
    for axis_number in range(cube.ndim + 1, output_ndim + 1):
        axes.append(Axis(n=1, o=0.0, d=1.0, index=axis_number))
    return axes


def _normalize_requested_n(requested: int, input_n: int) -> int:
    if requested < 0:
        raise PadError("n# must be non-negative")
    if requested == 0:
        output = 1
        while output < input_n:
            output *= 2
        return output
    return requested
