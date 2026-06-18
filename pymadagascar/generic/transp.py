"""Transpose and reshape file-backed RSF datasets."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np

from pymadagascar.core.axis import Axis
from pymadagascar.core.hypercube import Hypercube
from pymadagascar.io.rsf import RSFArray, RSFHeader, SF_MAX_DIM, read_rsf, write_rsf


class TransposeError(ValueError):
    """Raised when transpose or reshape parameters are invalid."""


def transpose_array(
    data: np.ndarray,
    header: RSFHeader | Mapping[str, Any],
    order: Sequence[int],
) -> RSFArray:
    """Transpose an array using a 1-based RSF axis ``order``.

    ``order=(2, 1)`` means output axis 1 is input axis 2, and output axis 2 is
    input axis 1. The NumPy array axes are transformed accordingly because RSF
    ``n1`` is stored as the fastest-varying, last NumPy dimension.
    """

    rsf_header = header.copy() if isinstance(header, RSFHeader) else RSFHeader(header)
    cube = Hypercube.from_header(rsf_header)
    array = np.asarray(data)
    if array.shape != cube.numpy_shape:
        raise TransposeError(
            f"data shape {array.shape} does not match RSF header shape {cube.numpy_shape}"
        )

    normalized_order = _normalize_order(order, cube.ndim)
    numpy_order = [cube.ndim - axis for axis in reversed(normalized_order)]
    output = np.ascontiguousarray(np.transpose(array, axes=numpy_order))
    output_cube = Hypercube([cube.axis(axis) for axis in normalized_order])
    output_header = output_cube.to_header(rsf_header)
    return RSFArray(output, output_header)


def transpose_rsf(
    input_path: str | Path,
    output_path: str | Path,
    order: Sequence[int],
) -> RSFArray:
    """Read, transpose, and write a file-backed RSF dataset."""

    rsf = read_rsf(input_path)
    result = transpose_array(rsf.data, rsf.header, order)
    return write_rsf(output_path, result.data, result.header)


def reshape_rsf(
    input_path: str | Path,
    output_path: str | Path,
    shape: int | Sequence[int],
) -> RSFArray:
    """Reshape an RSF dataset while preserving linear sample order."""

    rsf = read_rsf(input_path)
    rsf_shape = _normalize_shape(shape)
    new_numpy_shape = tuple(reversed(rsf_shape))
    if int(np.prod(rsf_shape)) != rsf.data.size:
        raise TransposeError(
            f"reshape sample count mismatch: requested {rsf_shape} has "
            f"{int(np.prod(rsf_shape))} samples, input has {rsf.data.size}"
        )

    output = np.ascontiguousarray(np.asarray(rsf.data).reshape(new_numpy_shape))
    output_header = _reshape_header(rsf.header, rsf_shape)
    return write_rsf(output_path, output, output_header)


def _normalize_order(order: Sequence[int], ndim: int) -> tuple[int, ...]:
    values = tuple(int(axis) for axis in order)
    if len(values) != ndim:
        raise TransposeError(f"order must contain exactly {ndim} RSF axes")
    expected = set(range(1, ndim + 1))
    actual = set(values)
    if actual != expected:
        raise TransposeError(
            f"order must be a 1-based permutation of {sorted(expected)}, got {values}"
        )
    if len(actual) != len(values):
        raise TransposeError("order must not contain duplicate axes")
    return values


def _normalize_shape(shape: int | Sequence[int]) -> tuple[int, ...]:
    if isinstance(shape, int):
        values = (shape,)
    else:
        values = tuple(int(size) for size in shape)
    if not values:
        raise TransposeError("shape must contain at least one RSF axis")
    if len(values) > SF_MAX_DIM:
        raise TransposeError(f"RSF supports at most {SF_MAX_DIM} axes")
    if any(size < 1 for size in values):
        raise TransposeError("all reshape dimensions must be positive")
    return values


def _reshape_header(header: RSFHeader, shape: tuple[int, ...]) -> RSFHeader:
    axes: list[Axis] = []
    for index, size in enumerate(shape, start=1):
        axes.append(
            Axis(
                n=size,
                o=float(header.get(f"o{index}", 0.0)),
                d=float(header.get(f"d{index}", 1.0)),
                label=header.get(f"label{index}"),
                unit=header.get(f"unit{index}"),
                index=index,
            )
        )
    return Hypercube(axes).to_header(header)
