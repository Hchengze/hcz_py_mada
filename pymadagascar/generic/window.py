"""Window and decimate RSF arrays with synchronized axis metadata."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np

from pymadagascar.core.axis import Axis
from pymadagascar.core.hypercube import Hypercube
from pymadagascar.core.params import RSFParams
from pymadagascar.io.rsf import RSFArray, RSFHeader


class WindowError(ValueError):
    """Raised when an RSF window request is invalid."""


@dataclass(frozen=True)
class WindowSpec:
    """Per-axis window specification in RSF axis order."""

    f: int
    n: int
    j: int


def window(
    data: np.ndarray,
    header: RSFHeader | Mapping[str, Any],
    axis: int | Sequence[int] | None = None,
    n: int | Sequence[int] | Mapping[int, int] | None = None,
    f: int | Sequence[int] | Mapping[int, int] | None = None,
    j: int | Sequence[int] | Mapping[int, int] | None = None,
) -> RSFArray:
    """Window ``data`` using 1-based RSF axis numbers.

    ``f`` is a zero-based first sample, ``n`` is output sample count, and
    ``j`` is stride. The returned header preserves axis labels and units while
    updating ``n#``, ``o#``, and ``d#``.
    """

    rsf_header = header.copy() if isinstance(header, RSFHeader) else RSFHeader(header)
    cube = Hypercube.from_header(rsf_header)
    array = np.asarray(data)
    if array.shape != cube.numpy_shape:
        raise WindowError(f"data shape {array.shape} does not match RSF header shape {cube.numpy_shape}")

    specs = _window_specs_from_api(cube, axis=axis, n=n, f=f, j=j)
    return _apply_window(array, rsf_header, cube, specs, squeeze=False)


def window_rsf(rsf_array: RSFArray, params: RSFParams | Mapping[str, Any] | None = None) -> RSFArray:
    """Window an ``RSFArray`` using Madagascar-style parameters."""

    param_map = _coerce_params(params)
    cube = Hypercube.from_header(rsf_array.header)
    specs = _window_specs_from_params(cube, param_map)
    squeeze = _get_bool(param_map, "squeeze", True)
    return _apply_window(rsf_array.data, rsf_array.header, cube, specs, squeeze=squeeze)


def _apply_window(
    data: np.ndarray,
    header: RSFHeader,
    cube: Hypercube,
    specs: Sequence[WindowSpec],
    *,
    squeeze: bool,
) -> RSFArray:
    slices: list[slice] = [slice(None)] * cube.ndim
    axes: list[Axis] = []
    for rsf_axis, (axis, spec) in enumerate(zip(cube.axes, specs), start=1):
        stop = spec.f + spec.n * spec.j
        numpy_axis = cube.ndim - rsf_axis
        slices[numpy_axis] = slice(spec.f, stop, spec.j)
        axes.append(
            axis.copy(
                n=spec.n,
                o=axis.o + spec.f * axis.d,
                d=axis.d * spec.j,
            )
        )

    windowed = np.ascontiguousarray(data[tuple(slices)])
    if squeeze:
        axes = [axis for axis in axes if axis.n != 1] + [axis for axis in axes if axis.n == 1]
        squeezed_cube = Hypercube(axes)
        windowed = np.ascontiguousarray(windowed.reshape(squeezed_cube.numpy_shape))
        output_header = squeezed_cube.to_header(header)
    else:
        output_header = Hypercube(axes).to_header(header)

    return RSFArray(windowed, output_header)


def _window_specs_from_api(
    cube: Hypercube,
    *,
    axis: int | Sequence[int] | None,
    n: int | Sequence[int] | Mapping[int, int] | None,
    f: int | Sequence[int] | Mapping[int, int] | None,
    j: int | Sequence[int] | Mapping[int, int] | None,
) -> tuple[WindowSpec, ...]:
    axes = _normalize_axis_selection(axis, cube.ndim)
    n_map = _normalize_api_values(n, axes, "n")
    f_map = _normalize_api_values(f, axes, "f")
    j_map = _normalize_api_values(j, axes, "j")

    specs: list[WindowSpec] = []
    for axis_number, axis_obj in enumerate(cube.axes, start=1):
        stride = int(j_map.get(axis_number, 1))
        start = int(f_map.get(axis_number, 0))
        start = _normalize_start(axis_number, start, axis_obj.n)
        count = n_map.get(axis_number)
        if count is None:
            count = _default_count(axis_obj.n, start, stride)
        specs.append(_validate_spec(axis_number, axis_obj.n, start, int(count), stride))
    return tuple(specs)


def _window_specs_from_params(
    cube: Hypercube,
    params: Mapping[str, Any],
) -> tuple[WindowSpec, ...]:
    specs: list[WindowSpec] = []
    for axis_number, axis_obj in enumerate(cube.axes, start=1):
        stride = _get_int(params, f"j{axis_number}", 1)
        start_value = _get_optional_int(params, f"f{axis_number}")
        if start_value is None and f"min{axis_number}" in params:
            start_value = _coordinate_to_index(params[f"min{axis_number}"], axis_obj.o, axis_obj.d)
        start = _normalize_start(axis_number, start_value if start_value is not None else 0, axis_obj.n)

        count_value = _get_optional_int(params, f"n{axis_number}")
        if count_value is None and f"max{axis_number}" in params:
            new_origin = axis_obj.o + start * axis_obj.d
            new_spacing = axis_obj.d * stride
            count_value = int(1.5 + (float(params[f"max{axis_number}"]) - new_origin) / new_spacing)
        if count_value is None:
            count_value = _default_count(axis_obj.n, start, stride)

        specs.append(_validate_spec(axis_number, axis_obj.n, start, count_value, stride))
    return tuple(specs)


def _validate_spec(axis: int, size: int, start: int, count: int, stride: int) -> WindowSpec:
    if stride < 1:
        raise WindowError(f"j{axis}= must be >= 1")
    if count < 1:
        raise WindowError(f"n{axis}= must be >= 1")
    if start < 0 or start >= size:
        raise WindowError(f"f{axis}={start} is outside 0..{size - 1}")
    last = start + (count - 1) * stride
    if last >= size:
        raise WindowError(
            f"window exceeds axis {axis}: f{axis}={start}, n{axis}={count}, "
            f"j{axis}={stride}, last sample={last}, axis size={size}"
        )
    return WindowSpec(start, count, stride)


def _normalize_start(axis: int, start: int, size: int) -> int:
    if start < 0:
        start = size + start
        if start < 0:
            raise WindowError(f"negative f{axis}= is outside the axis")
    return start


def _default_count(size: int, start: int, stride: int) -> int:
    if stride < 1:
        raise WindowError("stride must be >= 1")
    return ((size - 1 - start) // stride) + 1


def _normalize_axis_selection(axis: int | Sequence[int] | None, ndim: int) -> tuple[int, ...]:
    if axis is None:
        return tuple(range(1, ndim + 1))
    if isinstance(axis, int):
        axes = (axis,)
    else:
        axes = tuple(int(value) for value in axis)
    for value in axes:
        if value < 1 or value > ndim:
            raise WindowError(f"axis must be between 1 and {ndim}, got {value}")
    if len(set(axes)) != len(axes):
        raise WindowError("axis selection must not contain duplicates")
    return axes


def _normalize_api_values(
    values: int | Sequence[int] | Mapping[int, int] | None,
    axes: tuple[int, ...],
    name: str,
) -> dict[int, int]:
    if values is None:
        return {}
    if isinstance(values, Mapping):
        return {int(axis): int(value) for axis, value in values.items()}
    if isinstance(values, int):
        if len(axes) != 1:
            raise WindowError(f"scalar {name}= requires a single axis")
        return {axes[0]: values}

    items = tuple(int(value) for value in values)
    if len(items) != len(axes):
        raise WindowError(f"{name}= length must match selected axes")
    return dict(zip(axes, items))


def _coerce_params(params: RSFParams | Mapping[str, Any] | None) -> Mapping[str, Any]:
    if params is None:
        return {}
    if isinstance(params, RSFParams):
        return params.params
    return params


def _get_optional_int(params: Mapping[str, Any], key: str) -> int | None:
    if key not in params:
        return None
    return int(params[key])


def _get_int(params: Mapping[str, Any], key: str, default: int) -> int:
    if key not in params:
        return default
    return int(params[key])


def _get_bool(params: Mapping[str, Any], key: str, default: bool) -> bool:
    if key not in params:
        return default
    value = str(params[key]).strip().lower()
    if value in {"y", "yes", "true", "t", "1", "on"}:
        return True
    if value in {"n", "no", "false", "f", "0", "off"}:
        return False
    raise WindowError(f"{key}= must be a boolean value")


def _coordinate_to_index(value: Any, origin: float, spacing: float) -> int:
    return int(0.5 + (float(value) - origin) / spacing)
