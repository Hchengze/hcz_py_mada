"""Small source-aligned spectral transforms for RSF datasets."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import numpy as np

from pymadagascar.core.axis import Axis
from pymadagascar.core.hypercube import Hypercube
from pymadagascar.io.rsf import RSFArray, RSFHeader, read_rsf, write_rsf
from pymadagascar.signal.fft import irfft_rsf, rfft_rsf


CosftNorm = Literal["ortho"]
SpectrumMode = Literal["amplitude", "power"]


class TransformError(ValueError):
    """Raised when a spectral-transform request is invalid."""


def fft1_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    axis: int = 1,
    inverse: bool = False,
    norm: str | None = None,
) -> RSFArray:
    """Run the bounded ``sffft1`` real/complex one-axis FFT subset.

    Forward mode maps real input to a one-sided complex RFFT. Inverse mode maps
    complex one-sided input back to real samples, using stored ``fft_n#``
    metadata when available.
    """

    if inverse:
        return irfft_rsf(input_path, output_path, axis=axis, norm=norm)
    return rfft_rsf(input_path, output_path, axis=axis, norm=norm)


def cosft(
    data: Any,
    *,
    axis: int = 1,
    inverse: bool = False,
    norm: CosftNorm = "ortho",
) -> np.ndarray:
    """Apply a bounded one-axis discrete cosine transform."""

    array = _coerce_real_array(data)
    rsf_axis = _validate_axis(axis, array.ndim)
    _normalize_cosft_norm(norm)
    numpy_axis = array.ndim - rsf_axis
    output = _apply_orthonormal_dct(array.astype(np.float64), axis=numpy_axis, inverse=inverse)
    return np.ascontiguousarray(output.astype(_real_output_dtype(array)))


def cosft_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    axis: int = 1,
    inverse: bool = False,
    norm: CosftNorm = "ortho",
) -> RSFArray:
    """Apply a shape-preserving cosine transform to an RSF file."""

    rsf = read_rsf(input_path)
    result = cosft(rsf.data, axis=axis, inverse=inverse, norm=norm)
    header = _cosft_header(rsf.header, axis=axis, inverse=inverse)
    return write_rsf(output_path, result, header)


def spectra2(
    data: Any,
    *,
    axes: tuple[int, int] | list[int] = (1, 2),
    d1: float = 1.0,
    d2: float = 1.0,
    mode: SpectrumMode = "amplitude",
    average: bool = False,
) -> np.ndarray:
    """Compute a bounded two-dimensional amplitude or power spectrum."""

    array = _coerce_real_array(data)
    axis1, axis2 = _normalize_two_axes(axes, array.ndim)
    normalized_mode = _normalize_spectrum_mode(mode)
    d1_value = _positive_float(d1, "d1")
    d2_value = _positive_float(d2, "d2")
    numpy_axis1 = array.ndim - axis1
    numpy_axis2 = array.ndim - axis2

    working = np.asarray(array, dtype=np.float64)
    working = _center_axis2_for_spectrum(working, axis=numpy_axis2)
    spectrum = np.fft.rfft(working, axis=numpy_axis1)
    spectrum = np.fft.fft(spectrum, axis=numpy_axis2)
    values = np.abs(spectrum) / np.sqrt(float(array.shape[numpy_axis1] * array.shape[numpy_axis2]))
    if normalized_mode == "power":
        values = values * values
    if average:
        mean_axes = tuple(i for i in range(values.ndim) if i not in {numpy_axis1, numpy_axis2})
        if mean_axes:
            values = values.mean(axis=mean_axes)
    _ = (d1_value, d2_value)
    return np.ascontiguousarray(values.astype(_real_output_dtype(array)))


def spectra2_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    axes: tuple[int, int] | list[int] = (1, 2),
    mode: SpectrumMode = "amplitude",
    average: bool = False,
) -> RSFArray:
    """Compute a bounded 2-D spectrum from an RSF file."""

    rsf = read_rsf(input_path)
    cube = Hypercube.from_header(rsf.header)
    axis1, axis2 = _normalize_two_axes(axes, cube.ndim)
    axis1_obj = cube.axis(axis1)
    axis2_obj = cube.axis(axis2)
    result = spectra2(
        rsf.data,
        axes=(axis1, axis2),
        d1=axis1_obj.d,
        d2=axis2_obj.d,
        mode=mode,
        average=average,
    )
    header = _spectra2_header(
        rsf.header,
        axes=(axis1, axis2),
        average=average,
        output_shape=result.shape,
    )
    return write_rsf(output_path, result, header)


def _apply_orthonormal_dct(array: np.ndarray, *, axis: int, inverse: bool) -> np.ndarray:
    n = array.shape[axis]
    matrix = _orthonormal_dct_matrix(n)
    transform = matrix.T if inverse else matrix
    moved = np.moveaxis(array, axis, -1)
    output = np.tensordot(moved, transform.T, axes=([-1], [0]))
    return np.moveaxis(output, -1, axis)


def _orthonormal_dct_matrix(n: int) -> np.ndarray:
    if n < 1:
        raise TransformError("cosft axis length must be positive")
    samples = np.arange(n, dtype=np.float64) + 0.5
    freqs = np.arange(n, dtype=np.float64)[:, None]
    matrix = np.cos(np.pi * freqs * samples / float(n))
    matrix[0, :] *= np.sqrt(1.0 / n)
    if n > 1:
        matrix[1:, :] *= np.sqrt(2.0 / n)
    return matrix


def _cosft_header(header: RSFHeader, *, axis: int, inverse: bool) -> RSFHeader:
    cube = Hypercube.from_header(header)
    axis = _validate_axis(axis, cube.ndim)
    axis_obj = cube.axis(axis)
    output = header.copy()
    if inverse:
        restored = axis_obj.copy(
            o=float(output.get(f"cosft_o{axis}", axis_obj.o)),
            d=float(output.get(f"cosft_d{axis}", axis_obj.d)),
            label=output.get(f"cosft_label{axis}", axis_obj.label),
            unit=output.get(f"cosft_unit{axis}", axis_obj.unit),
        )
        output = cube.update_axis(axis, **_axis_updates(restored)).to_header(output)
        for prefix in ("cosft_o", "cosft_d", "cosft_label", "cosft_unit"):
            key = f"{prefix}{axis}"
            if key in output:
                del output[key]
        return output

    output[f"cosft_o{axis}"] = axis_obj.o
    output[f"cosft_d{axis}"] = axis_obj.d
    if axis_obj.label is not None:
        output[f"cosft_label{axis}"] = axis_obj.label
    if axis_obj.unit is not None:
        output[f"cosft_unit{axis}"] = axis_obj.unit
    transformed = axis_obj.copy(
        o=0.0,
        d=_cosft_spacing(axis_obj),
        label=_frequency_label(axis_obj.label),
        unit=_frequency_unit(axis_obj.unit),
    )
    return cube.update_axis(axis, **_axis_updates(transformed)).to_header(output)


def _spectra2_header(
    header: RSFHeader,
    *,
    axes: tuple[int, int],
    average: bool,
    output_shape: tuple[int, ...],
) -> RSFHeader:
    cube = Hypercube.from_header(header)
    axis1, axis2 = axes
    axis1_obj = cube.axis(axis1)
    axis2_obj = cube.axis(axis2)
    freq_axis = Axis(
        n=axis1_obj.n // 2 + 1,
        o=0.0,
        d=1.0 / (axis1_obj.n * _positive_float(axis1_obj.d, f"d{axis1}")),
        label="Frequency",
        unit=_frequency_unit(axis1_obj.unit),
        index=axis1,
    )
    wave_axis = Axis(
        n=axis2_obj.n,
        o=-0.5 / _positive_float(axis2_obj.d, f"d{axis2}"),
        d=1.0 / (axis2_obj.n * _positive_float(axis2_obj.d, f"d{axis2}")),
        label="Wavenumber",
        unit=_frequency_unit(axis2_obj.unit),
        index=axis2,
    )
    if average:
        ordered = [freq_axis.copy(index=1), wave_axis.copy(index=2)]
        return Hypercube(ordered).to_header(header)
    output = cube.update_axis(axis1, **_axis_updates(freq_axis))
    output = output.update_axis(axis2, **_axis_updates(wave_axis))
    rsf_header = output.to_header(header)
    rsf_header.set_dimensions_from_shape(output_shape)
    return rsf_header


def _center_axis2_for_spectrum(array: np.ndarray, *, axis: int) -> np.ndarray:
    length = array.shape[axis]
    signs = np.ones(length, dtype=np.float64)
    signs[1::2] = -1.0
    shape = [1] * array.ndim
    shape[axis] = length
    return array * signs.reshape(shape)


def _axis_updates(axis_obj: Axis) -> dict[str, Any]:
    return {
        "n": axis_obj.n,
        "o": axis_obj.o,
        "d": axis_obj.d,
        "label": axis_obj.label,
        "unit": axis_obj.unit,
    }


def _cosft_spacing(axis_obj: Axis) -> float:
    if axis_obj.n <= 1:
        return 1.0
    return 1.0 / (2.0 * (axis_obj.n - 1) * _positive_float(axis_obj.d, f"d{axis_obj.index}"))


def _frequency_label(label: str | None) -> str:
    if label in {"Time", "time"}:
        return "Frequency" if label == "Time" else "frequency"
    return "Frequency"


def _frequency_unit(unit: str | None) -> str | None:
    if unit is None:
        return None
    if unit == "s":
        return "Hz"
    if unit.startswith("1/"):
        return unit[2:]
    return f"1/{unit}"


def _coerce_real_array(data: Any) -> np.ndarray:
    array = np.asarray(data)
    if array.ndim < 1:
        raise TransformError("transform input must have at least one dimension")
    if np.iscomplexobj(array):
        raise TransformError("this transform subset requires real-valued input")
    if not np.issubdtype(array.dtype, np.number):
        raise TransformError("transform input must be numeric")
    return np.asarray(array, dtype=np.float64 if array.dtype == np.dtype("float64") else np.float32)


def _real_output_dtype(array: np.ndarray) -> np.dtype[Any]:
    return np.dtype("float64") if array.dtype == np.dtype("float64") else np.dtype("float32")


def _validate_axis(axis: int, ndim: int) -> int:
    value = int(axis)
    if value < 1 or value > ndim:
        raise TransformError(f"axis must be between 1 and {ndim}, got {axis}")
    return value


def _normalize_two_axes(axes: tuple[int, int] | list[int], ndim: int) -> tuple[int, int]:
    if len(axes) != 2:
        raise TransformError("axes must contain exactly two RSF axes")
    axis1 = _validate_axis(int(axes[0]), ndim)
    axis2 = _validate_axis(int(axes[1]), ndim)
    if axis1 == axis2:
        raise TransformError("axes must be distinct")
    return axis1, axis2


def _normalize_cosft_norm(norm: str) -> str:
    if str(norm).strip().lower() != "ortho":
        raise TransformError("cosft currently supports norm='ortho' only")
    return "ortho"


def _normalize_spectrum_mode(mode: str) -> str:
    normalized = str(mode).strip().lower()
    if normalized not in {"amplitude", "power"}:
        raise TransformError("mode= must be 'amplitude' or 'power'")
    return normalized


def _positive_float(value: float, name: str) -> float:
    result = float(value)
    if result <= 0.0:
        raise TransformError(f"{name}= must be positive")
    return result
