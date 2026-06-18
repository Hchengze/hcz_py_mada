"""Internal metrics for deterministic seismic pipeline regressions.

The functions in this module support topic-level tests and workflows. They are
not stable public processing APIs or production QC definitions.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import json
import os
from pathlib import Path
from typing import Any

import numpy as np

from pymadagascar.io.rsf import RSFArray
from pymadagascar.signal.fir import band_energy
from pymadagascar.signal.spectral import frequency_attributes


SampleWindow = tuple[int, int]
FrequencyBand = tuple[float, float]


class SeismicMetricsError(ValueError):
    """Raised when an internal seismic metric request is invalid."""


def compute_trace_metrics(
    data: Any,
    *,
    dt: float,
    signal_window: SampleWindow,
    noise_window: SampleWindow,
    target_band: FrequencyBand = (15.0, 35.0),
    reject_band: FrequencyBand = (60.0, 80.0),
) -> dict[str, float]:
    """Compute deterministic scalar metrics for one finite real trace."""

    array = _finite_real_array(data, ndim=1, name="trace")
    return _signal_metrics(
        array,
        dt=dt,
        signal_window=signal_window,
        noise_window=noise_window,
        target_band=target_band,
        reject_band=reject_band,
    )


def compute_panel_metrics(
    data: Any,
    *,
    dt: float,
    signal_window: SampleWindow,
    noise_window: SampleWindow,
    target_band: FrequencyBand = (15.0, 35.0),
    reject_band: FrequencyBand = (60.0, 80.0),
) -> dict[str, float]:
    """Compute aggregate metrics for a ``(trace, time)`` finite real panel."""

    array = _finite_real_array(data, ndim=2, name="panel")
    return _signal_metrics(
        array,
        dt=dt,
        signal_window=signal_window,
        noise_window=noise_window,
        target_band=target_band,
        reject_band=reject_band,
    )


def compute_gather_pipeline_metrics(
    raw: RSFArray,
    before_filter: RSFArray,
    after_filter: RSFArray,
    processed: RSFArray,
    stack: RSFArray,
    *,
    signal_window: SampleWindow,
    noise_window: SampleWindow,
    target_band: FrequencyBand = (15.0, 35.0),
    reject_band: FrequencyBand = (60.0, 80.0),
    mute_t0: float = 0.080,
    mute_velocity: float = 4000.0,
) -> dict[str, float | bool]:
    """Summarize the S2 regular-gather processing stages.

    SNR and frequency metrics compare ``before_filter`` with ``after_filter``.
    Final output, mute, and stack metrics use ``processed`` and ``stack``.
    """

    gather_items = (raw, before_filter, after_filter, processed)
    gather_arrays = [
        _finite_real_array(item.data, ndim=2, name=name)
        for item, name in zip(
            gather_items,
            ("raw", "before_filter", "after_filter", "processed"),
        )
    ]
    if any(array.shape != gather_arrays[0].shape for array in gather_arrays[1:]):
        raise SeismicMetricsError("all gather stages must have identical shapes")
    stack_array = _finite_real_array(stack.data, ndim=1, name="stack")
    if stack_array.size != gather_arrays[0].shape[-1]:
        raise SeismicMetricsError("stack length must match the gather time axis")

    dt = _positive_finite(_header_float(raw, "d1"), "d1")
    time_origin = _finite(_header_float(raw, "o1", default=0.0), "o1")
    before = compute_panel_metrics(
        before_filter.data,
        dt=dt,
        signal_window=signal_window,
        noise_window=noise_window,
        target_band=target_band,
        reject_band=reject_band,
    )
    after = compute_panel_metrics(
        after_filter.data,
        dt=dt,
        signal_window=signal_window,
        noise_window=noise_window,
        target_band=target_band,
        reject_band=reject_band,
    )
    final_panel = compute_panel_metrics(
        processed.data,
        dt=dt,
        signal_window=signal_window,
        noise_window=noise_window,
        target_band=target_band,
        reject_band=reject_band,
    )
    stacked = compute_trace_metrics(
        stack.data,
        dt=dt,
        signal_window=signal_window,
        noise_window=noise_window,
        target_band=target_band,
        reject_band=reject_band,
    )

    target_ratio = _ratio(
        after["target_band_energy"],
        before["target_band_energy"],
    )
    reject_ratio = _ratio(
        after["reject_band_energy"],
        before["reject_band_energy"],
    )
    stack_noise_ratio = _ratio(
        stacked["noise_window_rms"],
        final_panel["noise_window_rms"],
    )

    mute_speed = _positive_finite(mute_velocity, "mute_velocity")
    mute_origin = _finite(mute_t0, "mute_t0")
    offset_origin = _header_float(raw, "o2")
    offset_spacing = _positive_finite(_header_float(raw, "d2"), "d2")
    offsets = offset_origin + offset_spacing * np.arange(
        gather_arrays[0].shape[0],
        dtype=np.float64,
    )
    times = time_origin + dt * np.arange(
        gather_arrays[0].shape[1],
        dtype=np.float64,
    )
    muted = times[None, :] < (
        mute_origin + np.abs(offsets[:, None]) / mute_speed
    )
    muted_fraction = float(np.mean(muted))
    mute_zero_fraction = (
        float(np.mean(np.abs(gather_arrays[-1][muted]) <= 1.0e-8))
        if bool(np.any(muted))
        else 1.0
    )

    signal_slice = _window_slice(
        signal_window,
        stack_array.size,
        "signal_window",
    )
    peak_index = signal_slice.start + int(
        np.argmax(np.abs(stack_array[signal_slice]))
    )
    finite_count = sum(np.count_nonzero(np.isfinite(array)) for array in gather_arrays)
    finite_count += int(np.count_nonzero(np.isfinite(stack_array)))
    sample_count = sum(array.size for array in gather_arrays) + stack_array.size

    return {
        "input_rms": _rms(gather_arrays[0]),
        "output_rms": _rms(gather_arrays[-1]),
        "noise_window_rms_before": before["noise_window_rms"],
        "noise_window_rms_after": after["noise_window_rms"],
        "signal_window_rms_before": before["signal_window_rms"],
        "signal_window_rms_after": after["signal_window_rms"],
        "snr_before_db": before["snr_db"],
        "snr_after_db": after["snr_db"],
        "snr_improvement_db": after["snr_db"] - before["snr_db"],
        "stack_peak_time": time_origin + peak_index * dt,
        "stack_peak_amplitude": float(stack_array[peak_index]),
        "stack_signal_window_rms": stacked["signal_window_rms"],
        "stack_noise_window_rms": stacked["noise_window_rms"],
        "stack_snr_db": stacked["snr_db"],
        "dominant_frequency_before": before["dominant_frequency"],
        "dominant_frequency_after": after["dominant_frequency"],
        "target_band_energy_before": before["target_band_energy"],
        "target_band_energy_after": after["target_band_energy"],
        "target_band_energy_ratio": target_ratio,
        "reject_band_energy_before": before["reject_band_energy"],
        "reject_band_energy_after": after["reject_band_energy"],
        "reject_band_energy_ratio": reject_ratio,
        "processed_noise_window_rms": final_panel["noise_window_rms"],
        "stack_noise_reduction_ratio": stack_noise_ratio,
        "finite_fraction": float(finite_count / sample_count),
        "muted_fraction": muted_fraction,
        "mute_zero_fraction": mute_zero_fraction,
        "header_axis_ok": _pipeline_headers_ok(
            raw,
            before_filter,
            after_filter,
            processed,
            stack,
        ),
    }


def compare_pipeline_metrics(
    metrics: Mapping[str, Any],
    *,
    min_snr_improvement_db: float = 6.0,
    target_band_ratio: tuple[float, float] = (0.75, 1.10),
    max_reject_band_ratio: float = 0.02,
    max_stack_noise_ratio: float = 0.45,
) -> dict[str, bool]:
    """Apply broad S2 regression thresholds to a metrics mapping."""

    required = {
        "snr_improvement_db",
        "target_band_energy_ratio",
        "reject_band_energy_ratio",
        "stack_noise_reduction_ratio",
        "finite_fraction",
        "muted_fraction",
        "mute_zero_fraction",
        "header_axis_ok",
    }
    missing = sorted(required - set(metrics))
    if missing:
        raise SeismicMetricsError("missing pipeline metrics: " + ", ".join(missing))

    lower, upper = target_band_ratio
    if not np.isfinite(lower) or not np.isfinite(upper) or lower > upper:
        raise SeismicMetricsError("target_band_ratio must be a finite ordered pair")
    checks = {
        "snr_improved": _metric_float(metrics, "snr_improvement_db")
        >= _finite(min_snr_improvement_db, "min_snr_improvement_db"),
        "target_band_preserved": lower
        <= _metric_float(metrics, "target_band_energy_ratio")
        <= upper,
        "reject_band_attenuated": _metric_float(
            metrics,
            "reject_band_energy_ratio",
        )
        <= _nonnegative_finite(max_reject_band_ratio, "max_reject_band_ratio"),
        "stack_noise_reduced": _metric_float(
            metrics,
            "stack_noise_reduction_ratio",
        )
        <= _nonnegative_finite(max_stack_noise_ratio, "max_stack_noise_ratio"),
        "mute_applied": (
            _metric_float(metrics, "muted_fraction") > 0.0
            and _metric_float(metrics, "mute_zero_fraction") >= 0.999
        ),
        "finite": np.isclose(_metric_float(metrics, "finite_fraction"), 1.0),
        "header_axis_ok": bool(metrics["header_axis_ok"]),
    }
    checks["overall_pass"] = bool(all(checks.values()))
    return checks


def write_metrics_json(
    path: str | os.PathLike[str],
    report: Mapping[str, Any],
) -> Path:
    """Write deterministic, finite JSON without serializing path objects."""

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    ready = _json_ready(report)
    output.write_text(
        json.dumps(ready, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return output


def _signal_metrics(
    array: np.ndarray,
    *,
    dt: float,
    signal_window: SampleWindow,
    noise_window: SampleWindow,
    target_band: FrequencyBand,
    reject_band: FrequencyBand,
) -> dict[str, float]:
    sample_interval = _positive_finite(dt, "dt")
    signal_slice = _window_slice(signal_window, array.shape[-1], "signal_window")
    noise_slice = _window_slice(noise_window, array.shape[-1], "noise_window")
    if max(signal_slice.start, noise_slice.start) < min(
        signal_slice.stop,
        noise_slice.stop,
    ):
        raise SeismicMetricsError("signal_window and noise_window must not overlap")
    target = _frequency_band(target_band, sample_interval, "target_band")
    reject = _frequency_band(reject_band, sample_interval, "reject_band")

    signal_rms = _rms(array[..., signal_slice])
    noise_rms = _rms(array[..., noise_slice])
    epsilon = np.finfo(np.float64).eps
    snr_db = 20.0 * np.log10(max(signal_rms / max(noise_rms, epsilon), epsilon))
    energies = band_energy(
        array,
        sample_interval,
        (target, reject),
        axis=1,
        mode="energy",
        average=True,
    )
    dominant = frequency_attributes(
        array,
        sample_interval,
        axis=1,
        input_kind="signal",
        attrs=("dominant",),
    )
    return {
        "rms": _rms(array),
        "signal_window_rms": signal_rms,
        "noise_window_rms": noise_rms,
        "snr_db": float(snr_db),
        "dominant_frequency": float(np.mean(dominant, dtype=np.float64)),
        "target_band_energy": float(np.asarray(energies)[0]),
        "reject_band_energy": float(np.asarray(energies)[1]),
        "finite_fraction": 1.0,
    }


def _pipeline_headers_ok(
    raw: RSFArray,
    before_filter: RSFArray,
    after_filter: RSFArray,
    processed: RSFArray,
    stack: RSFArray,
) -> bool:
    try:
        reference = raw.header
        if raw.data.ndim != 2 or reference.shape != raw.data.shape:
            return False
        if (
            reference.get("label1") != "Time"
            or reference.get("unit1") != "s"
            or reference.get("label2") != "Offset"
            or reference.get("unit2") != "m"
            or reference.get("axis2_role") != "signed_offset"
            or reference.get("coordinate_sampling") != "regular"
        ):
            return False
        for item in (before_filter, after_filter, processed):
            if item.data.shape != raw.data.shape or item.header.shape != raw.data.shape:
                return False
            for key in (
                "n1",
                "o1",
                "d1",
                "label1",
                "unit1",
                "n2",
                "o2",
                "d2",
                "label2",
                "unit2",
                "axis2_role",
                "coordinate_sampling",
            ):
                if item.header.get(key) != reference.get(key):
                    return False
        return bool(
            stack.data.ndim == 1
            and stack.data.size == raw.data.shape[-1]
            and stack.header.shape == stack.data.shape
            and stack.header.get("n1") == reference.get("n1")
            and stack.header.get("o1") == reference.get("o1")
            and stack.header.get("d1") == reference.get("d1")
            and stack.header.get("label1") == "Time"
            and stack.header.get("unit1") == "s"
        )
    except (KeyError, TypeError, ValueError):
        return False


def _finite_real_array(data: Any, *, ndim: int, name: str) -> np.ndarray:
    array = np.asarray(data)
    if array.ndim != ndim or array.size == 0:
        raise SeismicMetricsError(f"{name} must be a non-empty {ndim}D array")
    if array.dtype.kind not in {"f", "i", "u"} or np.iscomplexobj(array):
        raise SeismicMetricsError(f"{name} must contain real numeric samples")
    if not bool(np.all(np.isfinite(array))):
        raise SeismicMetricsError(f"{name} must contain only finite samples")
    return np.asarray(array, dtype=np.float64)


def _window_slice(value: Sequence[int], length: int, name: str) -> slice:
    if len(value) != 2:
        raise SeismicMetricsError(f"{name} must contain start and stop samples")
    start, stop = int(value[0]), int(value[1])
    if start < 0 or stop <= start or stop > length:
        raise SeismicMetricsError(
            f"{name} must satisfy 0 <= start < stop <= {length}"
        )
    return slice(start, stop)


def _frequency_band(
    value: Sequence[float],
    dt: float,
    name: str,
) -> FrequencyBand:
    if len(value) != 2:
        raise SeismicMetricsError(f"{name} must contain low and high frequencies")
    low = _nonnegative_finite(value[0], f"{name} low")
    high = _positive_finite(value[1], f"{name} high")
    nyquist = 0.5 / dt
    if low >= high or high >= nyquist:
        raise SeismicMetricsError(
            f"{name} must satisfy 0 <= low < high < Nyquist ({nyquist:g})"
        )
    return low, high


def _header_float(
    item: RSFArray,
    key: str,
    *,
    default: float | None = None,
) -> float:
    value = item.header.get(key, default)
    if value is None:
        raise SeismicMetricsError(f"RSF header is missing {key}")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise SeismicMetricsError(f"RSF header {key} must be numeric") from exc


def _metric_float(metrics: Mapping[str, Any], key: str) -> float:
    return _finite(metrics[key], key)


def _ratio(numerator: float, denominator: float) -> float:
    return float(numerator / max(denominator, np.finfo(np.float64).eps))


def _rms(array: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(array), dtype=np.float64)))


def _finite(value: Any, name: str) -> float:
    result = float(value)
    if not np.isfinite(result):
        raise SeismicMetricsError(f"{name} must be finite")
    return result


def _positive_finite(value: Any, name: str) -> float:
    result = _finite(value, name)
    if result <= 0.0:
        raise SeismicMetricsError(f"{name} must be positive")
    return result


def _nonnegative_finite(value: Any, name: str) -> float:
    result = _finite(value, name)
    if result < 0.0:
        raise SeismicMetricsError(f"{name} must be non-negative")
    return result


def _json_ready(value: Any) -> Any:
    if isinstance(value, Path):
        raise SeismicMetricsError("metrics JSON must not contain Path objects")
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if isinstance(value, np.generic):
        return _json_ready(value.item())
    if isinstance(value, float) and not np.isfinite(value):
        raise SeismicMetricsError("metrics JSON must contain only finite numbers")
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise SeismicMetricsError(
        f"metrics JSON value has unsupported type {type(value).__name__}"
    )


__all__ = [
    "SeismicMetricsError",
    "compare_pipeline_metrics",
    "compute_gather_pipeline_metrics",
    "compute_panel_metrics",
    "compute_trace_metrics",
    "write_metrics_json",
]
