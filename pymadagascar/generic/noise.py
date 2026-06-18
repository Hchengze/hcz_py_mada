"""Synthetic random noise helpers for RSF data."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any
import math

import numpy as np

from pymadagascar.core.axis import Axis
from pymadagascar.io.rsf import (
    RSFArray,
    RSFHeader,
    SF_MAX_DIM,
    format_from_dtype,
    read_rsf,
    write_rsf,
)


class NoiseError(ValueError):
    """Raised when random noise parameters are invalid."""


def noise(
    shape: int | Sequence[int] | None = None,
    header: RSFHeader | Mapping[str, Any] | None = None,
    seed: int | None = None,
    mean: float = 0.0,
    std: float = 1.0,
    distribution: str | bool = "normal",
    *,
    var: float | None = None,
    noise_range: float | None = None,
    dtype: Any = "float32",
    axes: Sequence[Axis | Mapping[str, Any]] | None = None,
) -> RSFArray:
    """Generate a synthetic noise RSFArray.

    ``shape`` is in RSF axis order ``(n1, n2, ...)``; returned NumPy data uses
    the project convention ``data.shape == tuple(reversed(shape))``.
    """

    dtype_obj = _normalize_noise_dtype(dtype)
    rsf_shape = _resolve_rsf_shape(shape, header, axes)
    numpy_shape = tuple(reversed(rsf_shape))
    data = _generate_noise(
        numpy_shape,
        dtype_obj,
        seed=seed,
        mean=mean,
        std=std,
        distribution=distribution,
        var=var,
        noise_range=noise_range,
    )
    output_header = _make_header(rsf_shape, header, axes, dtype_obj)
    return RSFArray(np.ascontiguousarray(data), output_header)


def add_noise(
    data: np.ndarray,
    std: float = 1.0,
    seed: int | None = None,
    distribution: str | bool = "normal",
    *,
    mean: float = 0.0,
    var: float | None = None,
    noise_range: float | None = None,
) -> np.ndarray:
    """Return ``data`` plus random noise.

    Real floating inputs preserve float32/float64 precision. Integer inputs are
    promoted to float32. Complex inputs get independent real and imaginary
    noise components.
    """

    array = np.asarray(data)
    dtype_obj = _output_dtype_for_input(array.dtype)
    samples = _generate_noise(
        array.shape,
        dtype_obj,
        seed=seed,
        mean=mean,
        std=std,
        distribution=distribution,
        var=var,
        noise_range=noise_range,
    )
    return np.ascontiguousarray(array.astype(dtype_obj, copy=False) + samples)


def noise_rsf(
    input_path: str | Path | None = None,
    output_path: str | Path | None = None,
    *,
    shape: int | Sequence[int] | None = None,
    header: RSFHeader | Mapping[str, Any] | None = None,
    seed: int | None = None,
    mean: float = 0.0,
    std: float = 1.0,
    distribution: str | bool = "normal",
    var: float | None = None,
    noise_range: float | None = None,
    replace: bool = False,
    dtype: Any = "float32",
    axes: Sequence[Axis | Mapping[str, Any]] | None = None,
) -> RSFArray:
    """Generate noise or add noise to an existing RSF file."""

    if input_path is None:
        result = noise(
            shape=shape,
            header=header,
            seed=seed,
            mean=mean,
            std=std,
            distribution=distribution,
            var=var,
            noise_range=noise_range,
            dtype=dtype,
            axes=axes,
        )
    else:
        input_rsf = read_rsf(input_path)
        output_header = input_rsf.header.copy()
        if replace:
            result = noise(
                shape=input_rsf.header.dimensions,
                header=output_header,
                seed=seed,
                mean=mean,
                std=std,
                distribution=distribution,
                var=var,
                noise_range=noise_range,
                dtype=_output_dtype_for_input(input_rsf.data.dtype),
            )
        else:
            data = add_noise(
                input_rsf.data,
                std=std,
                seed=seed,
                distribution=distribution,
                mean=mean,
                var=var,
                noise_range=noise_range,
            )
            result = RSFArray(data, output_header)

    if output_path is None:
        return result
    return write_rsf(output_path, result.data, result.header)


def _generate_noise(
    shape: tuple[int, ...],
    dtype: np.dtype[Any],
    *,
    seed: int | None,
    mean: float,
    std: float,
    distribution: str | bool,
    var: float | None,
    noise_range: float | None,
) -> np.ndarray:
    normalized_distribution = _normalize_distribution(distribution)
    rng = np.random.default_rng(seed)
    if np.issubdtype(dtype, np.complexfloating):
        component_dtype = np.float32 if dtype == np.dtype("complex64") else np.float64
        real = _generate_real_noise(
            shape,
            component_dtype,
            rng,
            mean=mean,
            std=std,
            distribution=normalized_distribution,
            var=var,
            noise_range=noise_range,
        )
        imag = _generate_real_noise(
            shape,
            component_dtype,
            rng,
            mean=mean,
            std=std,
            distribution=normalized_distribution,
            var=var,
            noise_range=noise_range,
        )
        return (real + 1j * imag).astype(dtype)
    return _generate_real_noise(
        shape,
        dtype,
        rng,
        mean=mean,
        std=std,
        distribution=normalized_distribution,
        var=var,
        noise_range=noise_range,
    )


def _generate_real_noise(
    shape: tuple[int, ...],
    dtype: np.dtype[Any],
    rng: np.random.Generator,
    *,
    mean: float,
    std: float,
    distribution: str,
    var: float | None,
    noise_range: float | None,
) -> np.ndarray:
    scale = _resolve_scale(distribution, std=std, var=var, noise_range=noise_range)
    if distribution == "normal":
        values = rng.normal(loc=mean, scale=scale, size=shape)
    else:
        values = rng.uniform(low=mean - scale, high=mean + scale, size=shape)
    return values.astype(dtype, copy=False)


def _resolve_scale(
    distribution: str,
    *,
    std: float,
    var: float | None,
    noise_range: float | None,
) -> float:
    if var is not None:
        if var < 0:
            raise NoiseError("var= must be non-negative")
        std_value = math.sqrt(float(var))
        return std_value if distribution == "normal" else math.sqrt(3.0) * std_value
    if noise_range is not None:
        if noise_range < 0:
            raise NoiseError("range= must be non-negative")
        return (2.0 * float(noise_range) / 9.0) if distribution == "normal" else float(noise_range)
    if std < 0:
        raise NoiseError("std= must be non-negative")
    return float(std) if distribution == "normal" else math.sqrt(3.0) * float(std)


def _normalize_distribution(distribution: str | bool) -> str:
    if isinstance(distribution, bool):
        return "normal" if distribution else "uniform"
    normalized = str(distribution).strip().lower()
    if normalized in {"normal", "gaussian", "gauss", "n", "yes", "y", "true", "1"}:
        return "normal"
    if normalized in {"uniform", "u", "flat", "no", "false", "0"}:
        return "uniform"
    raise NoiseError("distribution= must be normal or uniform")


def _normalize_noise_dtype(dtype: Any) -> np.dtype[Any]:
    dtype_obj = np.dtype(dtype)
    if np.issubdtype(dtype_obj, np.floating) or np.issubdtype(dtype_obj, np.complexfloating):
        format_from_dtype(dtype_obj)
        return dtype_obj
    raise NoiseError("noise dtype must be a supported floating or complex dtype")


def _output_dtype_for_input(dtype: np.dtype[Any]) -> np.dtype[Any]:
    dtype_obj = np.dtype(dtype)
    if dtype_obj == np.dtype("complex64"):
        return np.dtype("complex64")
    if dtype_obj == np.dtype("complex128"):
        return np.dtype("complex128")
    if dtype_obj == np.dtype("float64"):
        return np.dtype("float64")
    return np.dtype("float32")


def _resolve_rsf_shape(
    shape: int | Sequence[int] | None,
    header: RSFHeader | Mapping[str, Any] | None,
    axes: Sequence[Axis | Mapping[str, Any]] | None,
) -> tuple[int, ...]:
    if axes is not None:
        axis_shape = tuple(_coerce_axis(axis, index).n for index, axis in enumerate(axes, start=1))
        if shape is not None and _normalize_shape(shape) != axis_shape:
            raise NoiseError("shape does not match axes")
        if header is not None and _coerce_header(header).dimensions != axis_shape:
            raise NoiseError("header dimensions do not match axes")
        return axis_shape
    if header is not None:
        header_shape = _coerce_header(header).dimensions
        if shape is not None and _normalize_shape(shape) != header_shape:
            raise NoiseError("shape does not match header dimensions")
        return header_shape
    if shape is None:
        raise NoiseError("noise generation requires shape, header, axes, or input_path")
    return _normalize_shape(shape)


def _normalize_shape(shape: int | Sequence[int]) -> tuple[int, ...]:
    if isinstance(shape, (int, np.integer)):
        normalized = (int(shape),)
    else:
        normalized = tuple(int(size) for size in shape)
    if not normalized:
        raise NoiseError("shape must contain at least one RSF axis")
    if len(normalized) > SF_MAX_DIM:
        raise NoiseError(f"RSF supports at most {SF_MAX_DIM} axes")
    if any(size < 1 for size in normalized):
        raise NoiseError("all shape dimensions must be positive")
    return normalized


def _make_header(
    rsf_shape: tuple[int, ...],
    header: RSFHeader | Mapping[str, Any] | None,
    axes: Sequence[Axis | Mapping[str, Any]] | None,
    dtype: np.dtype[Any],
) -> RSFHeader:
    output = _coerce_header(header).copy() if header is not None else RSFHeader()
    if axes is not None:
        normalized_axes = tuple(_coerce_axis(axis, index) for index, axis in enumerate(axes, start=1))
    elif header is not None:
        normalized_axes = _axes_from_header(_coerce_header(header))
    else:
        normalized_axes = _default_axes(rsf_shape)
    for axis in normalized_axes:
        output[f"n{axis.index}"] = axis.n
        output[f"o{axis.index}"] = axis.o
        output[f"d{axis.index}"] = axis.d
        if axis.label is not None:
            output[f"label{axis.index}"] = axis.label
        if axis.unit is not None:
            output[f"unit{axis.index}"] = axis.unit
    output["data_format"] = format_from_dtype(dtype)
    output["esize"] = dtype.itemsize
    return output


def _default_axes(shape: tuple[int, ...]) -> tuple[Axis, ...]:
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


def _axes_from_header(header: RSFHeader) -> tuple[Axis, ...]:
    return tuple(
        Axis(
            n=int(header[f"n{index}"]),
            o=header.get_float(f"o{index}", 0.0) or 0.0,
            d=header.get_float(f"d{index}", 0.004 if index == 1 else 0.1)
            or (0.004 if index == 1 else 0.1),
            label=header.get_string(f"label{index}", "Time" if index == 1 else "Distance"),
            unit=header.get_string(f"unit{index}", "s" if index == 1 else "km"),
            index=index,
        )
        for index in range(1, len(header.dimensions) + 1)
    )


def _coerce_axis(axis: Axis | Mapping[str, Any], index: int) -> Axis:
    if isinstance(axis, Axis):
        return axis.copy(index=index)
    if "n" not in axis:
        raise NoiseError(f"axis {index} is missing n")
    return Axis(
        n=int(axis["n"]),
        o=float(axis.get("o", 0.0)),
        d=float(axis.get("d", 0.004 if index == 1 else 0.1)),
        label=axis.get("label", "Time" if index == 1 else "Distance"),
        unit=axis.get("unit", "s" if index == 1 else "km"),
        index=index,
    )


def _coerce_header(header: RSFHeader | Mapping[str, Any]) -> RSFHeader:
    return header if isinstance(header, RSFHeader) else RSFHeader(header)
