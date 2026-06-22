"""Basic array math operations for file-backed RSF datasets."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any
import warnings

import numpy as np

from pymadagascar.core.hypercube import Hypercube
from pymadagascar.io.rsf import RSFArray, read_rsf, write_rsf
from pymadagascar.seismic._utils import broadcast_axis_values, validate_rsf_axis


class ArrayMathError(ValueError):
    """Raised when a basic array math operation is invalid."""


def add_rsf(
    inputs: Sequence[str | Path],
    output_path: str | Path,
) -> RSFArray:
    """Add compatible RSF datasets element by element."""

    if len(inputs) < 2:
        raise ArrayMathError("add_rsf requires at least two input files")

    arrays = [read_rsf(path) for path in inputs]
    _check_compatible_arrays(arrays)
    dtype = _addition_dtype([array.data for array in arrays])
    result = np.asarray(arrays[0].data, dtype=dtype).copy()
    for array in arrays[1:]:
        result = result + np.asarray(array.data, dtype=dtype)
    return write_rsf(output_path, np.ascontiguousarray(result.astype(dtype)), arrays[0].header.copy())


def scale_rsf(
    input_path: str | Path,
    output_path: str | Path,
    scale: float | complex,
) -> RSFArray:
    """Multiply an RSF dataset by a scalar."""

    rsf = read_rsf(input_path)
    dtype = _scaled_dtype(rsf.data)
    if isinstance(scale, complex) and scale.imag != 0.0:
        dtype = np.dtype("complex64")
    result = np.asarray(rsf.data, dtype=dtype) * scale
    return write_rsf(output_path, np.ascontiguousarray(result.astype(dtype)), rsf.header.copy())


def multiply_rsf(
    input_path: str | Path,
    other: str | Path | None,
    output_path: str | Path,
    *,
    scalar: float | complex | None = None,
) -> RSFArray:
    """Multiply an RSF dataset by another compatible RSF file or by a scalar."""

    rsf = read_rsf(input_path)
    _ensure_single_other(other, scalar, operation="multiply")

    if scalar is not None:
        scalar_array = _scalar_array_for_dtype(scalar, rsf.data)
        dtype = _multiply_dtype(rsf.data, scalar_array)
        result = np.asarray(rsf.data, dtype=dtype) * np.asarray(scalar_array, dtype=dtype)
    else:
        assert other is not None
        other_rsf = read_rsf(other)
        _check_compatible_arrays([rsf, other_rsf])
        dtype = _multiply_dtype(rsf.data, other_rsf.data)
        result = np.asarray(rsf.data, dtype=dtype) * np.asarray(other_rsf.data, dtype=dtype)

    return write_rsf(output_path, np.ascontiguousarray(_cast_supported(result)), rsf.header.copy())


def divide_rsf(
    input_path: str | Path,
    other: str | Path | None,
    output_path: str | Path,
    *,
    scalar: float | complex | None = None,
    zero_policy: str = "raise",
) -> RSFArray:
    """Divide an RSF dataset by another compatible RSF file or by a scalar."""

    rsf = read_rsf(input_path)
    _ensure_single_other(other, scalar, operation="divide")
    policy = zero_policy.strip().lower()
    if policy not in {"raise", "warn", "nan", "inf"}:
        raise ArrayMathError("zero_policy must be one of: raise, warn, nan, inf")

    if scalar is not None:
        denominator = np.asarray(scalar)
    else:
        assert other is not None
        other_rsf = read_rsf(other)
        _check_compatible_arrays([rsf, other_rsf])
        denominator = np.asarray(other_rsf.data)

    zero_mask = denominator == 0
    has_zero = bool(np.any(zero_mask))
    if has_zero and policy == "raise":
        raise ArrayMathError("division denominator contains zero values")
    if has_zero and policy == "warn":
        warnings.warn(
            "division denominator contains zero values; output may contain inf or nan",
            RuntimeWarning,
            stacklevel=2,
        )

    dtype = _division_dtype(rsf.data, denominator)
    numerator = np.asarray(rsf.data, dtype=dtype)
    divisor = np.asarray(denominator, dtype=dtype)
    if has_zero and policy == "nan":
        result = np.full(numerator.shape, np.nan, dtype=dtype)
        np.divide(numerator, divisor, out=result, where=~zero_mask)
    else:
        with np.errstate(divide="ignore", invalid="ignore"):
            result = np.divide(numerator, divisor)

    return write_rsf(output_path, np.ascontiguousarray(_cast_supported(result)), rsf.header.copy())


def tpow_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    power: float = 1.0,
    axis: int = 1,
    abs_time: bool = False,
) -> RSFArray:
    """Apply ``t ** power`` gain along a 1-based RSF axis."""

    rsf = read_rsf(input_path)
    cube = Hypercube.from_header(rsf.header)
    axis = validate_rsf_axis(axis, cube.ndim)
    coords = cube.axis(axis).coordinates()
    if abs_time:
        coords = np.abs(coords)

    if power < 0 and np.any(coords == 0):
        raise ArrayMathError("tpow with negative power is undefined for zero coordinates")

    gain_coords = coords.copy()
    if not abs_time and _is_fractional_power(power):
        gain_coords[gain_coords <= 0] = 0.0

    with np.errstate(invalid="ignore", divide="ignore"):
        gain = np.power(gain_coords, power)
    if np.any(np.isnan(gain)):
        raise ArrayMathError(
            "tpow produced nan gain values; use abs_time=y or choose an integer power"
        )

    dtype = _tpow_dtype(rsf.data, gain)
    result = np.asarray(rsf.data, dtype=dtype) * broadcast_axis_values(
        gain.astype(dtype, copy=False), axis=axis, ndim=rsf.data.ndim
    )
    return write_rsf(output_path, np.ascontiguousarray(result.astype(dtype)), rsf.header.copy())


def clip_rsf(
    input_path: str | Path,
    output_path: str | Path,
    clip: float,
    *,
    value: float | None = None,
) -> RSFArray:
    """Clip real-valued RSF data using the ``sfclip`` ``clip=``/``value=`` subset."""

    if clip < 0:
        raise ArrayMathError("clip= must be non-negative")
    replacement = float(clip if value is None else value)

    rsf = read_rsf(input_path)
    if np.iscomplexobj(rsf.data):
        raise ArrayMathError("clip_rsf only supports real-valued data")

    dtype = _real_output_dtype(rsf.data)
    data = np.asarray(rsf.data, dtype=dtype)
    result = data.copy()
    result[data > clip] = replacement
    result[data < -clip] = -replacement
    nonfinite = ~np.isfinite(data)
    result[nonfinite] = np.where(np.signbit(data[nonfinite]), -replacement, replacement)
    return write_rsf(output_path, np.ascontiguousarray(result.astype(dtype)), rsf.header.copy())


def normalize_rsf(
    input_path: str | Path,
    output_path: str | Path,
    mode: str = "max",
) -> RSFArray:
    """Normalize an RSF dataset by max absolute value or RMS amplitude."""

    rsf = read_rsf(input_path)
    dtype = _scaled_dtype(rsf.data)
    factor = _normalization_factor(rsf.data, mode)
    result = np.asarray(rsf.data, dtype=dtype) * factor
    return write_rsf(output_path, np.ascontiguousarray(result.astype(dtype)), rsf.header.copy())


def _check_compatible_arrays(arrays: Sequence[RSFArray]) -> None:
    reference = arrays[0]
    for index, array in enumerate(arrays[1:], start=2):
        if array.data.shape != reference.data.shape:
            raise ArrayMathError(
                f"shape mismatch for input {index}: {array.data.shape} != {reference.data.shape}"
            )
        if array.header.dimensions != reference.header.dimensions:
            raise ArrayMathError(
                f"RSF n# mismatch for input {index}: "
                f"{array.header.dimensions} != {reference.header.dimensions}"
            )


def _ensure_single_other(other: str | Path | None, scalar: object | None, *, operation: str) -> None:
    if scalar is None and other is None:
        raise ArrayMathError(f"{operation} requires either another RSF file or scalar=")
    if scalar is not None and other is not None:
        raise ArrayMathError(f"{operation} accepts either another RSF file or scalar=, not both")


def _addition_dtype(arrays: Sequence[np.ndarray]) -> np.dtype[Any]:
    dtypes = [np.asarray(array).dtype for array in arrays]
    if any(np.issubdtype(dtype, np.complexfloating) for dtype in dtypes):
        return np.dtype("complex64")
    if any(dtype == np.dtype("float64") for dtype in dtypes):
        return np.dtype("float64")
    if any(np.issubdtype(dtype, np.floating) for dtype in dtypes):
        return np.dtype("float32")
    return np.dtype("int32")


def _cast_supported(data: np.ndarray) -> np.ndarray:
    dtype = np.asarray(data).dtype
    if np.issubdtype(dtype, np.complexfloating):
        return np.asarray(data, dtype=np.complex64)
    if dtype == np.dtype("float64"):
        return np.asarray(data, dtype=np.float64)
    if np.issubdtype(dtype, np.floating):
        return np.asarray(data, dtype=np.float32)
    if np.issubdtype(dtype, np.integer):
        return np.asarray(data, dtype=np.int32)
    return np.asarray(data, dtype=np.float32)


def _multiply_dtype(left: np.ndarray, right: np.ndarray) -> np.dtype[Any]:
    dtypes = [np.asarray(left).dtype, np.asarray(right).dtype]
    if any(np.issubdtype(dtype, np.complexfloating) for dtype in dtypes):
        return np.dtype("complex64")
    if any(dtype == np.dtype("float64") for dtype in dtypes):
        return np.dtype("float64")
    if any(np.issubdtype(dtype, np.floating) for dtype in dtypes):
        return np.dtype("float32")
    return np.dtype("int32")


def _scalar_array_for_dtype(scalar: float | complex, data: np.ndarray) -> np.ndarray:
    if isinstance(scalar, complex) and scalar.imag != 0.0:
        return np.asarray(scalar, dtype=np.complex64)
    if np.asarray(data).dtype == np.dtype("float64"):
        return np.asarray(scalar, dtype=np.float64)
    return np.asarray(scalar, dtype=np.float32)


def _division_dtype(numerator: np.ndarray, denominator: np.ndarray) -> np.dtype[Any]:
    dtypes = [np.asarray(numerator).dtype, np.asarray(denominator).dtype]
    if any(np.issubdtype(dtype, np.complexfloating) for dtype in dtypes):
        return np.dtype("complex64")
    if any(dtype == np.dtype("float64") for dtype in dtypes):
        return np.dtype("float64")
    return np.dtype("float32")


def _tpow_dtype(data: np.ndarray, gain: np.ndarray) -> np.dtype[Any]:
    dtype = np.result_type(data, gain, np.float32)
    if np.issubdtype(dtype, np.complexfloating):
        return np.dtype("complex64")
    if dtype == np.dtype("float64"):
        return np.dtype("float64")
    return np.dtype("float32")


def _is_fractional_power(power: float) -> bool:
    return not float(power).is_integer()


def _scaled_dtype(data: np.ndarray) -> np.dtype[Any]:
    dtype = np.asarray(data).dtype
    if np.issubdtype(dtype, np.complexfloating):
        return np.dtype("complex64")
    return _real_output_dtype(data)


def _real_output_dtype(data: np.ndarray) -> np.dtype[Any]:
    dtype = np.asarray(data).dtype
    if dtype == np.dtype("float64"):
        return np.dtype("float64")
    return np.dtype("float32")


def _normalization_factor(data: np.ndarray, mode: str) -> float:
    normalized = mode.strip().lower()
    amplitudes = np.abs(np.asarray(data))
    finite = amplitudes[np.isfinite(amplitudes)]
    if finite.size == 0:
        raise ArrayMathError("cannot normalize data with no finite samples")

    if normalized in {"max", "maximum"}:
        scale = float(np.max(finite))
    elif normalized == "rms":
        scale = float(np.sqrt(np.mean(np.square(finite))))
    else:
        raise ArrayMathError("mode= must be max or rms")

    if scale == 0.0:
        return 1.0
    return 1.0 / scale
