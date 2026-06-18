"""S3 NMO prototype contract workflow using the S1/S2 foundations.

This deterministic regular-gather regression is not a production NMO recipe.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import numpy as np

from pymadagascar.io.rsf import RSFArray, read_rsf
from pymadagascar.plot._common import pyplot
from pymadagascar.plot.grey import grey
from pymadagascar.seismic.nmo import nmo_correct
from pymadagascar.seismic.stack import stack_rsf
from pymadagascar.testing.seismic_fixtures import make_hyperbolic_gather_fixture
from pymadagascar.testing.seismic_metrics import (
    compute_trace_metrics,
    write_metrics_json,
)

from _common import parse_output_dir, print_outputs


TRUE_VELOCITY = 2200.0
WRONG_VELOCITY = 1700.0
SIGNAL_WINDOW = (95, 135)
PICK_WINDOW = (95, 145)
NOISE_WINDOW = (300, 450)
TARGET_BAND = (15.0, 35.0)
REJECT_BAND = (60.0, 80.0)


def run_pipeline(output_dir: Path) -> dict[str, object]:
    """Run the bounded S3 NMO regression and return its internal QC report."""

    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "raw": output_dir / "s3_raw_gather.rsf",
        "corrected": output_dir / "s3_nmo_corrected_gather.rsf",
        "wrong": output_dir / "s3_wrong_velocity_gather.rsf",
        "pre_stack": output_dir / "s3_pre_nmo_stack.rsf",
        "post_stack": output_dir / "s3_post_nmo_stack.rsf",
        "wrong_stack": output_dir / "s3_wrong_velocity_stack.rsf",
        "quicklook": output_dir / "s3_nmo_corrected_quicklook.png",
        "report": output_dir / "s3_nmo_qc_report.json",
    }

    make_hyperbolic_gather_fixture(path=paths["raw"])
    nmo_correct(
        paths["raw"],
        TRUE_VELOCITY,
        paths["corrected"],
        half=False,
        stretch=None,
    )
    nmo_correct(
        paths["raw"],
        WRONG_VELOCITY,
        paths["wrong"],
        half=False,
        stretch=None,
    )
    stack_rsf(paths["raw"], paths["pre_stack"], axis=2, mode="mean", nonzero=False)
    stack_rsf(
        paths["corrected"],
        paths["post_stack"],
        axis=2,
        mode="mean",
        nonzero=False,
    )
    stack_rsf(
        paths["wrong"],
        paths["wrong_stack"],
        axis=2,
        mode="mean",
        nonzero=False,
    )

    raw = read_rsf(paths["raw"])
    corrected = read_rsf(paths["corrected"])
    wrong = read_rsf(paths["wrong"])
    pre_stack = read_rsf(paths["pre_stack"])
    post_stack = read_rsf(paths["post_stack"])
    wrong_stack = read_rsf(paths["wrong_stack"])
    metrics = _nmo_metrics(
        raw,
        corrected,
        wrong,
        pre_stack,
        post_stack,
        wrong_stack,
    )
    checks = _nmo_checks(metrics, dt=float(raw.header["d1"]))

    fig = grey(
        corrected.data,
        corrected.header,
        output_path=paths["quicklook"],
        title="S3 NMO prototype contract: correct velocity",
        pclip=99.0,
    )
    pyplot().close(fig)

    report: dict[str, object] = {
        "workflow": "seismic_nmo_contract",
        "stage": "S3",
        "status": "prototype_contract_regression",
        "fixture": "hyperbolic_gather",
        "parameters": {
            "correct_velocity_m_per_s": TRUE_VELOCITY,
            "wrong_velocity_m_per_s": WRONG_VELOCITY,
            "offset_convention": "receiver_minus_source",
            "half_offset_input": False,
            "stretch_mute": "disabled",
            "interpolation": "linear",
        },
        "windows": {
            "signal_samples": list(SIGNAL_WINDOW),
            "pick_samples": list(PICK_WINDOW),
            "noise_samples": list(NOISE_WINDOW),
        },
        "metrics": metrics,
        "checks": checks,
    }
    write_metrics_json(paths["report"], report)
    return report


def _nmo_metrics(
    raw: RSFArray,
    corrected: RSFArray,
    wrong: RSFArray,
    pre_stack: RSFArray,
    post_stack: RSFArray,
    wrong_stack: RSFArray,
) -> dict[str, float | bool]:
    dt = float(raw.header["d1"])
    trace_kwargs = {
        "dt": dt,
        "signal_window": SIGNAL_WINDOW,
        "noise_window": NOISE_WINDOW,
        "target_band": TARGET_BAND,
        "reject_band": REJECT_BAND,
    }
    before = compute_trace_metrics(pre_stack.data, **trace_kwargs)
    after = compute_trace_metrics(post_stack.data, **trace_kwargs)
    wrong_velocity = compute_trace_metrics(wrong_stack.data, **trace_kwargs)
    before_peak = _window_peak(pre_stack.data)
    after_peak = _window_peak(post_stack.data)
    wrong_peak = _window_peak(wrong_stack.data)
    sample_count = sum(
        item.data.size
        for item in (raw, corrected, wrong, pre_stack, post_stack, wrong_stack)
    )
    finite_count = sum(
        int(np.count_nonzero(np.isfinite(item.data)))
        for item in (raw, corrected, wrong, pre_stack, post_stack, wrong_stack)
    )
    epsilon = np.finfo(np.float64).eps
    expected_t0 = float(raw.header["event_t0_s"])
    return {
        "event_pick_std_before_s": _event_pick_std(raw.data, dt),
        "event_pick_std_after_s": _event_pick_std(corrected.data, dt),
        "event_pick_std_wrong_velocity_s": _event_pick_std(wrong.data, dt),
        "pre_stack_peak_amplitude": before_peak[1],
        "post_stack_peak_amplitude": after_peak[1],
        "wrong_velocity_stack_peak_amplitude": wrong_peak[1],
        "stack_peak_amplitude_ratio": after_peak[1] / max(before_peak[1], epsilon),
        "correct_vs_wrong_stack_peak_ratio": after_peak[1]
        / max(wrong_peak[1], epsilon),
        "expected_zero_offset_time_s": expected_t0,
        "post_stack_peak_time_s": after_peak[0] * dt
        + float(raw.header.get("o1", 0.0)),
        "stack_snr_before_db": before["snr_db"],
        "stack_snr_after_db": after["snr_db"],
        "stack_snr_improvement_db": after["snr_db"] - before["snr_db"],
        "wrong_velocity_stack_snr_db": wrong_velocity["snr_db"],
        "noise_window_rms_before": before["noise_window_rms"],
        "noise_window_rms_after": after["noise_window_rms"],
        "noise_window_rms_ratio": after["noise_window_rms"]
        / max(before["noise_window_rms"], epsilon),
        "finite_fraction": float(finite_count / sample_count),
        "header_axis_ok": _headers_ok(raw, corrected, pre_stack, post_stack),
    }


def _event_pick_std(data: np.ndarray, dt: float) -> float:
    start, stop = PICK_WINDOW
    picks = start + np.argmax(np.asarray(data)[:, start:stop], axis=1)
    return float(np.std(picks.astype(np.float64) * dt))


def _window_peak(data: np.ndarray) -> tuple[int, float]:
    start, stop = SIGNAL_WINDOW
    window = np.asarray(data)[start:stop]
    local_index = int(np.argmax(np.abs(window)))
    return start + local_index, float(abs(window[local_index]))


def _headers_ok(
    raw: RSFArray,
    corrected: RSFArray,
    pre_stack: RSFArray,
    post_stack: RSFArray,
) -> bool:
    gather_keys = (
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
        raw.data.shape == corrected.data.shape
        and all(
            raw.header.get(key) == corrected.header.get(key)
            for key in gather_keys
        )
        and corrected.header.get("nmo_half") == "n"
        and corrected.header.get("nmo_direction") == "forward"
        and corrected.header.get("nmo_interpolation") == "linear"
        and corrected.header.get("nmo_offset_source") == "axis"
        and pre_stack.data.shape == post_stack.data.shape == (raw.data.shape[-1],)
        and pre_stack.header.get("n1") == raw.header.get("n1")
        and post_stack.header.get("n1") == raw.header.get("n1")
        and pre_stack.header.get("o1") == raw.header.get("o1")
        and post_stack.header.get("o1") == raw.header.get("o1")
        and pre_stack.header.get("d1") == raw.header.get("d1")
        and post_stack.header.get("d1") == raw.header.get("d1")
        and pre_stack.header.get("label1") == "Time"
        and post_stack.header.get("label1") == "Time"
        and pre_stack.header.get("unit1") == "s"
        and post_stack.header.get("unit1") == "s"
    )


def _nmo_checks(
    metrics: dict[str, float | bool],
    *,
    dt: float,
) -> dict[str, bool]:
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
        "noise_not_amplified": float(metrics["noise_window_rms_ratio"]) <= 1.2,
        "finite": np.isclose(float(metrics["finite_fraction"]), 1.0),
        "header_axis_ok": bool(metrics["header_axis_ok"]),
    }
    checks["overall_pass"] = bool(all(checks.values()))
    return checks


def main(argv: Sequence[str] | None = None) -> int:
    output_dir = parse_output_dir("seismic_nmo_contract", argv)
    report = run_pipeline(output_dir)
    metrics = report["metrics"]
    checks = report["checks"]
    assert isinstance(metrics, dict)
    assert isinstance(checks, dict)
    print(f"output_dir={output_dir}")
    print(
        "nmo_contract: "
        f"flattening_std_s={metrics['event_pick_std_after_s']:.6g} "
        f"stack_ratio={metrics['stack_peak_amplitude_ratio']:.6g} "
        f"correct_vs_wrong={metrics['correct_vs_wrong_stack_peak_ratio']:.6g} "
        f"overall_pass={checks['overall_pass']}"
    )
    print_outputs(
        [
            output_dir / "s3_raw_gather.rsf",
            output_dir / "s3_nmo_corrected_gather.rsf",
            output_dir / "s3_pre_nmo_stack.rsf",
            output_dir / "s3_post_nmo_stack.rsf",
            output_dir / "s3_nmo_corrected_quicklook.png",
            output_dir / "s3_nmo_qc_report.json",
        ]
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
