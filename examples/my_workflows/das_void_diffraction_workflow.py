"""Synthetic DAS road-void diffraction workflow.

This is a workflow-only kinematic prototype. It does not model elastic waves,
fiber coupling, gauge length, or production DAS acquisition.
"""

from __future__ import annotations

from collections.abc import Sequence
import csv
from dataclasses import asdict, dataclass
import json
from pathlib import Path

import numpy as np

from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf
from pymadagascar.localization import (
    diffraction_travel_time_2d,
    grid_search_point_location_velocity_2d,
)
from pymadagascar.plot._common import pyplot
from pymadagascar.plot.grey import grey
from pymadagascar.seismic.fk import fk_filter
from pymadagascar.signal.wavelet import ricker_wavelet

from _common import parse_output_dir, print_outputs


@dataclass(frozen=True)
class SyntheticGeometry:
    source_x: float = -6.0
    void_x: float = 17.5
    void_depth: float = 2.5
    vr: float = 240.0
    channel_count: int = 72
    channel_spacing: float = 0.5
    sample_count: int = 480
    dt: float = 0.0005
    fpeak: float = 45.0
    noise_std: float = 0.025
    seed: int = 20260613


@dataclass(frozen=True)
class InversionResult:
    void_x: float
    void_depth: float
    vr: float
    rmse: float


def build_das_geometry_metadata(
    geometry: SyntheticGeometry,
    receiver_x: np.ndarray,
) -> dict[str, object]:
    """Return JSON-safe workflow-only DAS geometry metadata.

    The contract is deliberately small and local to this workflow. It records
    the synthetic regular-linear fiber geometry used by D-1/D-2A without
    promoting a stable DAS API or modeling gauge-length strain response.
    """

    receivers = np.asarray(receiver_x, dtype=np.float64).reshape(-1)
    if receivers.size != geometry.channel_count:
        raise ValueError("receiver_x size must match channel_count")
    if receivers.size == 0 or not np.all(np.isfinite(receivers)):
        raise ValueError("receiver_x must contain finite channel coordinates")

    channel_start = float(receivers[0])
    channel_stop = float(receivers[-1])
    expected_stop = channel_start + geometry.channel_spacing * (geometry.channel_count - 1)
    if not np.isclose(channel_stop, expected_stop):
        raise ValueError("receiver_x must describe a regular channel axis")

    return {
        "schema": "pymadagascar_workflow_das_geometry_v1",
        "geometry_kind": "regular_linear_das",
        "coordinate_frame": "local_2d",
        "distance_unit": "m",
        "time_unit": "s",
        "channel_count": int(geometry.channel_count),
        "channel_spacing": float(geometry.channel_spacing),
        "channel_start": channel_start,
        "channel_stop": channel_stop,
        "channel_axis_role": "fiber_channel",
        "fiber_origin_x": channel_start,
        "fiber_origin_y": 0.0,
        "fiber_orientation_degrees": 0.0,
        "fiber_x_start": channel_start,
        "fiber_x_stop": channel_stop,
        "source_x": float(geometry.source_x),
        "source_y": 0.0,
        "source_kind": "synthetic_impact",
        "gauge_length": None,
        "gauge_length_status": "not_modeled",
        "void_x": float(geometry.void_x),
        "void_depth": float(geometry.void_depth),
        "void_depth_positive": "down",
        "receiver_coordinate_convention": (
            "channel coordinate increases along fiber orientation"
        ),
        "sample_count": int(geometry.sample_count),
        "sample_interval": float(geometry.dt),
        "time_start": 0.0,
        "time_stop": float((geometry.sample_count - 1) * geometry.dt),
    }


def build_localization_algorithm_metadata() -> dict[str, object]:
    """Return JSON-safe metadata for the package-level localization prototype."""

    return {
        "module": "pymadagascar.localization.traveltime",
        "method": "grid_search_point_location_velocity_2d",
        "travel_time_model": "source_diffractor_receiver_kinematic",
        "velocity_mode": "closed_form_slowness",
        "residual_convention": "observed_minus_predicted",
        "coordinate_frame": "local_2d_x_z",
        "depth_positive": "down",
        "objective": "0.5_sum_weighted_squared_residuals",
        "prototype": True,
        "field_ready": False,
        "automatic_picking": False,
        "das_adapter": False,
        "gauge_response": False,
        "stable_root_api": False,
        "cli": False,
    }


