"""S6-2 small slant-stack contract workflow.

This deterministic workflow validates the current Python Radon/slant prototype
as a small sfslant-style operator pair.  ``radon`` is treated as the adjoint
slant stack (``m = A^T d``), while ``iradon`` is deterministic modeling
(``d = A m``).  It is not a high-resolution ``sfradon`` implementation and
does not call original Madagascar.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import numpy as np

from pymadagascar.io.rsf import RSFArray, RSFHeader, read_rsf, write_rsf
from pymadagascar.plot._common import pyplot
from pymadagascar.plot.grey import grey
from pymadagascar.seismic.radon import (
    inverse_linear_radon,
    linear_radon,
    radon_adjoint_array,
    radon_model_array,
)
from pymadagascar.testing.seismic_metrics import write_metrics_json

from _common import parse_output_dir, print_outputs


NT = 256
NX = 31
DT = 0.004
DX = 10.0
OX = -150.0
TAU0 = 0.448
P_TRUE = 0.0004
P_WRONG = -0.0004
PMIN = -0.0008
PMAX = 0.0008
DP = 0.0002
FPEAK = 24.0


def run_pipeline(output_dir: Path) -> dict[str, object]:
    """Run the bounded S6-2 slant-stack regression and return its report."""

    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "gather": output_dir / "s6_slant_raw_gather.rsf",
        "panel": output_dir / "s6_slant_panel.rsf",
        "model": output_dir / "s6_slant_model.rsf",
        "modeled": output_dir / "s6_slant_modeled_gather.rsf",
        "quicklook": output_dir / "s6_slant_panel_quicklook.png",
        "report": output_dir / "s6_slant_stack_qc_report.json",
    }

    offsets = _offsets()
    tau = _tau()
    p_values = _p_values()
    gather_data = _linear_event(P_TRUE).astype(np.float32)
    write_rsf(paths["gather"], gather_data, _gather_header())

    linear_radon(paths["gather"], paths["panel"], pmin=PMIN, pmax=PMAX, dp=DP)
    panel = read_rsf(paths["panel"])

    model_data = _model_event(p_values).astype(np.float32)
    write_rsf(paths["model"], model_data, _model_header(p_values))
    inverse_linear_radon(paths["model"], paths["modeled"])
    modeled = read_rsf(paths["modeled"])

    metrics = _slant_metrics(panel, modeled, gather_data, model_data, tau, offsets, p_values)
    checks = _slant_checks(metrics)

    fig = grey(
        panel.data,
        panel.header,
        output_path=paths["quicklook"],
        title="S6-2 small slant-stack contract panel",
        pclip=99.0,
    )
    pyplot().close(fig)

    report: dict[str, object] = {
        "workflow": "seismic_slant_stack_contract",
        "stage": "S6-2",
        "status": "prototype_contract_regression",
        "fixture": "analytic_linear_slant_event",
        "operator_direction": {
            "radon": "adjoint_slant_stack_m_equals_A_transpose_d",
            "iradon": "modeling_d_equals_A_m",
            "solved_inverse": False,
        },
        "madagascar_reference": "../src-master/system/seismic/Mslant.c and slant.c",
        "sfradon_equivalence": "not_sfradon",
        "parameters": {
            "nt": NT,
            "nx": NX,
            "dt_s": DT,
            "dx_m": DX,
            "ox_m": OX,
            "tau0_s": TAU0,
            "true_slope_s_per_m": P_TRUE,
            "wrong_slope_s_per_m": P_WRONG,
            "pmin_s_per_m": PMIN,
            "pmax_s_per_m": PMAX,
            "dp_s_per_m": DP,
        },
        "contracts": {
            "data": "finite small 2D gather, NumPy shape (ntrace, ntime)",
            "geometry": "regular signed offset axis or length-compatible explicit offset vector",
            "radon": "adjoint slant-stack A^T d",
            "iradon": "modeling A m",
            "segy_trace_header": "out_of_scope",
        },
        "metrics": metrics,
        "checks": checks,
    }
    write_metrics_json(paths["report"], report)
    return report


def _gather_header() -> RSFHeader:
    return RSFHeader(
        {
            "n1": NT,
            "o1": 0.0,
            "d1": DT,
            "label1": "Time",
            "unit1": "s",
            "n2": NX,
            "o2": OX,
            "d2": DX,
            "label2": "Signed Offset",
            "unit2": "m",
            "axis2_role": "signed_offset",
            "coordinate_sampling": "regular",
            "offset_sign_convention": "receiver_minus_source",
        }
    )


def _model_header(p_values: np.ndarray) -> RSFHeader:
    return RSFHeader(
        {
            "n1": NT,
            "o1": 0.0,
            "d1": DT,
            "label1": "Tau",
            "unit1": "s",
            "n2": p_values.size,
            "o2": float(p_values[0]),
            "d2": float(p_values[1] - p_values[0]),
            "label2": "Slowness",
            "unit2": "s/m",
            "axis2_role": "slowness",
            "radon_kind": "linear",
            "radon_nx": NX,
            "radon_ox": OX,
            "radon_dx": DX,
            "radon_x0": 1.0,
            "radon_time_label": "Time",
            "radon_time_unit": "s",
            "radon_offset_label": "Signed Offset",
            "radon_offset_unit": "m",
        }
    )


def _tau() -> np.ndarray:
    return DT * np.arange(NT, dtype=np.float64)


def _offsets() -> np.ndarray:
    return OX + DX * np.arange(NX, dtype=np.float64)


def _p_values() -> np.ndarray:
    return PMIN + DP * np.arange(int(round((PMAX - PMIN) / DP)) + 1, dtype=np.float64)


def _linear_event(p_value: float) -> np.ndarray:
    tau = _tau()
    offsets = _offsets()
    arrivals = TAU0 + p_value * offsets.reshape(NX, 1)
    return _ricker(tau.reshape(1, NT) - arrivals)


def _model_event(p_values: np.ndarray) -> np.ndarray:
    model = np.zeros((p_values.size, NT), dtype=np.float64)
    true_index = int(np.argmin(np.abs(p_values - P_TRUE)))
    model[true_index] = _ricker(_tau() - TAU0)
    return model


def _ricker(time: np.ndarray) -> np.ndarray:
    arg = np.pi * FPEAK * time
    return (1.0 - 2.0 * arg * arg) * np.exp(-(arg * arg))


def _slant_metrics(
    panel: RSFArray,
    modeled: RSFArray,
    gather_data: np.ndarray,
    model_data: np.ndarray,
    tau: np.ndarray,
    offsets: np.ndarray,
    p_values: np.ndarray,
) -> dict[str, float | bool]:
    panel_data = np.asarray(panel.data, dtype=np.float64)
    true_index = int(np.argmin(np.abs(p_values - P_TRUE)))
    wrong_index = int(np.argmin(np.abs(p_values - P_WRONG)))
    tau_index = int(round(TAU0 / DT))
    true_peak = float(np.max(np.abs(panel_data[true_index, tau_index - 2 : tau_index + 3])))
    wrong_peak = float(np.max(np.abs(panel_data[wrong_index, tau_index - 2 : tau_index + 3])))
    peak_index = np.unravel_index(int(np.argmax(np.abs(panel_data))), panel_data.shape)

    modeled_peak_error = _modeled_peak_error(modeled.data, offsets)
    dot_error = _dot_test_error(tau, offsets, p_values)
    sample_count = panel.data.size + modeled.data.size
    finite_count = int(np.count_nonzero(np.isfinite(panel.data))) + int(
        np.count_nonzero(np.isfinite(modeled.data))
    )
    reconstructed = radon_model_array(
        panel_data.astype(np.float32),
        tau,
        offsets,
        p_values,
    )
    return {
        "expected_slope_s_per_m": P_TRUE,
        "wrong_slope_s_per_m": P_WRONG,
        "peak_slope_s_per_m": float(p_values[peak_index[0]]),
        "expected_tau_s": TAU0,
        "peak_tau_s": float(tau[peak_index[1]]),
        "true_slope_peak": true_peak,
        "wrong_slope_peak": wrong_peak,
        "true_to_wrong_peak_ratio": true_peak / max(wrong_peak, np.finfo(np.float64).eps),
        "modeled_peak_max_abs_error_s": modeled_peak_error,
        "dot_test_relative_error": dot_error,
        "radon_then_iradon_shape_ok": bool(reconstructed.shape == gather_data.shape),
        "finite_fraction": float(finite_count / sample_count),
        "header_axis_ok": _headers_ok(panel, modeled),
        "model_peak_amplitude": float(np.max(model_data)),
    }


def _slant_checks(metrics: dict[str, float | bool]) -> dict[str, bool]:
    checks = {
        "peak_slope_near_true": abs(
            float(metrics["peak_slope_s_per_m"]) - P_TRUE
        )
        <= 0.5 * DP,
        "peak_tau_near_expected": abs(float(metrics["peak_tau_s"]) - TAU0) <= DT,
        "true_slope_beats_wrong": float(metrics["true_to_wrong_peak_ratio"]) >= 3.0,
        "modeling_event_predictable": float(metrics["modeled_peak_max_abs_error_s"]) <= 2.0 * DT,
        "dot_test_consistent": float(metrics["dot_test_relative_error"]) <= 1e-5,
        "radon_then_iradon_shape_ok": bool(metrics["radon_then_iradon_shape_ok"]),
        "finite": bool(np.isclose(float(metrics["finite_fraction"]), 1.0)),
        "header_axis_ok": bool(metrics["header_axis_ok"]),
    }
    checks["overall_pass"] = bool(all(checks.values()))
    return checks


def _modeled_peak_error(data: np.ndarray, offsets: np.ndarray) -> float:
    values = np.asarray(data, dtype=np.float64)
    errors = []
    for ix, offset in enumerate(offsets):
        expected = TAU0 + P_TRUE * offset
        peak_time = int(np.argmax(np.abs(values[ix]))) * DT
        errors.append(abs(peak_time - expected))
    return float(np.max(errors))


def _dot_test_error(tau: np.ndarray, offsets: np.ndarray, p_values: np.ndarray) -> float:
    rng = np.random.default_rng(6202)
    model = rng.normal(size=(p_values.size, tau.size)).astype(np.float32)
    data = rng.normal(size=(offsets.size, tau.size)).astype(np.float32)
    modeled = radon_model_array(model, tau, offsets, p_values)
    adjoint = radon_adjoint_array(data, tau, offsets, p_values)
    lhs = float(np.vdot(modeled, data))
    rhs = float(np.vdot(model, adjoint))
    return float(abs(lhs - rhs) / max(abs(lhs), abs(rhs), np.finfo(np.float64).eps))


def _headers_ok(panel: RSFArray, modeled: RSFArray) -> bool:
    return bool(
        panel.data.shape == (_p_values().size, NT)
        and panel.header.get("label1") == "Tau"
        and panel.header.get("label2") == "Slowness"
        and panel.header.get("unit2") == "s/m"
        and panel.header.get("radon_direction") == "adjoint_slant_stack"
        and panel.header.get("radon_operator_form") == "m=A^T d"
        and panel.header.get("radon_sfradon_equivalence") == "not_sfradon"
        and modeled.data.shape == (NX, NT)
        and modeled.header.get("label1") == "Time"
        and modeled.header.get("label2") == "Signed Offset"
        and modeled.header.get("unit2") == "m"
        and modeled.header.get("radon_direction") == "modeling"
        and modeled.header.get("radon_operator_form") == "d=A m"
    )


def main(argv: Sequence[str] | None = None) -> int:
    output_dir = parse_output_dir("seismic_slant_stack_contract", argv)
    report = run_pipeline(output_dir)
    metrics = report["metrics"]
    checks = report["checks"]
    print(f"output_dir={output_dir}")
    print_outputs(
        [
            output_dir / "s6_slant_raw_gather.rsf",
            output_dir / "s6_slant_panel.rsf",
            output_dir / "s6_slant_modeled_gather.rsf",
            output_dir / "s6_slant_panel_quicklook.png",
            output_dir / "s6_slant_stack_qc_report.json",
        ]
    )
    print(
        "Slant-stack S6-2 metrics: "
        f"peak_slope={metrics['peak_slope_s_per_m']:.6g} s/m, "
        f"true/wrong={metrics['true_to_wrong_peak_ratio']:.2f}, "
        f"dot_error={metrics['dot_test_relative_error']:.3g}, "
        f"overall_pass={checks['overall_pass']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
