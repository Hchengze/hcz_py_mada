"""Internal deterministic fixtures for seismic signal-processing tests.

These helpers define small regular-grid trace, panel, and CMP-like gather
contracts. They are testing infrastructure, not stable public processing APIs.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import numpy as np

from pymadagascar.io.rsf import RSFArray, RSFHeader, format_from_dtype, write_rsf


DEFAULT_SEED = 20260614


class SeismicFixtureError(ValueError):
    """Raised when an S1 seismic fixture request violates its contract."""


def make_trace_fixture(
    *,
    nt: int = 512,
    dt: float = 0.004,
    o1: float = 0.0,
    frequency: float = 20.0,
    secondary_frequency: float = 70.0,
    secondary_amplitude: float = 0.25,
    noise_std: float = 0.02,
    trend: float = 0.08,
    seed: int = DEFAULT_SEED,
    amplitude_unit: str = "relative",
    dtype: Any = np.float32,
    path: str | os.PathLike[str] | None = None,
) -> RSFArray:
    """Return a mixed-frequency finite trace with a small linear trend."""

    nt_value, dt_value, origin = _time_geometry(nt, dt, o1)
    dtype_obj = _fixture_dtype(dtype)
    primary = _positive_finite(frequency, "frequency")
    secondary = _positive_finite(secondary_frequency, "secondary_frequency")
    secondary_scale = _finite(secondary_amplitude, "secondary_amplitude")
    noise = _nonnegative_finite(noise_std, "noise_std")
    trend_value = _finite(trend, "trend")
    unit = _nonempty(amplitude_unit, "amplitude_unit")
    _validate_nyquist(max(primary, secondary), dt_value)

    time = origin + dt_value * np.arange(nt_value, dtype=np.float64)
    centered = time - float(np.mean(time))
    rng = np.random.default_rng(int(seed))
    data = (
        np.sin(2.0 * np.pi * primary * time)
        + secondary_scale * np.sin(2.0 * np.pi * secondary * time + 0.35)
        + trend_value * centered
        + noise * rng.standard_normal(nt_value)
    )
    header = _trace_header(
        nt_value,
        dt_value,
        origin,
        dtype_obj,
        fixture_kind="mixed_frequency_trace",
        amplitude_unit=unit,
    )
    header["primary_frequency_hz"] = primary
    header["secondary_frequency_hz"] = secondary
    header["fixture_seed"] = int(seed)
    return _finish(data, header, dtype_obj, path)


def make_ricker_event_fixture(
    *,
    nt: int = 512,
    dt: float = 0.004,
    o1: float = 0.0,
    peak_time: float = 0.6,
    fpeak: float = 25.0,
    amplitude: float = 1.0,
    noise_std: float = 0.0,
    seed: int = DEFAULT_SEED,
    amplitude_unit: str = "relative",
    dtype: Any = np.float32,
    path: str | os.PathLike[str] | None = None,
) -> RSFArray:
    """Return one sampled Ricker event at a known physical time."""

    nt_value, dt_value, origin = _time_geometry(nt, dt, o1)
    dtype_obj = _fixture_dtype(dtype)
    peak = _time_inside(peak_time, nt_value, dt_value, origin, "peak_time")
    frequency = _positive_finite(fpeak, "fpeak")
    scale = _finite(amplitude, "amplitude")
    noise = _nonnegative_finite(noise_std, "noise_std")
    unit = _nonempty(amplitude_unit, "amplitude_unit")
    _validate_nyquist(frequency, dt_value)

    time = origin + dt_value * np.arange(nt_value, dtype=np.float64)
    data = scale * _ricker(time - peak, frequency)
    if noise:
        data += noise * np.random.default_rng(int(seed)).standard_normal(nt_value)
    header = _trace_header(
        nt_value,
        dt_value,
        origin,
        dtype_obj,
        fixture_kind="ricker_event_trace",
        amplitude_unit=unit,
    )
    header["event_peak_time_s"] = peak
    header["event_peak_frequency_hz"] = frequency
    header["fixture_seed"] = int(seed)
    return _finish(data, header, dtype_obj, path)


def make_panel_fixture(
    *,
    nchannel: int = 12,
    nt: int = 512,
    dt: float = 0.004,
    o1: float = 0.0,
    channel_o: float = 0.0,
    channel_d: float = 12.5,
    event_time: float = 0.6,
    fpeak: float = 25.0,
    noise_std: float = 0.04,
    seed: int = DEFAULT_SEED,
    amplitude_unit: str = "relative",
    dtype: Any = np.float32,
    path: str | os.PathLike[str] | None = None,
) -> RSFArray:
    """Return a regular channel panel with one coherent Ricker event."""

    channel_count, spacing, channel_origin = _regular_axis(
        nchannel,
        channel_d,
        channel_o,
        size_name="nchannel",
        spacing_name="channel_d",
        origin_name="channel_o",
    )
    nt_value, dt_value, origin = _time_geometry(nt, dt, o1)
    dtype_obj = _fixture_dtype(dtype)
    event = _time_inside(event_time, nt_value, dt_value, origin, "event_time")
    frequency = _positive_finite(fpeak, "fpeak")
    noise = _nonnegative_finite(noise_std, "noise_std")
    unit = _nonempty(amplitude_unit, "amplitude_unit")
    _validate_nyquist(frequency, dt_value)

    time = origin + dt_value * np.arange(nt_value, dtype=np.float64)
    amplitudes = 1.0 + 0.08 * np.cos(np.arange(channel_count, dtype=np.float64))
    data = amplitudes[:, None] * _ricker(time[None, :] - event, frequency)
    if noise:
        data += noise * np.random.default_rng(int(seed)).standard_normal(data.shape)
    header = _panel_header(
        nt_value,
        dt_value,
        origin,
        channel_count,
        channel_origin,
        spacing,
        dtype_obj,
        fixture_kind="regular_channel_panel",
        axis2_label="Channel",
        axis2_unit="m",
        axis2_role="channel_coordinate",
        amplitude_unit=unit,
    )
    header["event_peak_time_s"] = event
    header["event_peak_frequency_hz"] = frequency
    header["fixture_seed"] = int(seed)
    return _finish(data, header, dtype_obj, path)


def make_plane_wave_panel_fixture(
    *,
    nchannel: int = 24,
    nt: int = 512,
    dt: float = 0.002,
    o1: float = 0.0,
    channel_o: float = -115.0,
    channel_d: float = 10.0,
    intercept_time: float = 0.45,
    apparent_velocity: float = 1500.0,
    fpeak: float = 30.0,
    noise_std: float = 0.01,
    seed: int = DEFAULT_SEED,
    amplitude_unit: str = "relative",
    dtype: Any = np.float32,
    path: str | os.PathLike[str] | None = None,
) -> RSFArray:
    """Return a regular panel with a known signed linear moveout slope."""

    channel_count, spacing, channel_origin = _regular_axis(
        nchannel,
        channel_d,
        channel_o,
        size_name="nchannel",
        spacing_name="channel_d",
        origin_name="channel_o",
    )
    nt_value, dt_value, origin = _time_geometry(nt, dt, o1)
    dtype_obj = _fixture_dtype(dtype)
    intercept = _finite(intercept_time, "intercept_time")
    velocity = _positive_finite(apparent_velocity, "apparent_velocity")
    frequency = _positive_finite(fpeak, "fpeak")
    noise = _nonnegative_finite(noise_std, "noise_std")
    unit = _nonempty(amplitude_unit, "amplitude_unit")
    _validate_nyquist(frequency, dt_value)

    channel = channel_origin + spacing * np.arange(channel_count, dtype=np.float64)
    arrivals = intercept + channel / velocity
    _times_inside(arrivals, nt_value, dt_value, origin, "plane-wave arrivals")
    time = origin + dt_value * np.arange(nt_value, dtype=np.float64)
    data = _ricker(time[None, :] - arrivals[:, None], frequency)
    if noise:
        data += noise * np.random.default_rng(int(seed)).standard_normal(data.shape)
    header = _panel_header(
        nt_value,
        dt_value,
        origin,
        channel_count,
        channel_origin,
        spacing,
        dtype_obj,
        fixture_kind="plane_wave_panel",
        axis2_label="Channel X",
        axis2_unit="m",
        axis2_role="channel_coordinate",
        amplitude_unit=unit,
    )
    header["plane_wave_intercept_time_s"] = intercept
    header["plane_wave_apparent_velocity_m_per_s"] = velocity
    header["plane_wave_slowness_s_per_m"] = 1.0 / velocity
    header["event_peak_frequency_hz"] = frequency
    header["fixture_seed"] = int(seed)
    return _finish(data, header, dtype_obj, path)


def make_hyperbolic_gather_fixture(
    *,
    ntrace: int = 21,
    nt: int = 512,
    dt: float = 0.004,
    o1: float = 0.0,
    offset_o: float = -500.0,
    offset_d: float = 50.0,
    t0: float = 0.45,
    velocity: float = 2200.0,
    fpeak: float = 24.0,
    interference_frequency: float = 70.0,
    interference_amplitude: float = 0.20,
    noise_std: float = 0.04,
    trend: float = 0.06,
    seed: int = DEFAULT_SEED,
    amplitude_unit: str = "relative",
    dtype: Any = np.float32,
    path: str | os.PathLike[str] | None = None,
) -> RSFArray:
    """Return a regular signed-offset CMP-like gather with known moveout."""

    trace_count, spacing, offset_origin = _regular_axis(
        ntrace,
        offset_d,
        offset_o,
        size_name="ntrace",
        spacing_name="offset_d",
        origin_name="offset_o",
    )
    nt_value, dt_value, origin = _time_geometry(nt, dt, o1)
    dtype_obj = _fixture_dtype(dtype)
    zero_offset_time = _positive_finite(t0, "t0")
    moveout_velocity = _positive_finite(velocity, "velocity")
    frequency = _positive_finite(fpeak, "fpeak")
    interference = _positive_finite(
        interference_frequency,
        "interference_frequency",
    )
    interference_scale = _nonnegative_finite(
        interference_amplitude,
        "interference_amplitude",
    )
    noise = _nonnegative_finite(noise_std, "noise_std")
    trend_value = _finite(trend, "trend")
    unit = _nonempty(amplitude_unit, "amplitude_unit")
    _validate_nyquist(max(frequency, interference), dt_value)

    offsets = offset_origin + spacing * np.arange(trace_count, dtype=np.float64)
    arrivals = np.sqrt(zero_offset_time**2 + np.square(offsets / moveout_velocity))
    _times_inside(arrivals, nt_value, dt_value, origin, "hyperbolic arrivals")
    time = origin + dt_value * np.arange(nt_value, dtype=np.float64)
    amplitudes = 1.0 / np.sqrt(1.0 + np.abs(offsets) / 500.0)
    event = amplitudes[:, None] * _ricker(
        time[None, :] - arrivals[:, None],
        frequency,
    )
    phases = 0.23 * np.arange(trace_count, dtype=np.float64)
    high_frequency = interference_scale * np.sin(
        2.0 * np.pi * interference * time[None, :] + phases[:, None]
    )
    centered_time = time - float(np.mean(time))
    trace_bias = 0.03 * np.linspace(-1.0, 1.0, trace_count, dtype=np.float64)
    data = event + high_frequency + trend_value * centered_time + trace_bias[:, None]
    if noise:
        data += noise * np.random.default_rng(int(seed)).standard_normal(data.shape)

    header = _panel_header(
        nt_value,
        dt_value,
        origin,
        trace_count,
        offset_origin,
        spacing,
        dtype_obj,
        fixture_kind="hyperbolic_cmp_gather",
        axis2_label="Offset",
        axis2_unit="m",
        axis2_role="signed_offset",
        amplitude_unit=unit,
    )
    header["offset_sign_convention"] = "receiver_minus_source"
    header["offset_geometry"] = "regular_signed"
    header["source_receiver_geometry"] = "not_encoded"
    header["trace_header_model"] = "ordinary_rsf_only"
    header["event_t0_s"] = zero_offset_time
    header["event_velocity_m_per_s"] = moveout_velocity
    header["event_peak_frequency_hz"] = frequency
    header["interference_frequency_hz"] = interference
    header["fixture_seed"] = int(seed)
    return _finish(data, header, dtype_obj, path)


def _trace_header(
    nt: int,
    dt: float,
    origin: float,
    dtype: np.dtype[Any],
    *,
    fixture_kind: str,
    amplitude_unit: str,
) -> RSFHeader:
    return RSFHeader(
        {
            "n1": nt,
            "o1": origin,
            "d1": dt,
            "label1": "Time",
            "unit1": "s",
            "data_format": format_from_dtype(dtype),
            "esize": dtype.itemsize,
            "fixture_kind": fixture_kind,
            "fixture_scope": "internal_testing",
            "finite_value_policy": "required",
            "amplitude_unit": amplitude_unit,
        }
    )


def _panel_header(
    nt: int,
    dt: float,
    time_origin: float,
    n2: int,
    o2: float,
    d2: float,
    dtype: np.dtype[Any],
    *,
    fixture_kind: str,
    axis2_label: str,
    axis2_unit: str,
    axis2_role: str,
    amplitude_unit: str,
) -> RSFHeader:
    header = _trace_header(
        nt,
        dt,
        time_origin,
        dtype,
        fixture_kind=fixture_kind,
        amplitude_unit=amplitude_unit,
    )
    header["n2"] = n2
    header["o2"] = o2
    header["d2"] = d2
    header["label2"] = axis2_label
    header["unit2"] = axis2_unit
    header["axis2_role"] = axis2_role
    header["coordinate_sampling"] = "regular"
    return header


def _finish(
    data: np.ndarray,
    header: RSFHeader,
    dtype: np.dtype[Any],
    path: str | os.PathLike[str] | None,
) -> RSFArray:
    output = np.ascontiguousarray(np.asarray(data, dtype=dtype))
    if not bool(np.all(np.isfinite(output))):
        raise SeismicFixtureError("fixture generation produced non-finite samples")
    if path is None:
        return RSFArray(output, header)
    return write_rsf(Path(path), output, header)


def _ricker(relative_time: np.ndarray, frequency: float) -> np.ndarray:
    argument = np.pi * frequency * relative_time
    squared = argument * argument
    return (1.0 - 2.0 * squared) * np.exp(-squared)


def _time_geometry(nt: int, dt: float, o1: float) -> tuple[int, float, float]:
    count = _positive_int(nt, "nt")
    spacing = _positive_finite(dt, "dt")
    origin = _finite(o1, "o1")
    return count, spacing, origin


def _regular_axis(
    size: int,
    spacing: float,
    origin: float,
    *,
    size_name: str,
    spacing_name: str,
    origin_name: str,
) -> tuple[int, float, float]:
    count = _positive_int(size, size_name)
    step = _positive_finite(spacing, spacing_name)
    start = _finite(origin, origin_name)
    return count, step, start


def _fixture_dtype(dtype: Any) -> np.dtype[Any]:
    try:
        value = np.dtype(dtype)
    except (TypeError, ValueError) as exc:
        raise SeismicFixtureError("dtype must be float32 or float64") from exc
    if value not in {np.dtype("float32"), np.dtype("float64")}:
        raise SeismicFixtureError("dtype must be float32 or float64")
    return value


def _time_inside(
    value: float,
    nt: int,
    dt: float,
    origin: float,
    name: str,
) -> float:
    result = _finite(value, name)
    _times_inside(np.asarray([result]), nt, dt, origin, name)
    return result


def _times_inside(
    values: np.ndarray,
    nt: int,
    dt: float,
    origin: float,
    name: str,
) -> None:
    start = origin
    stop = origin + (nt - 1) * dt
    if not bool(np.all(np.isfinite(values))) or bool(
        np.any((values < start) | (values > stop))
    ):
        raise SeismicFixtureError(
            f"{name} must lie inside sampled time range [{start:g}, {stop:g}]"
        )


def _validate_nyquist(frequency: float, dt: float) -> None:
    nyquist = 0.5 / dt
    if frequency >= nyquist:
        raise SeismicFixtureError(
            f"fixture frequency {frequency:g} must be below Nyquist {nyquist:g}"
        )


def _positive_int(value: int, name: str) -> int:
    result = int(value)
    if result < 1:
        raise SeismicFixtureError(f"{name} must be positive")
    return result


def _finite(value: float, name: str) -> float:
    result = float(value)
    if not np.isfinite(result):
        raise SeismicFixtureError(f"{name} must be finite")
    return result


def _positive_finite(value: float, name: str) -> float:
    result = _finite(value, name)
    if result <= 0.0:
        raise SeismicFixtureError(f"{name} must be positive")
    return result


def _nonnegative_finite(value: float, name: str) -> float:
    result = _finite(value, name)
    if result < 0.0:
        raise SeismicFixtureError(f"{name} must be non-negative")
    return result


def _nonempty(value: str, name: str) -> str:
    result = str(value).strip()
    if not result:
        raise SeismicFixtureError(f"{name} must not be empty")
    return result


__all__ = [
    "SeismicFixtureError",
    "make_hyperbolic_gather_fixture",
    "make_panel_fixture",
    "make_plane_wave_panel_fixture",
    "make_ricker_event_fixture",
    "make_trace_fixture",
]