def main(argv: Sequence[str] | None = None) -> int:
    output_dir = parse_output_dir("das_void_diffraction", argv)
    geometry = SyntheticGeometry()
    receiver_x = geometry.channel_spacing * np.arange(geometry.channel_count, dtype=np.float64)

    raw_tc, direct_times, diffraction_times = _synthetic_das_shot(geometry, receiver_x)
    raw_ct = np.ascontiguousarray(raw_tc.T)
    header = _gather_header(geometry)

    raw_path = output_dir / "das_void_raw.rsf"
    filtered_path = output_dir / "das_void_fk_filtered.rsf"
    raw_png = output_dir / "das_void_raw.png"
    filtered_png = output_dir / "das_void_fk_filtered_with_curves.png"
    picks_path = output_dir / "das_void_diffraction_picks.csv"
    result_path = output_dir / "das_void_inversion.json"

    write_rsf(raw_path, raw_ct, header)
    fk_filter(
        raw_path,
        filtered_path,
        vmin=1.25 * geometry.vr,
        vmax=5.0 * geometry.vr,
        taper=0.25 * geometry.vr,
        time_axis=1,
        space_axis=2,
    )
    filtered = read_rsf(filtered_path)

    pick_indices = np.arange(1, geometry.channel_count - 1, 3, dtype=np.int64)
    pick_x = receiver_x[pick_indices]
    rng = np.random.default_rng(geometry.seed + 1)
    pick_times = diffraction_times[pick_indices] + rng.normal(0.0, 0.00025, pick_indices.size)
    inversion = _invert_diffraction_picks(
        pick_x,
        pick_times,
        source_x=geometry.source_x,
        x_bounds=(float(receiver_x[0]), float(receiver_x[-1])),
        depth_bounds=(0.5, 6.0),
        velocity_bounds=(150.0, 400.0),
    )
    inverted_times = _diffraction_travel_times(
        receiver_x,
        source_x=geometry.source_x,
        void_x=inversion.void_x,
        void_depth=inversion.void_depth,
        vr=inversion.vr,
    )

    _write_picks(picks_path, pick_x, pick_times)
    _plot_raw_gather(raw_ct, header, raw_png, receiver_x, direct_times, diffraction_times)
    _plot_filtered_gather(
        filtered.data,
        filtered.header,
        filtered_png,
        receiver_x,
        diffraction_times,
        inverted_times,
        pick_x,
        pick_times,
    )
    geometry_metadata = build_das_geometry_metadata(geometry, receiver_x)
    localization_metadata = build_localization_algorithm_metadata()
    _write_result(
        result_path,
        geometry,
        inversion,
        pick_indices.size,
        geometry_metadata,
        localization_metadata,
    )

    print(f"output_dir={output_dir}")
    print(
        "true: "
        f"void_x={geometry.void_x:.6g} m "
        f"void_depth={geometry.void_depth:.6g} m "
        f"vr={geometry.vr:.6g} m/s"
    )
    print(
        "inverted: "
        f"void_x={inversion.void_x:.6g} m "
        f"void_depth={inversion.void_depth:.6g} m "
        f"vr={inversion.vr:.6g} m/s "
        f"rmse={inversion.rmse:.6g} s"
    )
    print_outputs([raw_path, filtered_path, raw_png, filtered_png, picks_path, result_path])
    return 0


