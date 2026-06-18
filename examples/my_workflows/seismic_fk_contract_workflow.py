"""S4-3 FK prototype source-aligned contract workflow.

This deterministic workflow validates the current Python FK prototype against
small regular plane-wave fixtures.  It is not a full ``sfdipfilter`` clone and
does not call original Madagascar.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import numpy as np

from pymadagascar.io.rsf import RSFArray, RSFHeader, read_rsf, write_rsf
from pymadagascar.plot._common import pyplot
from pymadagascar.plot.grey import grey
from pymadagascar.seismic.fk import centered_frequency_axis, fk_filter, fk_spectrum
from pymadagascar.testing.seismic_metrics import write_metrics_json

from _common import parse_output_dir, print_outputs


NT = 256
NX = 64
DT = 0.004
DX = 10.0
FREQUENCY_BIN = 20
TARGET_WAVENUMBER_BIN = 8
REJECT_WAVENUMBER_BIN = 20
FREQUENCY_HZ = FREQUENCY_BIN / (NT * DT)
TARGET_WAVENUMBER_1_PER_M = TARGET_WAVENUMBER_BIN / (NX * DX)
REJECT_WAVENUMBER_1_PER_M = REJECT_WAVENUMBER_BIN / (NX * DX)
TARGET_VELOCITY_M_PER_S = FREQUENCY_HZ / TARGET_WAVENUMBER_1_PER_M
REJECT_VELOCITY_M_PER_S = FREQUENCY_HZ / REJECT_WAVENUMBER_1_PER_M
PASS_VMIN = 1200.0
PASS_VMAX = 1800.0


def run_pipeline(output_dir: Path) -> dict[str, object]:
    """Run the bounded S4-3 FK prototype regression and return its report."""

    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "raw": output_dir / "s4_fk_raw_panel.rsf",
        "spectrum": output_dir / "s4_fk_spectrum.rsf",
        "filtered": output_dir / "s4_fk_filtered_panel.rsf",
        "quicklook": output_dir / "s4_fk_spectrum_quicklook.png",
        "report": output_dir / "s4_fk_qc_report.json",
    }

    target = _plane_wave(TARGET_WAVENUMBER_BIN, sign=1, amplitude=1.0)
    reject = _plane_wave(REJECT_WAVENUMBER_BIN, sign=-1, amplitude=0.5)
    mixed = (target + reject).astype(np.float32)
    write_rsf(paths["raw"], mixed, _panel_header())

    fk_spectrum(paths["raw"], paths["spectrum"])
    fk_filter(paths["raw"], paths["filtered"], vmin=PASS_VMIN, vmax=PASS_VMAX)

    raw = read_rsf(paths["raw"])
    spectrum = read_rsf(paths["spectrum"])
    filtered = read_rsf(paths["filtered"])
    metrics = _fk_metrics(raw, spectrum, filtered, target, reject)
    checks = _fk_checks(metrics)

    fig = grey(
        spectrum.data,
        spectrum.header,
        output_path=paths["quicklook"],
        title="S4-3 FK prototype contract spectrum",
        pclip=99.0,
    )
    pyplot().close(fig)

    report: dict[str, object] = {
        "workflow": "seismic_fk_contract",
        "stage": "S4-3",
        "status": "prototype_contract_regression",
        "fixture": "regular_plane_wave_panel",
        "madagascar_reference": "../src-master/system/generic/Mdipfilter.c",
        "direct_mfk_source_found": False,
        "parameters": {
            "frequency_hz": FREQUENCY_HZ,
            "target_wavenumber_1_per_m": TARGET_WAVENUMBER_1_PER_M,
            "reject_wavenumber_1_per_m": REJECT_WAVENUMBER_1_PER_M,
            "target_velocity_m_per_s": TARGET_VELOCITY_M_PER_S,
            "reject_velocity_m_per_s": REJECT_VELOCITY_M_PER_S,
            "pass_vmin_m_per_s": PASS_VMIN,
            "pass_vmax_m_per_s": PASS_VMAX,
            "regular_spatial_axis": True,
            "not_sfdipfilter_clone": True,
        },
        "contracts": {
            "data": "finite small 2D panel, NumPy shape (nspace, ntime)",
            "geometry": "regular spatial axis only; explicit offsets not consumed",
            "fk_velocity": "abs(frequency)/abs(wavenumber)",
            "segy_trace_header": "out_of_scope",
        },
        "metrics": metrics,
        "checks": checks,
    }
    write_metrics_json(paths["report"], report)
    return report


def _panel_header() -> RSFHeader:
    return RSFHeader(
        {
            "n1": NT,
            "o1": 0.0,
            "d1": DT,
            "label1": "Time",
            "unit1": "s",
            "n2": NX,
            "o2": 0.0,
            "d2": DX,
            "label2": "Channel X",
            "unit2": "m",
            "axis2_role": "regular_spatial_coordinate",
            "coordinate_sampling": "regular",
        }
    )


def _plane_wave(wavenumber_bin: int, *, sign: int, amplitude: float) -> np.ndarray:
    time = DT * np.arange(NT, dtype=np.float64)
    space = DX * np.arange(NX, dtype=np.float64)
    wavenumber = wavenumber_bin / (NX * DX)
    phase = 2.0 * np.pi * (
        FREQUENCY_HZ * time.reshape(1, NT)
        + sign * wavenumber * space.reshape(NX, 1)
    )
    return (amplitude * np.cos(phase)).astype(np.float32)


def _fk_metrics(
    raw: RSFArray,
    spectrum: RSFArray,
    filtered: RSFArray,
    target: np.ndarray,
    reject: np.ndarray,
) -> dict[str, float | bool]:
    peak_frequency, peak_wavenumber, peak_amplitude = _positive_frequency_peak(spectrum)
    before_coefficients = _basis_coefficients(raw.data, target, reject)
    after_coefficients = _basis_coefficients(filtered.data, target, reject)
    sample_count = raw.data.size + spectrum.data.size + filtered.data.size
    finite_count = sum(
        int(np.count_nonzero(np.isfinite(item.data)))
        for item in (raw, spectrum, filtered)
    )
    return {
        "expected_frequency_hz": FREQUENCY_HZ,
        "expected_target_wavenumber_1_per_m": TARGET_WAVENUMBER_1_PER_M,
        "expected_reject_wavenumber_1_per_m": REJECT_WAVENUMBER_1_PER_M,
        "peak_frequency_hz": peak_frequency,
        "peak_wavenumber_1_per_m": peak_wavenumber,
        "peak_amplitude": peak_amplitude,
        "target_velocity_m_per_s": TARGET_VELOCITY_M_PER_S,
        "reject_velocity_m_per_s": REJECT_VELOCITY_M_PER_S,
        "target_coefficient_before": before_coefficients[0],
        "target_coefficient_after": after_coefficients[0],
        "reject_coefficient_before": before_coefficients[1],
        "reject_coefficient_after": after_coefficients[1],
        "target_preservation_ratio": _ratio(after_coefficients[0], before_coefficients[0]),
        "reject_suppression_ratio": _ratio(abs(after_coefficients[1]), abs(before_coefficients[1])),
        "input_rms": _rms(raw.data),
        "filtered_rms": _rms(filtered.data),
        "finite_fraction": float(finite_count / sample_count),
        "header_axis_ok": _headers_ok(raw, spectrum, filtered),
    }


def _fk_checks(metrics: dict[str, float | bool]) -> dict[str, bool]:
    frequency_tolerance = 0.5 / (NT * DT)
    wavenumber_tolerance = 0.5 / (NX * DX)
    checks = {
        "peak_frequency_near_expected": abs(
            float(metrics["peak_frequency_hz"]) - FREQUENCY_HZ
        )
        <= frequency_tolerance,
        "peak_wavenumber_near_expected": abs(
            float(metrics["peak_wavenumber_1_per_m"])
            - TARGET_WAVENUMBER_1_PER_M
        )
        <= wavenumber_tolerance,
        "target_slope_preserved": float(metrics["target_preservation_ratio"]) >= 0.90,
        "reject_slope_suppressed": float(metrics["reject_suppression_ratio"]) <= 0.20,
        "finite": bool(np.isclose(float(metrics["finite_fraction"]), 1.0)),
        "header_axis_ok": bool(metrics["header_axis_ok"]),
    }
    checks["overall_pass"] = bool(all(checks.values()))
    return checks


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


def _basis_coefficients(data: np.ndarray, target: np.ndarray, reject: np.ndarray) -> tuple[float, float]:
    design = np.stack([target.ravel(), reject.ravel()], axis=1).astype(np.float64)
    coefficients = np.linalg.lstsq(design, np.asarray(data, dtype=np.float64).ravel(), rcond=None)[0]
    return float(coefficients[0]), float(coefficients[1])


def _ratio(numerator: float, denominator: float) -> float:
    return float(numerator / max(denominator, np.finfo(np.float64).eps))


def _rms(data: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(np.asarray(data, dtype=np.float64)))))


def _headers_ok(raw: RSFArray, spectrum: RSFArray, filtered: RSFArray) -> bool:
    return bool(
        raw.data.shape == (NX, NT)
        and raw.header.get("label1") == "Time"
        and raw.header.get("unit1") == "s"
        and raw.header.get("label2") == "Channel X"
        and raw.header.get("unit2") == "m"
        and raw.header.get("coordinate_sampling") == "regular"
        and spectrum.data.shape == raw.data.shape
        and spectrum.header.get("label1") == "Frequency"
        and spectrum.header.get("unit1") == "Hz"
        and spectrum.header.get("label2") == "Wavenumber"
        and spectrum.header.get("unit2") == "1/m"
        and spectrum.header.get("fk_reference_source")
        == "../src-master/system/generic/Mdipfilter.c"
        and spectrum.header.get("fk_madagascar_equivalence")
        == "no_direct_Mfk_transform_found"
        and filtered.data.shape == raw.data.shape
        and filtered.header.get("label1") == raw.header.get("label1")
        and filtered.header.get("label2") == raw.header.get("label2")
        and filtered.header.get("fkfilter_reference_source")
        == "../src-master/system/generic/Mdipfilter.c"
        and filtered.header.get("fkfilter_madagascar_equivalence")
        == "not_sfdipfilter_clone"
    )


def main(argv: Sequence[str] | None = None) -> int:
    output_dir = parse_output_dir("seismic_fk_contract", argv)
    report = run_pipeline(output_dir)
    metrics = report["metrics"]
    checks = report["checks"]
    assert isinstance(metrics, dict)
    assert isinstance(checks, dict)
    print(f"output_dir={output_dir}")
    print(
        "fk_contract: "
        f"peak_frequency={metrics['peak_frequency_hz']:.6g} "
        f"peak_wavenumber={metrics['peak_wavenumber_1_per_m']:.6g} "
        f"target_ratio={metrics['target_preservation_ratio']:.6g} "
        f"reject_ratio={metrics['reject_suppression_ratio']:.6g} "
        f"overall_pass={checks['overall_pass']}"
    )
    print_outputs(
        [
            output_dir / "s4_fk_raw_panel.rsf",
            output_dir / "s4_fk_spectrum.rsf",
            output_dir / "s4_fk_filtered_panel.rsf",
            output_dir / "s4_fk_spectrum_quicklook.png",
            output_dir / "s4_fk_qc_report.json",
        ]
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
