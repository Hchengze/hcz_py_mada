"""Zero selected windows of RSF datasets without changing shape."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

import numpy as np

from pymadagascar.core.hypercube import Hypercube
from pymadagascar.io.rsf import RSFArray, read_rsf, write_rsf


class CutError(ValueError):
    """Raised when a cut operation is invalid."""


def cut_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    axis: int | Sequence[int] = 1,
    f: int | Sequence[int] | Mapping[int, int] = 0,
    n: int | Sequence[int] | Mapping[int, int] | None = None,
    j: int | Sequence[int] | Mapping[int, int] = 1,
) -> RSFArray:
    """Zero a strided window on one or more 1-based RSF axes."""

    rsf = read_rsf(input_path)
    cube = Hypercube.from_header(rsf.header)
    axes = _normalize_axes(axis, cube.ndim)
    starts = _normalize_axis_values(f, axes, "f")
    strides = _normalize_axis_values(j, axes, "j")
    counts = _normalize_optional_axis_values(n, axes, "n")

    slices: list[slice] = [slice(None)] * cube.ndim
    for rsf_axis in axes:
        size = cube.axis(rsf_axis).n
        start = _normalize_start(starts[rsf_axis], size, rsf_axis)
        stride = strides[rsf_axis]
        if stride < 1:
            raise CutError(f"j{rsf_axis}= must be >= 1")
        count = counts.get(rsf_axis)
        if count is None:
            count = ((size - 1 - start) // stride) + 1
        if count < 1:
            raise CutError(f"n{rsf_axis}= must be >= 1")
        last = start + (count - 1) * stride
        if last >= size:
            raise CutError(
                f"cut window exceeds axis {rsf_axis}: f={start}, n={count}, "
                f"j={stride}, last sample={last}, axis size={size}"
            )
        slices[cube.ndim - rsf_axis] = slice(start, last + 1, stride)

    result = np.asarray(rsf.data).copy()
    result[tuple(slices)] = 0
    return write_rsf(output_path, np.ascontiguousarray(result), rsf.header.copy())


def _normalize_axes(axis: int | Sequence[int], ndim: int) -> tuple[int, ...]:
    if isinstance(axis, int):
        axes = (axis,)
    else:
        axes = tuple(int(value) for value in axis)
    if not axes:
        raise CutError("axis selection must not be empty")
    if len(set(axes)) != len(axes):
        raise CutError("axis selection must not contain duplicates")
    for value in axes:
        if value < 1 or value > ndim:
            raise CutError(f"axis must be between 1 and {ndim}, got {value}")
    return axes


def _normalize_axis_values(
    values: int | Sequence[int] | Mapping[int, int],
    axes: tuple[int, ...],
    name: str,
) -> dict[int, int]:
    if isinstance(values, Mapping):
        return _validate_mapping(values, axes, name)
    if isinstance(values, int):
        return {axis: int(values) for axis in axes}
    items = tuple(int(value) for value in values)
    if len(items) != len(axes):
        raise CutError(f"{name}= length must match selected axes")
    return dict(zip(axes, items))


def _normalize_optional_axis_values(
    values: int | Sequence[int] | Mapping[int, int] | None,
    axes: tuple[int, ...],
    name: str,
) -> dict[int, int]:
    if values is None:
        return {}
    return _normalize_axis_values(values, axes, name)


def _validate_mapping(values: Mapping[int, int], axes: tuple[int, ...], name: str) -> dict[int, int]:
    result = {int(axis): int(value) for axis, value in values.items()}
    for axis in result:
        if axis not in axes:
            raise CutError(f"{name} mapping includes unselected axis {axis}")
    missing = [axis for axis in axes if axis not in result]
    if missing:
        raise CutError(f"{name} mapping is missing axis {missing[0]}")
    return result


def _normalize_start(start: int, size: int, axis: int) -> int:
    value = int(start)
    if value < 0:
        value = size + value
    if value < 0 or value >= size:
        raise CutError(f"f{axis}={start} is outside 0..{size - 1}")
    return value