def _synthetic_das_shot(
    geometry: SyntheticGeometry,
    receiver_x: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return workflow-only data shaped ``(time, channel)``."""

    direct_times = np.abs(receiver_x - geometry.source_x) / geometry.vr
    diffraction_times = _diffraction_travel_times(
        receiver_x,
        source_x=geometry.source_x,
        void_x=geometry.void_x,
        void_depth=geometry.void_depth,
        vr=geometry.vr,
    )
    data_tc = np.zeros((geometry.sample_count, geometry.channel_count), dtype=np.float32)
    wavelet_samples = 81
    peak_sample = wavelet_samples // 2
    wavelet = ricker_wavelet(
        geometry.fpeak,
        geometry.dt,
        wavelet_samples,
        peak_time=peak_sample * geometry.dt,
    )

    direct_distance = np.abs(receiver_x - geometry.source_x)
    direct_amplitude = 1.0 / np.sqrt(1.0 + 0.08 * direct_distance)
    diffraction_path = (
        abs(geometry.void_x - geometry.source_x)
        + np.sqrt(np.square(receiver_x - geometry.void_x) + geometry.void_depth**2)
    )
    diffraction_amplitude = 0.65 / np.sqrt(1.0 + 0.05 * diffraction_path)
    _inject_events(data_tc, direct_times, direct_amplitude, wavelet, geometry.dt)
    _inject_events(data_tc, diffraction_times, diffraction_amplitude, wavelet, geometry.dt)

    rng = np.random.default_rng(geometry.seed)
    data_tc += rng.normal(0.0, geometry.noise_std, data_tc.shape).astype(np.float32)
    return data_tc, direct_times, diffraction_times


def _diffraction_travel_times(
    receiver_x: np.ndarray,
    *,
    source_x: float,
    void_x: float,
    void_depth: float,
    vr: float,
) -> np.ndarray:
    """Workflow adapter for the package-level kinematic diffraction model."""

    receivers = np.asarray(receiver_x, dtype=np.float64).reshape(-1)
    if void_depth <= 0.0:
        raise ValueError("void_depth must be positive")
    if vr <= 0.0:
        raise ValueError("vr must be positive")
    receiver_xy = np.column_stack([receivers, np.zeros_like(receivers)])
    return diffraction_travel_time_2d(
        [float(source_x), 0.0],
        receiver_xy,
        [float(void_x), float(void_depth)],
        float(vr),
    )


def _invert_diffraction_picks(
    receiver_x: np.ndarray,
    pick_times: np.ndarray,
    *,
    source_x: float,
    x_bounds: tuple[float, float],
    depth_bounds: tuple[float, float],
    velocity_bounds: tuple[float, float],
) -> InversionResult:
    """Workflow-only variable-projection least-squares inversion."""

    receivers = np.asarray(receiver_x, dtype=np.float64).reshape(-1)
    observed = np.asarray(pick_times, dtype=np.float64).reshape(-1)
    if receivers.size < 3 or receivers.size != observed.size:
        raise ValueError("receiver_x and pick_times must contain the same three or more samples")
    if not np.all(np.isfinite(receivers)) or not np.all(np.isfinite(observed)):
        raise ValueError("picks must be finite")

    x_low, x_high = map(float, x_bounds)
    d_low, d_high = map(float, depth_bounds)
    v_low, v_high = map(float, velocity_bounds)
    if not (x_low < x_high and 0.0 < d_low < d_high and 0.0 < v_low < v_high):
        raise ValueError("invalid inversion bounds")

    best: InversionResult | None = None
    for points in (91, 81, 81):
        x_values = np.linspace(x_low, x_high, points, dtype=np.float64)
        depth_values = np.linspace(d_low, d_high, points, dtype=np.float64)
        best = _search_diffraction_grid(
            receivers,
            observed,
            source_x=source_x,
            x_values=x_values,
            depth_values=depth_values,
            velocity_bounds=(v_low, v_high),
        )
        x_step = float(x_values[1] - x_values[0])
        d_step = float(depth_values[1] - depth_values[0])
        x_low, x_high = best.void_x - 2.0 * x_step, best.void_x + 2.0 * x_step
        d_low = max(1.0e-6, best.void_depth - 2.0 * d_step)
        d_high = best.void_depth + 2.0 * d_step

    assert best is not None
    return best


def _search_diffraction_grid(
    receiver_x: np.ndarray,
    pick_times: np.ndarray,
    *,
    source_x: float,
    x_values: np.ndarray,
    depth_values: np.ndarray,
    velocity_bounds: tuple[float, float],
) -> InversionResult:
    receivers = np.asarray(receiver_x, dtype=np.float64).reshape(-1)
    observed = np.asarray(pick_times, dtype=np.float64).reshape(-1)
    receiver_xy = np.column_stack([receivers, np.zeros_like(receivers)])
    result = grid_search_point_location_velocity_2d(
        [float(source_x), 0.0],
        receiver_xy,
        observed,
        x_values,
        depth_values,
        velocity_bounds=velocity_bounds,
    )
    rmse = float(np.sqrt(np.mean(np.square(result.residuals_at_best))))
    return InversionResult(
        void_x=float(result.best_x),
        void_depth=float(result.best_z),
        vr=float(result.best_velocity),
        rmse=rmse,
    )


def _inject_events(
    data_tc: np.ndarray,
    arrival_times: np.ndarray,
    amplitudes: np.ndarray,
    wavelet: np.ndarray,
    dt: float,
) -> None:
    peak = int(np.argmax(wavelet))
    nt = data_tc.shape[0]
    for channel, (arrival, amplitude) in enumerate(zip(arrival_times, amplitudes, strict=True)):
        start = int(round(float(arrival) / dt)) - peak
        stop = start + wavelet.size
        live_start = max(start, 0)
        live_stop = min(stop, nt)
        if live_start >= live_stop:
            continue
        wave_start = live_start - start
        wave_stop = wave_start + (live_stop - live_start)
        data_tc[live_start:live_stop, channel] += float(amplitude) * wavelet[wave_start:wave_stop]


def _gather_header(geometry: SyntheticGeometry) -> RSFHeader:
    return RSFHeader(
        {
            "n1": geometry.sample_count,
            "o1": 0.0,
            "d1": geometry.dt,
            "label1": "Time",
            "unit1": "s",
            "n2": geometry.channel_count,
            "o2": 0.0,
            "d2": geometry.channel_spacing,
            "label2": "DAS Channel X",
            "unit2": "m",
            "das_workflow": "void_diffraction_kinematic",
            "source_x": geometry.source_x,
            "void_x": geometry.void_x,
            "void_depth": geometry.void_depth,
            "rayleigh_velocity": geometry.vr,
        }
    )


def _plot_raw_gather(
    data_ct: np.ndarray,
    header: RSFHeader,
    output_path: Path,
    receiver_x: np.ndarray,
    direct_times: np.ndarray,
    diffraction_times: np.ndarray,
) -> None:
    fig = grey(data_ct, header, title="Synthetic DAS shot gather", pclip=99.0)
    axis = fig.axes[0]
    axis.plot(direct_times, receiver_x, color="cyan", linewidth=1.0, label="direct Rayleigh")
    axis.plot(diffraction_times, receiver_x, color="red", linewidth=1.2, label="void diffraction")
    axis.legend(loc="best")
    fig.savefig(output_path, bbox_inches="tight", dpi=150)
    pyplot().close(fig)


def _plot_filtered_gather(
    data_ct: np.ndarray,
    header: RSFHeader,
    output_path: Path,
    receiver_x: np.ndarray,
    true_times: np.ndarray,
    inverted_times: np.ndarray,
    pick_x: np.ndarray,
    pick_times: np.ndarray,
) -> None:
    fig = grey(data_ct, header, title="FK-filtered gather and diffraction fit", pclip=99.0)
    axis = fig.axes[0]
    axis.plot(true_times, receiver_x, color="red", linewidth=1.2, label="true curve")
    axis.plot(inverted_times, receiver_x, color="yellow", linestyle="--", linewidth=1.2, label="LS fit")
    axis.scatter(pick_times, pick_x, s=10, c="cyan", edgecolors="none", label="simulated picks")
    axis.legend(loc="best")
    fig.savefig(output_path, bbox_inches="tight", dpi=150)
    pyplot().close(fig)


def _write_picks(path: Path, receiver_x: np.ndarray, pick_times: np.ndarray) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["receiver_x_m", "pick_time_s"])
        writer.writerows(zip(receiver_x, pick_times, strict=True))


def _write_result(
    path: Path,
    geometry: SyntheticGeometry,
    inversion: InversionResult,
    pick_count: int,
    geometry_metadata: dict[str, object],
    localization_metadata: dict[str, object],
) -> None:
    true_values = {
        "source_x": geometry.source_x,
        "void_x": geometry.void_x,
        "void_depth": geometry.void_depth,
        "vr": geometry.vr,
    }
    inverted_values = asdict(inversion)
    payload = {
        "workflow": "das_void_diffraction_kinematic_prototype",
        "data_layout": "NumPy synthesis uses data[time, channel]; RSF stores (channel, time).",
        "das_geometry": dict(geometry_metadata),
        "localization_algorithm": dict(localization_metadata),
        "true": true_values,
        "inverted": inverted_values,
        "relative_error": {
            "void_x": abs(inversion.void_x - geometry.void_x) / max(abs(geometry.void_x), 1.0),
            "void_depth": abs(inversion.void_depth - geometry.void_depth) / geometry.void_depth,
            "vr": abs(inversion.vr - geometry.vr) / geometry.vr,
        },
        "pick_count": int(pick_count),
        "synthetic": asdict(geometry),
        "fk_filter": {
            "vmin": 1.25 * geometry.vr,
            "vmax": 5.0 * geometry.vr,
            "taper": 0.25 * geometry.vr,
        },
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
