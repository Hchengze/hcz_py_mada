"""FK spectrum analysis and fan filtering for 2D RSF gathers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from pymadagascar.core.axis import Axis
from pymadagascar.core.hypercube import Hypercube
from pymadagascar.io.rsf import RSFArray, RSFHeader, read_rsf, write_rsf
from pymadagascar.seismic._utils import numpy_axis, output_dtype, validate_rsf_axis


class FKError(ValueError):
    """Raised when an FK operation is invalid."""


FK_REFERENCE_SOURCE = "../src-master/system/generic/Mdipfilter.c"
FK_DIRECT_SOURCE_STATUS = "no_direct_Mfk_transform_found"


def fk_spectrum(
    input_path: str | Path,
    output_path: str | Path,
    *,
    time_axis: int = 1,
    space_axis: int = 2,
    amplitude: bool = True,
    norm: str | None = None,
) -> RSFArray:
    """Compute a centered 2D frequency-wavenumber spectrum.

    Axis numbers follow RSF/Madagascar convention: axis 1 is ``n1`` and is the
    fastest varying dimension. For ordinary shot gathers this means ``axis1``
    is time and ``axis2`` is offset/space, while the NumPy array shape is
    ``(n2, n1)``.
    """

    rsf = read_rsf(input_path)
    data = np.asarray(rsf.data)
    _validate_finite_data(data)
    cube = _validate_2d_gather(rsf.header, time_axis=time_axis, space_axis=space_axis)
    norm_value = _normalize_norm(norm)

    time_np = numpy_axis(time_axis, cube.ndim)
    space_np = numpy_axis(space_axis, cube.ndim)
    spectrum = _forward_fk(data, time_np=time_np, space_np=space_np, norm=norm_value)
    header = fk_axis_header_update(
        rsf.header,
        time_axis=time_axis,
        space_axis=space_axis,
    )
    _store_spectrum_metadata(header, amplitude=amplitude, norm=norm_value)

    if amplitude:
        output = np.abs(spectrum).astype(np.float32)
    else:
        output = spectrum.astype(np.complex64)
    return write_rsf(output_path, np.ascontiguousarray(output), header)


def fk_filter(
    input_path: str | Path,
    output_path: str | Path,
    *,
    vmin: float | None = None,
    vmax: float | None = None,
    taper: float = 0.0,
    reject: bool = False,
    time_axis: int = 1,
    space_axis: int = 2,
    norm: str | None = None,
) -> RSFArray:
    """Apply a zero-phase FK fan velocity filter to a 2D gather."""

    rsf = read_rsf(input_path)
    data = np.asarray(rsf.data)
    _validate_finite_data(data)
    cube = _validate_2d_gather(rsf.header, time_axis=time_axis, space_axis=space_axis)
    norm_value = _normalize_norm(norm)

    time = cube.axis(time_axis)
    space = cube.axis(space_axis)
    _validate_sampling(time, time_axis)
    _validate_sampling(space, space_axis)
    frequencies = centered_frequency_axis(time.n, time.d)
    wavenumbers = centered_frequency_axis(space.n, space.d)

    time_np = numpy_axis(time_axis, cube.ndim)
    space_np = numpy_axis(space_axis, cube.ndim)
    spectrum = _forward_fk(data, time_np=time_np, space_np=space_np, norm=norm_value)
    mask = make_fk_mask(
        frequencies,
        wavenumbers,
        vmin=vmin,
        vmax=vmax,
        taper=taper,
        reject=reject,
    )
    mask_nd = _reshape_mask(mask, data.ndim, time_np=time_np, space_np=space_np)
    filtered_spectrum = spectrum * mask_nd
    filtered = _inverse_fk(
        filtered_spectrum,
        time_np=time_np,
        space_np=space_np,
        norm=norm_value,
    )

    output = _cast_filtered_output(filtered, data)
    header = rsf.header.copy()
    _store_filter_metadata(header, vmin=vmin, vmax=vmax, taper=taper, reject=reject)
    return write_rsf(output_path, np.ascontiguousarray(output), header)


def make_fk_mask(
    frequencies: np.ndarray,
    wavenumbers: np.ndarray,
    *,
    vmin: float | None = None,
    vmax: float | None = None,
    taper: float = 0.0,
    reject: bool = False,
) -> np.ndarray:
    """Return an FK fan mask indexed as ``(wavenumber, frequency)``.

    Apparent velocity is defined as ``abs(frequency) / abs(wavenumber)`` using
    ordinary cycles per axis unit. With time in seconds and space in meters,
    the velocity unit is meters/second.
    """

    freq = np.asarray(frequencies, dtype=np.float64)
    wave = np.asarray(wavenumbers, dtype=np.float64)
    if freq.ndim != 1:
        raise FKError("frequencies must be a 1D array")
    if wave.ndim != 1:
        raise FKError("wavenumbers must be a 1D array")
    if not np.all(np.isfinite(freq)):
        raise FKError("frequencies must be finite")
    if not np.all(np.isfinite(wave)):
        raise FKError("wavenumbers must be finite")
    low = _optional_nonnegative(vmin, "vmin")
    high = _optional_nonnegative(vmax, "vmax")
    taper_width = float(taper)
    if not np.isfinite(taper_width):
        raise FKError("taper= must be finite")
    if taper_width < 0.0:
        raise FKError("taper= must be non-negative")
    if low is None and high is None:
        raise FKError("at least one of vmin= or vmax= is required")
    if low is not None and high is not None and low > high:
        raise FKError("vmin= must be smaller than or equal to vmax=")

    velocity = _apparent_velocity_grid(freq, wave)
    response = np.ones_like(velocity, dtype=np.float64)
    if low is not None:
        response *= _low_velocity_edge(velocity, low, taper_width)
    if high is not None:
        response *= _high_velocity_edge(velocity, high, taper_width)
    response = np.nan_to_num(response, nan=0.0, posinf=0.0, neginf=0.0)
    if reject:
        response = 1.0 - response
    return response.astype(np.float32)


def fk_axis_header_update(
    header: RSFHeader,
    *,
    time_axis: int = 1,
    space_axis: int = 2,
) -> RSFHeader:
    """Return a header with time/space axes converted to frequency/wavenumber."""

    cube = _validate_2d_gather(header, time_axis=time_axis, space_axis=space_axis)
    time = cube.axis(time_axis)
    space = cube.axis(space_axis)
    _validate_sampling(time, time_axis)
    _validate_sampling(space, space_axis)
    frequencies = centered_frequency_axis(time.n, time.d)
    wavenumbers = centered_frequency_axis(space.n, space.d)

    output = header.copy()
    _store_original_axis(output, time, time_axis)
    _store_original_axis(output, space, space_axis)
    transformed = cube.update_axis(
        time_axis,
        n=frequencies.size,
        o=float(frequencies[0]) if frequencies.size else 0.0,
        d=_axis_spacing(frequencies),
        label="Frequency",
        unit=_frequency_unit(time.unit),
    ).update_axis(
        space_axis,
        n=wavenumbers.size,
        o=float(wavenumbers[0]) if wavenumbers.size else 0.0,
        d=_axis_spacing(wavenumbers),
        label="Wavenumber",
        unit=_inverse_unit(space.unit),
    )
    return transformed.to_header(output)


def centered_frequency_axis(n: int, d: float) -> np.ndarray:
    """Return ``fftshift(fftfreq(n, d))`` as float64."""

    if int(n) < 1:
        raise FKError("axis length must be positive")
    spacing = float(d)
    if not np.isfinite(spacing) or spacing <= 0.0:
        raise FKError("axis sampling d= must be finite and positive")
    return np.fft.fftshift(np.fft.fftfreq(int(n), d=spacing)).astype(np.float64)


def _forward_fk(
    data: np.ndarray,
    *,
    time_np: int,
    space_np: int,
    norm: str | None,
) -> np.ndarray:
    complex_data = np.asarray(data, dtype=np.complex64)
    transformed = np.fft.fft2(complex_data, axes=(space_np, time_np), norm=norm)
    return np.fft.fftshift(transformed, axes=(space_np, time_np))


def _inverse_fk(
    spectrum: np.ndarray,
    *,
    time_np: int,
    space_np: int,
    norm: str | None,
) -> np.ndarray:
    shifted = np.fft.ifftshift(spectrum, axes=(space_np, time_np))
    return np.fft.ifft2(shifted, axes=(space_np, time_np), norm=norm)


def _cast_filtered_output(filtered: np.ndarray, input_data: np.ndarray) -> np.ndarray:
    dtype = output_dtype(input_data)
    if np.iscomplexobj(input_data):
        return filtered.astype(dtype)
    return filtered.real.astype(dtype)


def _validate_finite_data(data: np.ndarray) -> None:
    if not np.all(np.isfinite(data)):
        raise FKError("FK operations require finite input samples")


def _validate_2d_gather(
    header: RSFHeader,
    *,
    time_axis: int,
    space_axis: int,
) -> Hypercube:
    cube = Hypercube.from_header(header)
    if cube.ndim != 2:
        raise FKError(f"FK operations currently require 2D input, got {cube.ndim}D")
    validate_rsf_axis(time_axis, cube.ndim)
    validate_rsf_axis(space_axis, cube.ndim)
    if time_axis == space_axis:
        raise FKError("time_axis and space_axis must be different")
    return cube


def _validate_sampling(axis: Axis, axis_number: int) -> None:
    if not np.isfinite(float(axis.o)):
        raise FKError(f"o{axis_number}= must be finite")
    if not np.isfinite(float(axis.d)) or axis.d <= 0.0:
        raise FKError(f"d{axis_number}= must be finite and positive")


def _reshape_mask(mask: np.ndarray, ndim: int, *, time_np: int, space_np: int) -> np.ndarray:
    shape = [1] * ndim
    shape[space_np] = mask.shape[0]
    shape[time_np] = mask.shape[1]
    return mask.reshape(shape)


def _apparent_velocity_grid(freq: np.ndarray, wave: np.ndarray) -> np.ndarray:
    abs_freq = np.abs(freq).reshape(1, freq.size)
    abs_wave = np.abs(wave).reshape(wave.size, 1)
    velocity = np.full((wave.size, freq.size), np.inf, dtype=np.float64)
    np.divide(abs_freq, abs_wave, out=velocity, where=abs_wave > 0.0)
    velocity[(abs_wave == 0.0) & (abs_freq == 0.0)] = 0.0
    return velocity


def _low_velocity_edge(velocity: np.ndarray, cutoff: float, taper: float) -> np.ndarray:
    response = np.zeros_like(velocity, dtype=np.float64)
    if cutoff == 0.0 and taper == 0.0:
        response[:] = 1.0
        return response
    if taper == 0.0:
        response[velocity >= cutoff] = 1.0
        return response

    stop_end = max(0.0, cutoff - taper)
    response[velocity >= cutoff] = 1.0
    ramp = (velocity > stop_end) & (velocity < cutoff)
    denominator = cutoff - stop_end
    if denominator > 0.0:
        response[ramp] = 0.5 * (1.0 - np.cos(np.pi * (velocity[ramp] - stop_end) / denominator))
    return response


def _high_velocity_edge(velocity: np.ndarray, cutoff: float, taper: float) -> np.ndarray:
    response = np.zeros_like(velocity, dtype=np.float64)
    if taper == 0.0:
        response[velocity <= cutoff] = 1.0
        return response

    stop_start = cutoff + taper
    response[velocity <= cutoff] = 1.0
    ramp = (velocity > cutoff) & (velocity < stop_start)
    response[ramp] = 0.5 * (1.0 + np.cos(np.pi * (velocity[ramp] - cutoff) / taper))
    return response


def _optional_nonnegative(value: float | None, name: str) -> float | None:
    if value is None:
        return None
    number = float(value)
    if not np.isfinite(number):
        raise FKError(f"{name}= must be finite")
    if number < 0.0:
        raise FKError(f"{name}= must be non-negative")
    return number


def _axis_spacing(values: np.ndarray) -> float:
    return float(values[1] - values[0]) if values.size > 1 else 1.0


def _store_original_axis(header: RSFHeader, axis: Axis, axis_number: int) -> None:
    header[f"fk_n{axis_number}"] = axis.n
    header[f"fk_o{axis_number}"] = axis.o
    header[f"fk_d{axis_number}"] = axis.d
    if axis.label is not None:
        header[f"fk_label{axis_number}"] = axis.label
    if axis.unit is not None:
        header[f"fk_unit{axis_number}"] = axis.unit


def _store_spectrum_metadata(
    header: RSFHeader,
    *,
    amplitude: bool,
    norm: str | None,
) -> None:
    header["fk_algorithm"] = "numpy_fft2_centered"
    header["fk_reference_source"] = FK_REFERENCE_SOURCE
    header["fk_madagascar_equivalence"] = FK_DIRECT_SOURCE_STATUS
    header["fk_input_domain"] = "time_space"
    header["fk_output_domain"] = "frequency_wavenumber"
    header["fk_amplitude_output"] = "y" if amplitude else "n"
    header["fk_norm"] = "backward" if norm is None else norm


def _store_filter_metadata(
    header: RSFHeader,
    *,
    vmin: float | None,
    vmax: float | None,
    taper: float,
    reject: bool,
) -> None:
    header["fkfilter_algorithm"] = "raw_gather_fft_fan_filter"
    header["fkfilter_reference_source"] = FK_REFERENCE_SOURCE
    header["fkfilter_madagascar_equivalence"] = "not_sfdipfilter_clone"
    header["fkfilter_mask_velocity"] = "abs_frequency_over_abs_wavenumber"
    header["fkfilter_input_domain"] = "time_space"
    header["fkfilter_output_domain"] = "time_space"
    if vmin is not None:
        header["fkfilter_vmin"] = vmin
    if vmax is not None:
        header["fkfilter_vmax"] = vmax
    header["fkfilter_taper"] = taper
    header["fkfilter_reject"] = "y" if reject else "n"


def _frequency_unit(unit: str | None) -> str | None:
    if unit is None:
        return None
    if unit == "s":
        return "Hz"
    if unit.startswith("1/"):
        return unit[2:]
    return f"1/{unit}"


def _inverse_unit(unit: str | None) -> str | None:
    if unit is None:
        return None
    if unit.startswith("1/"):
        return unit[2:]
    return f"1/{unit}"


def _normalize_norm(norm: str | None) -> str | None:
    if norm in {None, "", "none"}:
        return None
    value = str(norm).strip().lower()
    if value in {"backward", "forward", "ortho"}:
        return value
    raise FKError("norm= must be backward, forward, ortho, or omitted")
