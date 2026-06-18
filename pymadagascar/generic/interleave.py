"""Interleave compatible file-backed RSF datasets."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np

from pymadagascar.core.hypercube import Hypercube
from pymadagascar.io.rsf import RSFArray, read_rsf, write_rsf
from pymadagascar.seismic._utils import numpy_axis, validate_rsf_axis


class InterleaveError(ValueError):
    """Raised when RSF interleaving inputs are incompatible."""


def interleave_rsf(
    input_paths: Sequence[str | Path],
    output_path: str | Path,
    *,
    axis: int = 1,
) -> RSFArray:
    """Interleave two or more compatible RSF datasets along a 1-based RSF axis."""

    if len(input_paths) < 2:
        raise InterleaveError("interleave_rsf requires at least two input files")

    arrays = [read_rsf(path) for path in input_paths]
    cube = Hypercube.from_header(arrays[0].header)
    axis = validate_rsf_axis(axis, cube.ndim)
    _check_interleave_compatible(arrays, axis=axis)

    np_axis = numpy_axis(axis, arrays[0].data.ndim)
    dtype = _interleave_dtype([array.data for array in arrays])
    moved = [np.moveaxis(np.asarray(array.data, dtype=dtype), np_axis, 0) for array in arrays]
    n_axis = moved[0].shape[0]
    stacked = np.stack(moved, axis=1)
    interleaved = stacked.reshape(n_axis * len(arrays), *moved[0].shape[1:])
    result = np.moveaxis(interleaved, 0, np_axis)

    out_cube = cube.update_axis(axis, n=cube.axis(axis).n * len(arrays))
    return write_rsf(
        output_path,
        np.ascontiguousarray(result.astype(dtype)),
        out_cube.to_header(arrays[0].header.copy()),
    )


def _check_interleave_compatible(arrays: Sequence[RSFArray], *, axis: int) -> None:
    reference = arrays[0]
    reference_cube = Hypercube.from_header(reference.header)
    for index, array in enumerate(arrays[1:], start=2):
        if array.data.shape != reference.data.shape:
            raise InterleaveError(
                f"shape mismatch for input {index}: {array.data.shape} != {reference.data.shape}"
            )
        if array.header.dimensions != reference.header.dimensions:
            raise InterleaveError(
                f"RSF n# mismatch for input {index}: "
                f"{array.header.dimensions} != {reference.header.dimensions}"
            )
        cube = Hypercube.from_header(array.header)
        for axis_index in range(1, reference_cube.ndim + 1):
            ref_axis = reference_cube.axis(axis_index)
            current = cube.axis(axis_index)
            if current.n != ref_axis.n:
                raise InterleaveError(f"n{axis_index} mismatch for input {index}: need {ref_axis.n}")
            if axis_index == axis:
                continue
            if current.o != ref_axis.o or current.d != ref_axis.d:
                raise InterleaveError(
                    f"o{axis_index}/d{axis_index} mismatch for input {index}: "
                    f"need o={ref_axis.o}, d={ref_axis.d}"
                )


def _interleave_dtype(arrays: Sequence[np.ndarray]) -> np.dtype[Any]:
    dtype = np.result_type(*[np.asarray(array).dtype for array in arrays])
    if np.issubdtype(dtype, np.complexfloating):
        return np.dtype("complex64")
    if dtype == np.dtype("float64"):
        return np.dtype("float64")
    if np.issubdtype(dtype, np.floating):
        return np.dtype("float32")
    return np.dtype("int32")
