"""S5 integrated small-gather processing workflow.

This workflow combines the S1-S4 seismic-topic fixtures, metrics, geometry,
NMO, Semblance, and FK prototype checks into one deterministic regression. It
is not a production velocity-analysis, FK filtering, or field-processing flow.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import numpy as np

from pymadagascar.io.rsf import RSFArray, read_rsf
from pymadagascar.plot._common import pyplot
from pymadagascar.plot.grey import grey
from pymadagascar.seismic.agc import agc_rsf
from pymadagascar.seismic.fk import fk_filter, fk_spectrum
from pymadagascar.seismic.mute import mutter_rsf
from pymadagascar.seismic.nmo import nmo_correct
from pymadagascar.seismic.semblance import semblance_scan
from pymadagascar.seismic.stack import stack_rsf
from pymadagascar.signal.filter import bandpass_rsf
from pymadagascar.signal.qc import demean_rsf, detrend_rsf
from pymadagascar.testing.seismic_fixtures import make_hyperbolic_gather_fixture
from pymadagascar.testing.seismic_geometry import (
    make_explicit_offset_vector,
    make_regular_offset_geometry,
    make_source_receiver_table,
    table_column,
    validate_source_receiver_table,
    write_offset_vector_rsf,
)
from pymadagascar.testing.seismic_metrics import (
    compare_pipeline_metrics,
    compute_gather_pipeline_metrics,
    compute_trace_metrics,
    write_metrics_json,
)

from _common import parse_output_dir, print_outputs


TRUE_VELOCITY = 2200.0
WRONG_VELOCITY = 1700.0
VMIN = 1700.0
VMAX = 2700.0
DV = 100.0
SIGNAL_WINDOW = (95, 135)
PIPELINE_SIGNAL_WINDOW = (100, 163)
NOISE_WINDOW = (300, 450)
TARGET_BAND = (15.0, 35.0)
REJECT_BAND = (60.0, 80.0)
MUTE_T0 = 0.080
MUTE_VELOCITY = 4000.0
FK_VMIN = 1200.0
FK_VMAX = 4500.0


def run_pipeline(output_dir: Path) -> dict[str, object]:
    """Run the S5 integrated small-gather regression and return its report."""

    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "raw": output_dir / "s5_raw_gather.rsf",
        "offset_vector": output_dir / "s5_offset_vector.rsf",
        "geometry_table": output_dir / "s5_source_receiver_table.rsf",
        "demean": output_dir / "s5_demean_gather.rsf",
        "before_filter": output_dir / "s5_detrended_gather.rsf",
        "after_filter": output_dir / "s5_bandpassed_gather.rsf",
        "agc": output_dir / "s5_agc_gather.rsf",
        "processed": output_dir / "s5_processed_gather.rsf",
        "processed_stack": output_dir / "s5_processed_stack.rsf",
        "pre_nmo_stack": output_dir / "s5_pre_nmo_stack.rsf",
        "true_nmo": output_dir / "s5_true_velocity_nmo.rsf",
        "wrong_nmo": output_dir / "s5_wrong_velocity_nmo.rsf",
        "true_stack": output_dir / "s5_true_velocity_stack.rsf",
        "wrong_stack": output_dir / "s5_wrong_velocity_stack.rsf",
        "semblance": output_dir / "s5_semblance_panel.rsf",
        "fk_spectrum": output_dir / "s5_fk_spectrum.rsf",
        "fk_filtered": output_dir / "s5_fk_filtered_gather.rsf",
        "quicklook_gather": output_dir / "s5_true_nmo_quicklook.png",
        "quicklook_semblance": output_dir / "s5_semblance_quicklook.png",
        "quicklook_fk": output_dir / "s5_fk_spectrum_quicklook.png",
        "report": output_dir / "s5_integrated_qc_report.json",
    }

    raw = make_hyperbolic_gather_fixture(path=paths["raw"])
    geometry_report = _write_geometry_artifacts(raw, paths)

    demean_rsf(paths["raw"], paths["demean"], axis=1, nan_policy="raise")
    detrend_rsf(
        paths["demean"],
        paths["before_filter"],
        axis=1,
        type="linear",
        nan_policy="raise",
    )
    bandpass_rsf(
        paths["before_filter"],
        paths["after_filter"],
        flo=8.0,
        fhi=45.0,
        axis=1,
        taper=5.0,
    )
    agc_rsf(paths["after_filter"], paths["agc"], rect=0.080, axis=1)
    mutter_rsf(
        paths["agc"],
        paths["processed"],
        time_axis=1,
        offset_axis=2,
        t0=MUTE_T0,
        v=MUTE_VELOCITY,
        side="above",
        taper=6,
    )
    stack_rsf(paths["processed"], paths["processed_stack"], axis=2, mode="mean", nonzero=False)

    nmo_correct(paths["after_filter"], TRUE_VELOCITY, paths["true_nmo"], half=False, stretch=None)
    nmo_correct(paths["after_filter"], WRONG_VELOCITY, paths["wrong_nmo"], half=False, stretch=None)
    stack_rsf(paths["after_filter"], paths["pre_nmo_stack"], axis=2, mode="mean", nonzero=False)
    stack_rsf(paths["true_nmo"], paths["true_stack"], axis=2, mode="mean", nonzero=False)
    stack_rsf(paths["wrong_nmo"], paths["wrong_stack"], axis=2, mode="mean", nonzero=False)

    semblance_scan(
        paths["after_filter"],
        paths["semblance"],
        vmin=VMIN,
        vmax=VMAX,
        dv=DV,
        half=False,
        stretch=None,
        smooth=2,
    )
    fk_spectrum(paths["after_filter"], paths["fk_spectrum"])
    fk_filter(paths["after_filter"], paths["fk_filtered"], vmin=FK_VMIN, vmax=FK_VMAX)

    raw_rsf = read_rsf(paths["raw"])
    before_filter = read_rsf(paths["before_filter"])
    after_filter = read_rsf(paths["after_filter"])
    processed = read_rsf(paths["processed"])
    processed_stack = read_rsf(paths["processed_stack"])
    true_nmo = read_rsf(paths["true_nmo"])
    wrong_nmo = read_rsf(paths["wrong_nmo"])
    pre_nmo_stack = read_rsf(paths["pre_nmo_stack"])
    true_stack = read_rsf(paths["true_stack"])
    wrong_stack = read_rsf(paths["wrong_stack"])
    semblance = read_rsf(paths["semblance"])
    fk_panel = read_rsf(paths["fk_spectrum"])
    fk_filtered = read_rsf(paths["fk_filtered"])

    pipeline_metrics = compute_gather_pipeline_metrics(
        raw_rsf,
        before_filter,
        after_filter,
        processed,
        processed_stack,
        signal_window=PIPELINE_SIGNAL_WINDOW,
        noise_window=NOISE_WINDOW,
        target_band=TARGET_BAND,
        reject_band=REJECT_BAND,
        mute_t0=MUTE_T0,
        mute_velocity=MUTE_VELOCITY,
    )
    pipeline_checks = compare_pipeline_metrics(pipeline_metrics)
    nmo_metrics = _nmo_metrics(
        raw_rsf,
        after_filter,
        true_nmo,
        wrong_nmo,
        pre_nmo_stack,
        true_stack,
        wrong_stack,
    )
    nmo_checks = _nmo_checks(nmo_metrics, dt=float(raw_rsf.header["d1"]))
    semblance_metrics = _semblance_metrics(after_filter, semblance, true_stack, wrong_stack)
    semblance_checks = _semblance_checks(semblance_metrics, dt=float(raw_rsf.header["d1"]))
    fk_metrics = _fk_metrics(after_filter, fk_panel, fk_filtered)
    fk_checks = _fk_checks(fk_metrics)
    stack_metrics = _stack_metrics(raw_rsf, pre_nmo_stack, true_stack, wrong_stack)
    stack_checks = _stack_checks(stack_metrics, dt=float(raw_rsf.header["d1"]))

    for path, item, title in (
        (paths["quicklook_gather"], true_nmo, "S5 integrated workflow: true-velocity NMO"),
        (paths["quicklook_semblance"], semblance, "S5 integrated workflow: semblance panel"),
        (paths["quicklook_fk"], fk_panel, "S5 integrated workflow: FK spectrum"),
    ):
        fig = grey(item.data, item.header, output_path=path, title=title, pclip=99.0)
        pyplot().close(fig)

    checks = {
        "geometry": bool(geometry_report["checks"]["overall_pass"]),
        "pipeline": bool(pipeline_checks["overall_pass"]),
        "nmo": bool(nmo_checks["overall_pass"]),
        "semblance": bool(semblance_checks["overall_pass"]),
        "fk": bool(fk_checks["overall_pass"]),
        "stack": bool(stack_checks["overall_pass"]),
        "finite": bool(
            np.isclose(float(pipeline_metrics["finite_fraction"]), 1.0)
            and np.isclose(float(nmo_metrics["finite_fraction"]), 1.0)
            and np.isclose(float(semblance_metrics["finite_fraction"]), 1.0)
            and np.isclose(float(fk_metrics["finite_fraction"]), 1.0)
        ),
    }
    checks["overall_pass"] = bool(all(checks.values()))

    report: dict[str, object] = {
        "workflow": "seismic_small_gather_processing_workflow",
        "stage": "S5",
        "status": "integrated_workflow_regression_v0",
        "inputs": {
            "fixture": "hyperbolic_gather",
            "true_velocity_m_per_s": TRUE_VELOCITY,
            "wrong_velocity_m_per_s": WRONG_VELOCITY,
            "velocity_scan_min_m_per_s": VMIN,
            "velocity_scan_max_m_per_s": VMAX,
            "velocity_scan_step_m_per_s": DV,
            "fk_filter_vmin_m_per_s": FK_VMIN,
            "fk_filter_vmax_m_per_s": FK_VMAX,
            "output_schema": "workflow_internal_regression_only",
        },
        "geometry": geometry_report,
        "pipeline": {
            "metrics": pipeline_metrics,
            "checks": pipeline_checks,
        },
        "nmo": {
            "metrics": nmo_metrics,
            "checks": nmo_checks,
        },
        "semblance": {
            "metrics": semblance_metrics,
            "checks": semblance_checks,
        },
        "fk": {
            "metrics": fk_metrics,
            "checks": fk_checks,
        },
        "stack": {
            "metrics": stack_metrics,
            "checks": stack_checks,
        },
        "checks": checks,
    }
    write_metrics_json(paths["report"], report)
    return report


def _write_geometry_artifacts(
    raw: RSFArray,
    paths: dict[str, Path],
) -> dict[str, object]:
    regular = make_regular_offset_geometry(raw, expected_ntrace=raw.data.shape[0])
    explicit = make_explicit_offset_vector(
        regular.offsets,
        expected_ntrace=raw.data.shape[0],
        unit=regular.unit,
        time_unit=regular.time_unit,
        velocity_unit=regular.velocity_unit,
    )
    write_offset_vector_rsf(paths["offset_vector"], explicit)
    make_source_receiver_table(offsets=explicit, path=paths["geometry_table"])
    table = read_rsf(paths["geometry_table"])
    table_metrics = validate_source_receiver_table(table)
    offsets = table_column(table, "offset")
    finite_fraction = _finite_fraction(raw.data, explicit.values, table.data)
    metrics = {
        "ntrace": int(raw.data.shape[0]),
        "regular_offset_min_m": float(np.min(regular.offsets)),
        "regular_offset_max_m": float(np.max(regular.offsets)),
        "regular_offset_step_m": float(regular.offsets[1] - regular.offsets[0]),
        "regular_explicit_max_abs_diff_m": float(
            np.max(np.abs(regular.offsets - explicit.values))
        ),
        "table_offset_max_abs_diff_m": float(np.max(np.abs(offsets - explicit.values))),
        "finite_fraction": finite_fraction,
        "source_receiver_table_overall_pass": bool(table_metrics["overall_pass"]),
    }
    checks = {
        "regular_explicit_agree": metrics["regular_explicit_max_abs_diff_m"] <= 1.0e-12,
        "table_offsets_agree": metrics["table_offset_max_abs_diff_m"] <= 1.0e-12,
        "source_receiver_table": bool(table_metrics["overall_pass"]),
        "ordinary_rsf_only": raw.header["trace_header_model"] == "ordinary_rsf_only",
        "not_segy_trace_header": table.header["segy_trace_header_model"] == "not_supported",
        "finite": finite_fraction == 1.0,
    }
    checks["overall_pass"] = bool(all(checks.values()))
    return {
        "contracts": {
            "regular_offset": regular.as_report(),
            "explicit_offset": explicit.as_report(),
            "source_receiver_table": {
                "trace_header_model": "minimal_numeric_header_table",
                "segy_trace_header_model": "not_supported",
            },
        },
        "metrics": metrics,
        "checks": checks,
    }


def _nmo_metrics(
    raw: RSFArray,
    before_nmo: RSFArray,
    true_nmo: RSFArray,
    wrong_nmo: RSFArray,
    pre_stack: RSFArray,
    true_stack: RSFArray,
    wrong_stack: RSFArray,
) -> dict[str, float | bool]:
    before_peak = _window_peak(pre_stack.data)
    true_peak = _window_peak(true_stack.data)
    wrong_peak = _window_peak(wrong_stack.data)
    epsilon = np.finfo(np.float64).eps
    finite_count = sum(
        int(np.count_nonzero(np.isfinite(item.data)))
        for item in (raw, before_nmo, true_nmo, wrong_nmo, pre_stack, true_stack, wrong_stack)
    )
    sample_count = sum(
        item.data.size
        for item in (raw, before_nmo, true_nmo, wrong_nmo, pre_stack, true_stack, wrong_stack)
    )
    trace_kwargs = {
        "dt": float(raw.header["d1"]),
        "signal_window": SIGNAL_WINDOW,
        "noise_window": NOISE_WINDOW,
        "target_band": TARGET_BAND,
        "reject_band": REJECT_BAND,
    }
    before_stack_metrics = compute_trace_metrics(pre_stack.data, **trace_kwargs)
    true_stack_metrics = compute_trace_metrics(true_stack.data, **trace_kwargs)
    wrong_stack_metrics = compute_trace_metrics(wrong_stack.data, **trace_kwargs)
    return {
        "event_pick_std_before_s": _event_pick_std(before_nmo.data, float(raw.header["d1"])),
        "event_pick_std_after_s": _event_pick_std(true_nmo.data, float(raw.header["d1"])),
        "event_pick_std_wrong_velocity_s": _event_pick_std(
            wrong_nmo.data,
            float(raw.header["d1"]),
        ),
        "stack_peak_amplitude_before": before_peak[1],
        "stack_peak_amplitude_after": true_peak[1],
        "stack_peak_amplitude_wrong_velocity": wrong_peak[1],
        "stack_peak_amplitude_ratio": true_peak[1] / max(before_peak[1], epsilon),
        "correct_vs_wrong_stack_peak_ratio": true_peak[1] / max(wrong_peak[1], epsilon),
        "post_stack_peak_time_s": true_peak[0] * float(raw.header["d1"])
        + float(raw.header.get("o1", 0.0)),
        "expected_zero_offset_time_s": float(raw.header["event_t0_s"]),
        "stack_snr_before_db": before_stack_metrics["snr_db"],
        "stack_snr_after_db": true_stack_metrics["snr_db"],
        "stack_snr_wrong_velocity_db": wrong_stack_metrics["snr_db"],
        "finite_fraction": float(finite_count / sample_count),
        "header_axis_ok": _nmo_headers_ok(before_nmo, true_nmo, pre_stack, true_stack),
    }


def _nmo_checks(metrics: dict[str, float | bool], *, dt: float) -> dict[str, bool]:
    checks = {
        "event_flattened": float(metrics["event_pick_std_after_s"]) <= 0.003,
        "flattening_improved": float(metrics["event_pick_std_after_s"])
        <= 0.35 * float(metrics["event_pick_std_before_s"]),
        "correct_velocity_better_than_wrong": (
            float(metrics["event_pick_std_wrong_velocity_s"])
            >= 2.0 * float(metrics["event_pick_std_after_s"])
            and float(metrics["correct_vs_wrong_stack_peak_ratio"]) >= 1.8
        ),
        "stack_peak_increased": float(metrics["stack_peak_amplitude_ratio"]) >= 2.0,
        "stack_peak_time_near_t0": abs(
            float(metrics["post_stack_peak_time_s"])
            - float(metrics["expected_zero_offset_time_s"])
        )
        <= 1.5 * dt,
        "finite": bool(np.isclose(float(metrics["finite_fraction"]), 1.0)),
        "header_axis_ok": bool(metrics["header_axis_ok"]),
    }
    checks["overall_pass"] = bool(all(checks.values()))
    return checks


def _semblance_metrics(
    input_gather: RSFArray,
    panel: RSFArray,
    true_stack: RSFArray,
    wrong_stack: RSFArray,
) -> dict[str, float | bool]:
    velocities = _axis_values(panel, 2)
    times = _axis_values(panel, 1)
    event_index = int(round(float(input_gather.header["event_t0_s"]) / float(input_gather.header["d1"])))
    event_index = min(max(event_index, 0), panel.data.shape[-1] - 1)
    event_scores = np.asarray(panel.data[:, event_index], dtype=np.float64)
    true_index = int(np.argmin(np.abs(velocities - TRUE_VELOCITY)))
    wrong_index = int(np.argmin(np.abs(velocities - WRONG_VELOCITY)))
    peak_index = int(np.argmax(event_scores))
    global_index = np.unravel_index(int(np.argmax(panel.data)), panel.data.shape)
    true_peak = _window_peak(true_stack.data)
    wrong_peak = _window_peak(wrong_stack.data)
    finite_count = sum(
        int(np.count_nonzero(np.isfinite(item.data)))
        for item in (input_gather, panel, true_stack, wrong_stack)
    )
    sample_count = sum(item.data.size for item in (input_gather, panel, true_stack, wrong_stack))
    epsilon = np.finfo(np.float64).eps
    return {
        "expected_velocity_m_per_s": TRUE_VELOCITY,
        "wrong_velocity_m_per_s": WRONG_VELOCITY,
        "expected_event_time_s": float(input_gather.header["event_t0_s"]),
        "peak_velocity_at_event_m_per_s": float(velocities[peak_index]),
        "peak_semblance_at_event": float(event_scores[peak_index]),
        "true_velocity_semblance": float(event_scores[true_index]),
        "wrong_velocity_semblance": float(event_scores[wrong_index]),
        "true_to_wrong_semblance_ratio": float(
            event_scores[true_index] / max(event_scores[wrong_index], epsilon)
        ),
        "global_peak_velocity_m_per_s": float(velocities[global_index[0]]),
        "global_peak_time_s": float(times[global_index[1]]),
        "true_to_wrong_stack_peak_ratio": true_peak[1] / max(wrong_peak[1], epsilon),
        "finite_fraction": float(finite_count / sample_count),
        "header_axis_ok": _semblance_headers_ok(input_gather, panel),
    }


def _semblance_checks(metrics: dict[str, float | bool], *, dt: float) -> dict[str, bool]:
    checks = {
        "peak_velocity_near_true": abs(
            float(metrics["peak_velocity_at_event_m_per_s"]) - TRUE_VELOCITY
        )
        <= DV,
        "global_peak_velocity_near_true": abs(
            float(metrics["global_peak_velocity_m_per_s"]) - TRUE_VELOCITY
        )
        <= DV,
        "peak_time_near_t0": abs(
            float(metrics["global_peak_time_s"])
            - float(metrics["expected_event_time_s"])
        )
        <= 1.5 * dt,
        "true_velocity_beats_wrong": float(metrics["true_to_wrong_semblance_ratio"]) >= 2.0,
        "true_stack_beats_wrong": float(metrics["true_to_wrong_stack_peak_ratio"]) >= 1.8,
        "finite": bool(np.isclose(float(metrics["finite_fraction"]), 1.0)),
        "header_axis_ok": bool(metrics["header_axis_ok"]),
    }
    checks["overall_pass"] = bool(all(checks.values()))
    return checks


def _fk_metrics(input_gather: RSFArray, spectrum: RSFArray, filtered: RSFArray) -> dict[str, float | bool]:
    peak_frequency, peak_wavenumber, peak_amplitude = _positive_frequency_peak(spectrum)
    input_rms = _rms(input_gather.data)
    filtered_rms = _rms(filtered.data)
    finite_count = sum(
        int(np.count_nonzero(np.isfinite(item.data)))
        for item in (input_gather, spectrum, filtered)
    )
    sample_count = input_gather.data.size + spectrum.data.size + filtered.data.size
    return {
        "peak_frequency_hz": peak_frequency,
        "peak_wavenumber_1_per_m": peak_wavenumber,
        "peak_amplitude": peak_amplitude,
        "input_rms": input_rms,
        "filtered_rms": filtered_rms,
        "filtered_rms_ratio": filtered_rms / max(input_rms, np.finfo(np.float64).eps),
        "finite_fraction": float(finite_count / sample_count),
        "header_axis_ok": _fk_headers_ok(input_gather, spectrum, filtered),
    }


def _fk_checks(metrics: dict[str, float | bool]) -> dict[str, bool]:
    checks = {
        "spectrum_peak_finite": bool(
            np.isfinite(float(metrics["peak_frequency_hz"]))
            and np.isfinite(float(metrics["peak_wavenumber_1_per_m"]))
            and float(metrics["peak_amplitude"]) > 0.0
        ),
        "filter_energy_bounded": 0.05 <= float(metrics["filtered_rms_ratio"]) <= 1.05,
        "finite": bool(np.isclose(float(metrics["finite_fraction"]), 1.0)),
        "header_axis_ok": bool(metrics["header_axis_ok"]),
    }
    checks["overall_pass"] = bool(all(checks.values()))
    return checks


def _stack_metrics(raw: RSFArray, pre_stack: RSFArray, true_stack: RSFArray, wrong_stack: RSFArray) -> dict[str, float]:
    pre_peak = _window_peak(pre_stack.data)
    true_peak = _window_peak(true_stack.data)
    wrong_peak = _window_peak(wrong_stack.data)
    epsilon = np.finfo(np.float64).eps
    return {
        "expected_zero_offset_time_s": float(raw.header["event_t0_s"]),
        "pre_nmo_peak_time_s": pre_peak[0] * float(raw.header["d1"]) + float(raw.header.get("o1", 0.0)),
        "post_nmo_peak_time_s": true_peak[0] * float(raw.header["d1"]) + float(raw.header.get("o1", 0.0)),
        "wrong_nmo_peak_time_s": wrong_peak[0] * float(raw.header["d1"]) + float(raw.header.get("o1", 0.0)),
        "pre_nmo_peak_amplitude": pre_peak[1],
        "post_nmo_peak_amplitude": true_peak[1],
        "wrong_nmo_peak_amplitude": wrong_peak[1],
        "post_to_pre_peak_ratio": true_peak[1] / max(pre_peak[1], epsilon),
        "post_to_wrong_peak_ratio": true_peak[1] / max(wrong_peak[1], epsilon),
    }


def _stack_checks(metrics: dict[str, float], *, dt: float) -> dict[str, bool]:
    checks = {
        "post_stack_stronger_than_pre": metrics["post_to_pre_peak_ratio"] >= 2.0,
        "post_stack_stronger_than_wrong": metrics["post_to_wrong_peak_ratio"] >= 1.8,
        "post_peak_time_near_t0": abs(
            metrics["post_nmo_peak_time_s"] - metrics["expected_zero_offset_time_s"]
        )
        <= 1.5 * dt,
    }
    checks["overall_pass"] = bool(all(checks.values()))
    return checks


def _event_pick_std(data: np.ndarray, dt: float) -> float:
    start, stop = SIGNAL_WINDOW
    picks = start + np.argmax(np.asarray(data)[:, start:stop], axis=1)
    return float(np.std(picks.astype(np.float64) * dt))


def _window_peak(data: np.ndarray) -> tuple[int, float]:
    start, stop = SIGNAL_WINDOW
    window = np.asarray(data)[start:stop]
    local = int(np.argmax(np.abs(window)))
    return start + local, float(abs(window[local]))


def _positive_frequency_peak(item: RSFArray) -> tuple[float, float, float]:
    frequencies = _axis_values(item, 1)
    wavenumbers = _axis_values(item, 2)
    positive = frequencies > 0.0
    spectrum = np.asarray(item.data[:, positive], dtype=np.float64)
    peak = np.unravel_index(int(np.argmax(spectrum)), spectrum.shape)
    return (
        float(frequencies[positive][peak[1]]),
        float(wavenumbers[peak[0]]),
        float(spectrum[peak]),
    )


def _axis_values(item: RSFArray, axis: int) -> np.ndarray:
    origin = float(item.header[f"o{axis}"])
    spacing = float(item.header[f"d{axis}"])
    count = int(item.header[f"n{axis}"])
    return origin + spacing * np.arange(count, dtype=np.float64)


def _finite_fraction(*arrays: np.ndarray) -> float:
    total = sum(array.size for array in arrays)
    finite = sum(int(np.count_nonzero(np.isfinite(array))) for array in arrays)
    return float(finite / total)


def _rms(data: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(np.asarray(data, dtype=np.float64)))))


def _nmo_headers_ok(
    before_nmo: RSFArray,
    true_nmo: RSFArray,
    pre_stack: RSFArray,
    true_stack: RSFArray,
) -> bool:
    keys = (
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
        "offset_sign_convention",
    )
    return bool(
        before_nmo.data.shape == true_nmo.data.shape
        and all(before_nmo.header.get(key) == true_nmo.header.get(key) for key in keys)
        and true_nmo.header.get("nmo_half") == "n"
        and true_nmo.header.get("nmo_direction") == "forward"
        and true_nmo.header.get("nmo_offset_source") == "axis"
        and pre_stack.data.shape == true_stack.data.shape == (before_nmo.data.shape[-1],)
        and true_stack.header.get("label1") == "Time"
        and true_stack.header.get("unit1") == "s"
    )


def _semblance_headers_ok(input_gather: RSFArray, panel: RSFArray) -> bool:
    return bool(
        panel.data.shape == (int((VMAX - VMIN) / DV) + 1, input_gather.data.shape[-1])
        and panel.header.get("n1") == input_gather.header.get("n1")
        and panel.header.get("label1") == "Time"
        and panel.header.get("unit1") == "s"
        and panel.header.get("label2") == "Velocity"
        and panel.header.get("unit2") == "m/s"
        and panel.header.get("axis2_role") == "velocity"
        and panel.header.get("coordinate_sampling") == "regular"
        and panel.header.get("semblance_reference_source")
        == "../src-master/system/seismic/Mvscan.c"
        and panel.header.get("semblance_input_axis2_role") == "signed_offset"
    )


def _fk_headers_ok(input_gather: RSFArray, spectrum: RSFArray, filtered: RSFArray) -> bool:
    return bool(
        spectrum.data.shape == input_gather.data.shape
        and spectrum.header.get("label1") == "Frequency"
        and spectrum.header.get("unit1") == "Hz"
        and spectrum.header.get("label2") == "Wavenumber"
        and spectrum.header.get("unit2") == "1/m"
        and spectrum.header.get("fk_reference_source")
        == "../src-master/system/generic/Mdipfilter.c"
        and filtered.data.shape == input_gather.data.shape
        and filtered.header.get("label1") == input_gather.header.get("label1")
        and filtered.header.get("label2") == input_gather.header.get("label2")
        and filtered.header.get("fkfilter_reference_source")
        == "../src-master/system/generic/Mdipfilter.c"
    )


def main(argv: Sequence[str] | None = None) -> int:
    output_dir = parse_output_dir("seismic_small_gather_processing", argv)
    report = run_pipeline(output_dir)
    checks = report["checks"]
    nmo = report["nmo"]
    semblance = report["semblance"]
    fk = report["fk"]
    assert isinstance(checks, dict)
    assert isinstance(nmo, dict)
    assert isinstance(semblance, dict)
    assert isinstance(fk, dict)
    nmo_metrics = nmo["metrics"]
    semblance_metrics = semblance["metrics"]
    fk_metrics = fk["metrics"]
    assert isinstance(nmo_metrics, dict)
    assert isinstance(semblance_metrics, dict)
    assert isinstance(fk_metrics, dict)
    print(f"output_dir={output_dir}")
    print(
        "small_gather_processing: "
        f"nmo_stack_ratio={nmo_metrics['stack_peak_amplitude_ratio']:.6g} "
        f"semblance_peak_velocity={semblance_metrics['peak_velocity_at_event_m_per_s']:.6g} "
        f"fk_filtered_ratio={fk_metrics['filtered_rms_ratio']:.6g} "
        f"overall_pass={checks['overall_pass']}"
    )
    print_outputs(
        [
            output_dir / "s5_raw_gather.rsf",
            output_dir / "s5_processed_gather.rsf",
            output_dir / "s5_true_velocity_nmo.rsf",
            output_dir / "s5_semblance_panel.rsf",
            output_dir / "s5_fk_spectrum.rsf",
            output_dir / "s5_fk_filtered_gather.rsf",
            output_dir / "s5_true_nmo_quicklook.png",
            output_dir / "s5_integrated_qc_report.json",
        ]
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
