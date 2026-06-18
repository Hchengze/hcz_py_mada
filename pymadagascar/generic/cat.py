"""Concatenate compatible RSF datasets along an RSF axis."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from pymadagascar.core.axis import Axis
from pymadagascar.core.hypercube import Hypercube
from pymadagascar.io.rsf import RSFArray, RSFHeader, SF_MAX_DIM, read_rsf, write_rsf


class CatError(ValueError):
    """Raised when RSF datasets cannot be concatenated safely."""


def cat_arrays(
    arrays: Sequence[np.ndarray],
    headers: Sequence[RSFHeader | Mapping[str, Any]],
    axis: int,
) -> RSFArray:
    """Concatenate arrays and headers along a 1-based RSF ``axis``."""

    if not arrays:
        raise CatError("cat_arrays requires at least one input array")
    if len(arrays) != len(headers):
        raise CatError("arrays and headers must have the same length")

    rsf_headers = [header.copy() if isinstance(header, RSFHeader) else RSFHeader(header) for header in headers]
    normalized_axis = _normalize_axis(axis, rsf_headers[0])
    output_ndim = max(normalized_axis, *(len(header.dimensions) for header in rsf_headers))
    dims = [_extended_dims(header, output_ndim) for header in rsf_headers]
    _check_compatible(arrays, rsf_headers, dims, normalized_axis)

    reshaped = [
        _reshape_array(np.asarray(array), header, dims_i)
        for array, header, dims_i in zip(arrays, rsf_headers, dims)
    ]
    numpy_axis = output_ndim - normalized_axis
    data = np.ascontiguousarray(np.concatenate(reshaped, axis=numpy_axis))

    output_dims = list(dims[0])
    output_dims[normalized_axis - 1] = sum(item[normalized_axis - 1] for item in dims)
    header = _output_header(rsf_headers[0], output_dims, normalized_axis)
    return RSFArray(data, header)


def cat_rsf(
    inputs: Sequence[str | Path | RSFArray],
    output: str | Path,
    axis: int,
) -> RSFArray:
    """Read, concatenate, and write RSF files."""

    if len(inputs) < 1:
        raise CatError("cat_rsf requires at least one input")
    rsfs = [read_rsf(item) if not isinstance(item, RSFArray) else item for item in inputs]
    result = cat_arrays([rsf.data for rsf in rsfs], [rsf.header for rsf in rsfs], axis=axis)
    return write_rsf(output, result.data, result.header)


def _normalize_axis(axis: int, first_header: RSFHeader) -> int:
    axis = int(axis)
    if axis == 0:
        dims = first_header.dimensions
        for index in range(len(dims), 0, -1):
            if dims[index - 1] > 1:
                return index
        return 1
    if axis < 1 or axis > SF_MAX_DIM:
        raise CatError(f"axis must be between 1 and {SF_MAX_DIM}, got {axis}")
    return axis


def _extended_dims(header: RSFHeader, ndim: int) -> tuple[int, ...]:
    dims = header.dimensions
    if len(dims) > ndim:
        raise CatError("internal dimension normalization error")
    return dims + (1,) * (ndim - len(dims))


def _reshape_array(array: np.ndarray, header: RSFHeader, dims: tuple[int, ...]) -> np.ndarray:
    expected_shape = header.shape
    if array.shape != expected_shape:
        raise CatError(f"array shape {array.shape} does not match header shape {expected_shape}")
    return array.reshape(tuple(reversed(dims)))


def _check_compatible(
    arrays: Sequence[np.ndarray],
    headers: Sequence[RSFHeader],
    dims: Sequence[tuple[int, ...]],
    axis: int,
) -> None:
    first_dtype = np.asarray(arrays[0]).dtype
    first_format = headers[0].data_format
    first_esize = headers[0].esize

    for index, (array, header) in enumerate(zip(arrays, headers), start=1):
        if np.asarray(array).dtype != first_dtype:
            raise CatError(
                f"dtype mismatch for input {index}: {np.asarray(array).dtype} != {first_dtype}"
            )
        if header.data_format != first_format:
            raise CatError(
                f"data_format mismatch for input {index}: {header.data_format} != {first_format}"
            )
        if header.esize != first_esize:
            raise CatError(f"esize mismatch for input {index}: {header.esize} != {first_esize}")

    reference_dims = dims[0]
    for input_index, input_dims in enumerate(dims[1:], start=2):
        for axis_index, (left, right) in enumerate(zip(reference_dims, input_dims), start=1):
            if axis_index != axis and left != right:
                raise CatError(
                    f"n{axis_index} mismatch for input {input_index}: {right} != {left}"
                )

    reference_header = headers[0]
    for input_index, header in enumerate(headers[1:], start=2):
        for axis_index in range(1, len(reference_dims) + 1):
            if axis_index == axis:
                continue
            _check_axis_float("d", axis_index, reference_header, header, input_index)
            _check_axis_float("o", axis_index, reference_header, header, input_index)


def _check_axis_float(
    prefix: str,
    axis: int,
    reference: RSFHeader,
    other: RSFHeader,
    input_index: int,
) -> None:
    key = f"{prefix}{axis}"
    left = float(reference.get(key, 1.0 if prefix == "d" else 0.0))
    right = float(other.get(key, 1.0 if prefix == "d" else 0.0))
    tol = 1.0e-6 * max(abs(left), 1.0)
    if abs(left - right) > tol:
        raise CatError(f"{key} mismatch for input {input_index}: {right:g} != {left:g}")


def _output_header(first_header: RSFHeader, dims: Sequence[int], axis: int) -> RSFHeader:
    axes: list[Axis] = []
    for index, size in enumerate(dims, start=1):
        axes.append(
            Axis(
                n=int(size),
                o=float(first_header.get(f"o{index}", 0.0)),
                d=float(first_header.get(f"d{index}", 1.0)),
                label=first_header.get(f"label{index}"),
                unit=first_header.get(f"unit{index}"),
                index=index,
            )
        )
    header = Hypercube(axes).to_header(first_header)
    header[f"n{axis}"] = int(dims[axis - 1])
    return header
