"""S4-1 Semblance prototype contract workflow.

This deterministic regular-gather regression is not a production velocity
analysis workflow and does not attempt to clone full Madagascar ``sfvscan``.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import numpy as np

from pymadagascar.io.rsf import RSFArray, read_rsf
from pymadagascar.plot._common import pyplot
from pymadagascar.plot.grey import grey
from pymadagascar.seismic.nmo import nmo_correct
from pymadagascar.seismic.semblance import semblance_scan
from pymadagascar.seismic.stack import stack_rsf
from pymadagascar.testing.seismic_fixtures import make_hyperbolic_gather_fixture
from pymadagascar.testing.seismic_metrics import write_metrics_json

from _common import parse_output_dir, print_outputs


TRUE_VELOCITY = 2200.0
WRONG_VELOCITY = 1700.0
VMIN = 1700.0
VMAX = 2700.0
DV = 100.0
SIGNAL_WINDOW = (95, 135)
EVENT_SAMPLE = 112


def run_pipeline(output_dir: Path) -> dict[str, object]:
    """Run the bounded S4-1 Semblance regression and return its QC report."""

    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "raw": output_dir / "s4_semblance_raw_gather.rsf",
        "panel": output_dir / "s4_semblance_panel.rsf",
        "true_nmo": output_dir / "s4_true_velocity_nmo.rsf",
        "wrong_nmo": output_dir / "s4_wrong_velocity_nmo.rsf",
        "true_stack": output_dir / "s4_true_velocity_stack.rsf",
        "wrong_stack": output_dir / "s4_wrong_velocity_stack.rsf",
        "quicklook": output_dir / "s4_semblance_panel_quicklook.png",
        "report": output_dir / "s4_semblance_qc_report.json",
    }

    make_hyperbolic_gather_fixture(path=paths["raw"])
    semblance_scan(
        paths["raw"],
        paths["panel"],
        vmin=VMIN,
        vmax=VMAX,
        dv=DV,
        half=False,
        stretch=None,
        smooth=2,
    )
    nmo_correct(
        paths["raw"],
        TRUE_VELOCITY,
        paths["true_nmo"],
        half=False,
        stretch=None,
    )
    nmo_correct(
        paths["raw"],
        WRONG_VELOCITY,
        paths["wrong_nmo"],
        half=False,
        stretch=None,
    )
    stack_rsf(paths["true_nmo"], paths["true_stack"], axis=2, mode="mean", nonzero=False)
    stack_rsf(paths["wrong_nmo"], paths["wrong_stack"], axis=2, mode="mean", nonzero=False)

    raw = read_rsf(paths["raw"])
    panel = read_rsf(paths["panel"])
    true_stack = read_rsf(paths["true_stack"])
    wrong_stack = read_rsf(paths["wrong_stack"])
    metrics = _semblance_metrics(raw, panel, true_stack, wrong_stack)
    checks = _semblance_checks(metrics, dv=DV, dt=float(raw.header["d1"]))

    fig = grey(
        panel.data,
        panel.header,
        output_path=paths["quicklook"],
        title="S4-1 Semblance prototype contract panel",
        pclip=99.0,
    )
    pyplot().close(fig)

    report: dict[str, object] = {
        "workflow": "seismic_semblance_contract",
        "stage": "S4-1",
        "status": "prototype_contract_regression",
        "fixture": "hyperbolic_gather",
        "madagascar_reference": "../src-master/system/seismic/Mvscan.c",
        "parameters": {
            "velocity_min_m_per_s": VMIN,
            "velocity_max_m_per_s": VMAX,
            "velocity_step_m_per_s": DV,
            "true_velocity_m_per_s": TRUE_VELOCITY,
            "wrong_velocity_m_per_s": WRONG_VELOCITY,
            "offset_convention": "receiver_minus_source",
            "half_offset_input": False,
            "stretch_mute": "disabled",
            "semblance": "simple_nmo_stack_ratio",
            "not_sfvscan_clone": True,
        },
        "windows": {
            "signal_samples": list(SIGNAL_WINDOW),
            "event_sample": EVENT_SAMPLE,
        },
        "metrics": metrics,
        "checks": checks,
    }
    write_metrics_json(paths["report"], report)
    return report


def _semblance_metrics(
    raw: RSFArray,
    panel: RSFArray,
    true_stack: RSFArray,
    wrong_stack: RSFArray,
) -> dict[str, float | bool]:
    velocity_axis = _axis_values(panel, 2)
    time_axis = _axis_values(panel, 1)
    event_index = int(round(float(raw.header["event_t0_s"]) / float(raw.header["d1"])))
    event_index = min(max(event_index, 0), panel.data.shape[-1] - 1)
    true_index = int(np.argmin(np.abs(velocity_axis - TRUE_VELOCITY)))
    wrong_index = int(np.argmin(np.abs(velocity_axis - WRONG_VELOCITY)))
    event_scores = np.asarray(panel.data[:, event_index], dtype=np.float64)
    peak_velocity_index = int(np.argmax(event_scores))
    global_index = np.unravel_index(int(np.argmax(panel.data)), panel.data.shape)
    true_peak = _window_peak(true_stack.data)
    wrong_peak = _window_peak(wrong_stack.data)
    sample_count = raw.data.size + panel.data.size + true_stack.data.size + wrong_stack.data.size
    finite_count = sum(
        int(np.count_nonzero(np.isfinite(item.data)))
        for item in (raw, panel, true_stack, wrong_stack)
    )
    epsilon = np.finfo(np.float64).eps
    return {
        "expected_velocity_m_per_s": TRUE_VELOCITY,
        "wrong_velocity_m_per_s": WRONG_VELOCITY,
        "expected_event_time_s": float(raw.header["event_t0_s"]),
        "event_sample": float(event_index),
        "event_time_s": float(time_axis[event_index]),
        "peak_velocity_at_event_m_per_s": float(velocity_axis[peak_velocity_index]),
        "peak_semblance_at_event": float(event_scores[peak_velocity_index]),
        "true_velocity_semblance": float(event_scores[true_index]),
        "wrong_velocity_semblance": float(event_scores[wrong_index]),
        "true_to_wrong_semblance_ratio": float(
            event_scores[true_index] / max(event_scores[wrong_index], epsilon)
        ),
        "global_peak_velocity_m_per_s": float(velocity_axis[global_index[0]]),
        "global_peak_time_s": float(time_axis[global_index[1]]),
        "global_peak_semblance": float(panel.data[global_index]),
        "true_velocity_stack_peak_amplitude": true_peak[1],
        "wrong_velocity_stack_peak_amplitude": wrong_peak[1],
        "true_to_wrong_stack_peak_ratio": true_peak[1] / max(wrong_peak[1], epsilon),
        "finite_fraction": float(finite_count / sample_count),
        "header_axis_ok": _headers_ok(raw, panel),
    }


def _semblance_checks(
    metrics: dict[str, float | bool],
    *,
    dv: float,
    dt: float,
) -> dict[str, bool]:
    checks = {
        "peak_velocity_near_true": abs(
            float(metrics["peak_velocity_at_event_m_per_s"])
            - float(metrics["expected_velocity_m_per_s"])
        )
        <= dv,
        "global_peak_velocity_near_true": abs(
            float(metrics["global_peak_velocity_m_per_s"])
            - float(metrics["expected_velocity_m_per_s"])
        )
        <= dv,
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


def _axis_values(item: RSFArray, axis: int) -> np.ndarray:
    origin = float(item.header[f"o{axis}"])
    spacing = float(item.header[f"d{axis}"])
    count = int(item.header[f"n{axis}"])
    return origin + spacing * np.arange(count, dtype=np.float64)


def _window_peak(data: np.ndarray) -> tuple[int, float]:
    start, stop = SIGNAL_WINDOW
    window = np.asarray(data)[start:stop]
    local_index = int(np.argmax(np.abs(window)))
    return start + local_index, float(abs(window[local_index]))


def _headers_ok(raw: RSFArray, panel: RSFArray) -> bool:
    return bool(
        raw.data.ndim == 2
        and panel.data.ndim == 2
        and panel.header.get("n1") == raw.header.get("n1")
        and panel.header.get("o1") == raw.header.get("o1")
        and panel.header.get("d1") == raw.header.get("d1")
        and panel.header.get("label1") == "Time"
        and panel.header.get("unit1") == "s"
        and panel.header.get("n2") == str(int((VMAX - VMIN) / DV) + 1)
        and panel.header.get("o2") == f"{VMIN:g}"
        and panel.header.get("d2") == f"{DV:g}"
        and panel.header.get("label2") == "Velocity"
        and panel.header.get("unit2") == "m/s"
        and panel.header.get("axis2_role") == "velocity"
        and panel.header.get("coordinate_sampling") == "regular"
        and panel.header.get("semblance_offset_source") == "axis"
        and panel.header.get("semblance_input_offset_n") == raw.header.get("n2")
        and panel.header.get("semblance_input_offset_o") == raw.header.get("o2")
        and panel.header.get("semblance_input_offset_d") == raw.header.get("d2")
        and panel.header.get("semblance_input_axis2_role") == "signed_offset"
        and panel.header.get("semblance_input_offset_sign_convention")
        == "receiver_minus_source"
        and panel.header.get("semblance_reference_source")
        == "../src-master/system/seismic/Mvscan.c"
    )


def main(argv: Sequence[str] | None = None) -> int:
    output_dir = parse_output_dir("seismic_semblance_contract", argv)
    report = run_pipeline(output_dir)
    metrics = report["metrics"]
    checks = report["checks"]
    assert isinstance(metrics, dict)
    assert isinstance(checks, dict)
    print(f"output_dir={output_dir}")
    print(
        "semblance_contract: "
        f"peak_velocity={metrics['peak_velocity_at_event_m_per_s']:.6g} "
        f"semblance_ratio={metrics['true_to_wrong_semblance_ratio']:.6g} "
        f"stack_ratio={metrics['true_to_wrong_stack_peak_ratio']:.6g} "
        f"overall_pass={checks['overall_pass']}"
    )
    print_outputs(
        [
            output_dir / "s4_semblance_raw_gather.rsf",
            output_dir / "s4_semblance_panel.rsf",
            output_dir / "s4_true_velocity_stack.rsf",
            output_dir / "s4_wrong_velocity_stack.rsf",
            output_dir / "s4_semblance_panel_quicklook.png",
            output_dir / "s4_semblance_qc_report.json",
        ]
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
