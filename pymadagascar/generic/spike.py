"""Generate simple RSF spike datasets."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Mapping

import numpy as np

from pymadagascar.core.axis import Axis
from pymadagascar.io.rsf import RSFArray, RSFError, RSFHeader, format_from_dtype


def spike(
    shape: int | Sequence[int],
    locations: int | Sequence[int] | Sequence[Sequence[int]] | None = None,
    magnitudes: float | complex | Sequence[float | complex] | None = None,
    axes: Sequence[Axis | Mapping[str, Any]] | None = None,
    dtype: Any = "float32",
) -> RSFArray:
    """Create an RSFArray with point spikes on a zero background.

    ``shape`` and ``locations`` are in RSF axis order: ``(n1, n2, ...)`` and
    ``(k1, k2, ...)``. Locations use Madagascar's 1-based sample numbering.
    The returned NumPy array uses the existing pymadagascar RSF convention:
    ``data.shape == tuple(reversed(shape))``.
    """

    rsf_shape = _normalize_shape(shape)
    ndim = len(rsf_shape)
    dtype_obj = np.dtype(dtype)
    data_format = format_from_dtype(dtype_obj)
    data = np.zeros(tuple(reversed(rsf_shape)), dtype=dtype_obj)

    normalized_locations = _normalize_locations(locations, ndim)
    normalized_magnitudes = _normalize_magnitudes(magnitudes, len(normalized_locations))
    for location, magnitude in zip(normalized_locations, normalized_magnitudes):
        _validate_location(location, rsf_shape)
        numpy_index = tuple(sample - 1 for sample in reversed(location))
        data[numpy_index] += magnitude

    header = _make_header(rsf_shape, axes, data_format, dtype_obj.itemsize)
    return RSFArray(data, header)


def _normalize_shape(shape: int | Sequence[int]) -> tuple[int, ...]:
    if isinstance(shape, int):
        normalized = (shape,)
    else:
        normalized = tuple(int(size) for size in shape)
    if not normalized:
        raise ValueError("shape must contain at least one RSF axis")
    if len(normalized) > 9:
        raise ValueError("RSF supports at most 9 axes")
    if any(size < 1 for size in normalized):
        raise ValueError("all shape dimensions must be positive")
    return normalized


def _normalize_locations(
    locations: int | Sequence[int] | Sequence[Sequence[int]] | None,
    ndim: int,
) -> list[tuple[int, ...]]:
    if locations is None:
        return []
    if isinstance(locations, (int, np.integer)):
        if ndim != 1:
            raise ValueError("integer locations are only valid for 1-D spikes")
        return [(int(locations),)]

    values = list(locations)
    if not values:
        return []

    if ndim == 1 and all(_is_scalar(value) for value in values):
        return [(int(value),) for value in values]

    if len(values) == ndim and all(_is_scalar(value) for value in values):
        return [tuple(int(value) for value in values)]

    normalized: list[tuple[int, ...]] = []
    for item in values:
        if _is_scalar(item):
            raise ValueError("each multi-dimensional location must be a sequence")
        location = tuple(int(value) for value in item)  # type: ignore[arg-type]
        if len(location) != ndim:
            raise ValueError("location dimensionality must match shape")
        normalized.append(location)
    return normalized


def _normalize_magnitudes(
    magnitudes: float | complex | Sequence[float | complex] | None,
    count: int,
) -> list[float | complex]:
    if count == 0:
        return []
    if magnitudes is None:
        return [1.0] * count
    if _is_scalar(magnitudes):
        return [magnitudes] * count  # type: ignore[list-item]

    values = list(magnitudes)
    if not values:
        raise ValueError("magnitudes must not be empty when locations are provided")
    if len(values) == 1 and count > 1:
        values = values * count
    if len(values) != count:
        raise ValueError("magnitudes length must match number of spike locations")
    return values


def _validate_location(location: tuple[int, ...], shape: tuple[int, ...]) -> None:
    for axis, (sample, size) in enumerate(zip(location, shape), start=1):
        if sample < 1 or sample > size:
            raise ValueError(f"k{axis}={sample} is outside 1..{size}")


def _make_header(
    shape: tuple[int, ...],
    axes: Sequence[Axis | Mapping[str, Any]] | None,
    data_format: str,
    esize: int,
) -> RSFHeader:
    header = RSFHeader({"data_format": data_format, "esize": esize})
    normalized_axes = _normalize_axes(shape, axes)
    for axis in normalized_axes:
        index = axis.index
        header[f"n{index}"] = axis.n
        header[f"o{index}"] = axis.o
        header[f"d{index}"] = axis.d
        if axis.label is not None and _should_write_text(axis.label):
            header[f"label{index}"] = axis.label
        if axis.unit is not None and _should_write_text(axis.unit):
            header[f"unit{index}"] = axis.unit
    return header


def _normalize_axes(
    shape: tuple[int, ...],
    axes: Sequence[Axis | Mapping[str, Any]] | None,
) -> tuple[Axis, ...]:
    if axes is None:
        return tuple(
            Axis(
                n=size,
                o=0.0,
                d=0.004 if index == 1 else 0.1,
                label="Time" if index == 1 else "Distance",
                unit="s" if index == 1 else "km",
                index=index,
            )
            for index, size in enumerate(shape, start=1)
        )

    if len(axes) != len(shape):
        raise ValueError("axes length must match shape dimensionality")

    normalized: list[Axis] = []
    for index, (axis, size) in enumerate(zip(axes, shape), start=1):
        if isinstance(axis, Axis):
            item = axis.copy(index=index)
        else:
            item = Axis(
                n=int(axis.get("n", size)),
                o=float(axis.get("o", 0.0)),
                d=float(axis.get("d", 0.004 if index == 1 else 0.1)),
                label=axis.get("label", "Time" if index == 1 else "Distance"),
                unit=axis.get("unit", "s" if index == 1 else "km"),
                index=index,
            )
        if item.n != size:
            raise ValueError(f"axis {index} has n={item.n}, expected {size}")
        normalized.append(item)
    return tuple(normalized)


def _is_scalar(value: Any) -> bool:
    return isinstance(value, (str, bytes, int, float, complex, np.generic))


def _should_write_text(value: str) -> bool:
    return value != "" and value != " "
