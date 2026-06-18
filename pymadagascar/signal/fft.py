"""NumPy FFT transforms for file-backed RSF datasets."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal

import numpy as np

from pymadagascar.core.axis import Axis
from pymadagascar.core.hypercube import Hypercube
from pymadagascar.io.rsf import RSFArray, RSFHeader, read_rsf, write_rsf


FFTTransform = Literal["fft", "ifft", "rfft", "irfft"]


class FFTError(ValueError):
    """Raised when an FFT request is invalid."""


def fft_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    axis: int = 1,
    norm: str | None = None,
) -> RSFArray:
    """Compute a centered complex FFT along a 1-based RSF axis."""

    rsf = read_rsf(input_path)
    cube = Hypercube.from_header(rsf.header)
    axis = _validate_axis(axis, cube.ndim)
    numpy_axis = cube.ndim - axis
    norm_value = _normalize_norm(norm)

    output = np.fft.fft(np.asarray(rsf.data, dtype=np.complex64), axis=numpy_axis, norm=norm_value)
    output = np.fft.fftshift(output, axes=numpy_axis).astype(np.complex64)
    header = fft_axis_header_update(rsf.header, axis=axis, transform="fft")
    return write_rsf(output_path, np.ascontiguousarray(output), header)


def ifft_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    axis: int = 1,
    norm: str | None = None,
) -> RSFArray:
    """Invert a centered complex FFT along a 1-based RSF axis."""

    rsf = read_rsf(input_path)
    if not np.iscomplexobj(rsf.data):
        raise FFTError("ifft_rsf requires complex input")
    cube = Hypercube.from_header(rsf.header)
    axis = _validate_axis(axis, cube.ndim)
    numpy_axis = cube.ndim - axis
    norm_value = _normalize_norm(norm)

    shifted = np.fft.ifftshift(rsf.data, axes=numpy_axis)
    output = np.fft.ifft(shifted, axis=numpy_axis, norm=norm_value).astype(np.complex64)
    header = fft_axis_header_update(rsf.header, axis=axis, transform="ifft")
    return write_rsf(output_path, np.ascontiguousarray(output), header)


def rfft_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    axis: int = 1,
    norm: str | None = None,
) -> RSFArray:
    """Compute a real-to-complex FFT along a 1-based RSF axis."""

    rsf = read_rsf(input_path)
    if np.iscomplexobj(rsf.data):
        raise FFTError("rfft_rsf requires real-valued input")
    cube = Hypercube.from_header(rsf.header)
    axis = _validate_axis(axis, cube.ndim)
    numpy_axis = cube.ndim - axis
    norm_value = _normalize_norm(norm)

    output = np.fft.rfft(np.asarray(rsf.data, dtype=np.float32), axis=numpy_axis, norm=norm_value)
    output = output.astype(np.complex64)
    header = fft_axis_header_update(rsf.header, axis=axis, transform="rfft")
    return write_rsf(output_path, np.ascontiguousarray(output), header)


def irfft_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    axis: int = 1,
    n: int | None = None,
    norm: str | None = None,
) -> RSFArray:
    """Invert a real-to-complex FFT along a 1-based RSF axis."""

    rsf = read_rsf(input_path)
    if not np.iscomplexobj(rsf.data):
        raise FFTError("irfft_rsf requires complex input")
    cube = Hypercube.from_header(rsf.header)
    axis = _validate_axis(axis, cube.ndim)
    numpy_axis = cube.ndim - axis
    n_out = _inverse_real_length(rsf.header, axis, cube.axis(axis).n, n)
    norm_value = _normalize_norm(norm)

    output = np.fft.irfft(rsf.data, n=n_out, axis=numpy_axis, norm=norm_value).astype(np.float32)
    header = fft_axis_header_update(rsf.header, axis=axis, transform="irfft", n=n_out)
    return write_rsf(output_path, np.ascontiguousarray(output), header)


def fft_axis_header_update(
    header: RSFHeader | Mapping[str, Any],
    *,
    axis: int,
    transform: FFTTransform,
    n: int | None = None,
) -> RSFHeader:
    """Return a header with one RSF axis updated for an FFT transform."""

    rsf_header = header.copy() if isinstance(header, RSFHeader) else RSFHeader(header)
    cube = Hypercube.from_header(rsf_header)
    axis = _validate_axis(axis, cube.ndim)
    axis_obj = cube.axis(axis)

    if transform in {"fft", "rfft"}:
        output_axis = _frequency_axis(axis_obj, axis, transform=transform)
        output_header = cube.update_axis(axis, **_axis_updates(output_axis)).to_header(rsf_header)
        _store_original_axis(output_header, axis_obj, axis)
        return output_header

    if transform in {"ifft", "irfft"}:
        output_axis = _spatial_axis(rsf_header, axis_obj, axis, n=n)
        output_header = cube.update_axis(axis, **_axis_updates(output_axis)).to_header(rsf_header)
        _remove_original_axis_metadata(output_header, axis)
        return output_header

    raise FFTError(f"unsupported FFT transform {transform!r}")


def _frequency_axis(axis_obj: Axis, axis: int, *, transform: str) -> Axis:
    if axis_obj.d == 0.0:
        raise FFTError(f"d{axis}= must be nonzero")

    if transform == "rfft":
        n_out = axis_obj.n // 2 + 1
        spacing = 1.0 / (axis_obj.n * axis_obj.d)
        origin = 0.0
    else:
        frequencies = np.fft.fftshift(np.fft.fftfreq(axis_obj.n, d=axis_obj.d))
        n_out = axis_obj.n
        origin = float(frequencies[0]) if frequencies.size else 0.0
        spacing = float(frequencies[1] - frequencies[0]) if frequencies.size > 1 else 1.0

    return axis_obj.copy(
        n=n_out,
        o=origin,
        d=spacing,
        label=_fft_label(axis_obj.label, forward=True),
        unit=_fft_unit(axis_obj.unit),
    )


def _spatial_axis(
    header: RSFHeader,
    axis_obj: Axis,
    axis: int,
    *,
    n: int | None,
) -> Axis:
    restored_n = int(n if n is not None else header.get(f"fft_n{axis}", axis_obj.n))
    restored_o = float(header.get(f"fft_o{axis}", 0.0))
    if f"fft_d{axis}" in header:
        restored_d = float(header[f"fft_d{axis}"])
    else:
        restored_d = 1.0 / (restored_n * axis_obj.d) if axis_obj.d != 0.0 else 1.0
    label = header.get(f"fft_label{axis}", _fft_label(axis_obj.label, forward=False))
    unit = header.get(f"fft_unit{axis}", _fft_unit(axis_obj.unit))
    return axis_obj.copy(n=restored_n, o=restored_o, d=restored_d, label=label, unit=unit)


def _store_original_axis(header: RSFHeader, axis_obj: Axis, axis: int) -> None:
    header[f"fft_n{axis}"] = axis_obj.n
    header[f"fft_o{axis}"] = axis_obj.o
    header[f"fft_d{axis}"] = axis_obj.d
    if axis_obj.label is not None:
        header[f"fft_label{axis}"] = axis_obj.label
    if axis_obj.unit is not None:
        header[f"fft_unit{axis}"] = axis_obj.unit


def _remove_original_axis_metadata(header: RSFHeader, axis: int) -> None:
    for prefix in ("fft_n", "fft_o", "fft_d", "fft_label", "fft_unit"):
        key = f"{prefix}{axis}"
        if key in header:
            del header[key]


def _axis_updates(axis_obj: Axis) -> dict[str, Any]:
    return {
        "n": axis_obj.n,
        "o": axis_obj.o,
        "d": axis_obj.d,
        "label": axis_obj.label,
        "unit": axis_obj.unit,
    }


def _fft_label(label: str | None, *, forward: bool) -> str:
    if label == "Time":
        return "Frequency"
    if label == "time":
        return "frequency"
    if label == "Frequency":
        return "Time"
    if label == "frequency":
        return "time"
    return "Frequency" if forward else "Time"


def _fft_unit(unit: str | None) -> str | None:
    if unit is None:
        return None
    if unit == "s":
        return "Hz"
    if unit == "Hz":
        return "s"
    if unit.startswith("1/"):
        return unit[2:]
    return f"1/{unit}"


def _inverse_real_length(header: RSFHeader, axis: int, current_n: int, requested: int | None) -> int:
    if requested is not None:
        n_out = int(requested)
    elif f"fft_n{axis}" in header:
        n_out = int(header[f"fft_n{axis}"])
    else:
        n_out = 2 * (current_n - 1)
    if n_out < 1:
        raise FFTError("inverse FFT output length must be positive")
    return n_out


def _normalize_norm(norm: str | None) -> str | None:
    if norm in {None, "", "none"}:
        return None
    normalized = str(norm).strip().lower()
    if normalized in {"backward", "forward", "ortho"}:
        return normalized
    raise FFTError("norm= must be backward, forward, ortho, or omitted")


def _validate_axis(axis: int, ndim: int) -> int:
    value = int(axis)
    if value < 1 or value > ndim:
        raise FFTError(f"axis must be between 1 and {ndim}, got {axis}")
    return value
