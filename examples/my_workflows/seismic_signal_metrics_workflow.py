"""S2 pipeline metrics and QC-report workflow using existing processing APIs.

This deterministic small-gather regression is not a production QC recipe.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from pymadagascar.io.rsf import read_rsf
from pymadagascar.plot._common import pyplot
from pymadagascar.plot.grey import grey
from pymadagascar.seismic.agc import agc_rsf
from pymadagascar.seismic.mute import mutter_rsf
from pymadagascar.seismic.stack import stack_rsf
from pymadagascar.signal.filter import bandpass_rsf
from pymadagascar.signal.qc import demean_rsf, detrend_rsf
from pymadagascar.testing.seismic_fixtures import make_hyperbolic_gather_fixture
from pymadagascar.testing.seismic_metrics import (
    compare_pipeline_metrics,
    compute_gather_pipeline_metrics,
    write_metrics_json,
)

from _common import parse_output_dir, print_outputs


SIGNAL_WINDOW = (100, 163)
NOISE_WINDOW = (300, 450)
TARGET_BAND = (15.0, 35.0)
REJECT_BAND = (60.0, 80.0)
MUTE_T0 = 0.080
MUTE_VELOCITY = 4000.0


def run_pipeline(output_dir: Path) -> dict[str, object]:
    """Run the S2 processing chain and return its internal QC report."""

    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "raw": output_dir / "s2_raw_gather.rsf",
        "demean": output_dir / "s2_demean_gather.rsf",
        "before_filter": output_dir / "s2_detrended_gather.rsf",
        "after_filter": output_dir / "s2_bandpassed_gather.rsf",
        "agc": output_dir / "s2_agc_gather.rsf",
        "processed": output_dir / "s2_processed_gather.rsf",
        "stack": output_dir / "s2_stack.rsf",
        "quicklook": output_dir / "s2_processed_quicklook.png",
        "report": output_dir / "s2_qc_report.json",
    }

    make_hyperbolic_gather_fixture(path=paths["raw"])
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
    stack_rsf(
        paths["processed"],
        paths["stack"],
        axis=2,
        mode="mean",
        nonzero=False,
    )

    raw = read_rsf(paths["raw"])
    before_filter = read_rsf(paths["before_filter"])
    after_filter = read_rsf(paths["after_filter"])
    processed = read_rsf(paths["processed"])
    stack = read_rsf(paths["stack"])
    metrics = compute_gather_pipeline_metrics(
        raw,
        before_filter,
        after_filter,
        processed,
        stack,
        signal_window=SIGNAL_WINDOW,
        noise_window=NOISE_WINDOW,
        target_band=TARGET_BAND,
        reject_band=REJECT_BAND,
        mute_t0=MUTE_T0,
        mute_velocity=MUTE_VELOCITY,
    )
    checks = compare_pipeline_metrics(metrics)

    fig = grey(
        processed.data,
        processed.header,
        output_path=paths["quicklook"],
        title="S2 deterministic pipeline QC gather",
        pclip=99.0,
    )
    pyplot().close(fig)

    report: dict[str, object] = {
        "workflow": "seismic_signal_metrics",
        "stage": "S2",
        "status": "internal_testing_contract",
        "fixture": "hyperbolic_gather",
        "metric_scope": {
            "snr_and_frequency": "detrended gather before/after bandpass",
            "output": "AGC and regular signed-offset mute result",
            "stack": "mean stack of the final processed gather",
        },
        "windows": {
            "signal_samples": list(SIGNAL_WINDOW),
            "noise_samples": list(NOISE_WINDOW),
        },
        "bands_hz": {
            "target": list(TARGET_BAND),
            "reject": list(REJECT_BAND),
        },
        "metrics": metrics,
        "checks": checks,
    }
    write_metrics_json(paths["report"], report)
    return report


def main(argv: Sequence[str] | None = None) -> int:
    output_dir = parse_output_dir("seismic_signal_metrics", argv)
    report = run_pipeline(output_dir)
    metrics = report["metrics"]
    checks = report["checks"]
    assert isinstance(metrics, dict)
    assert isinstance(checks, dict)
    print(f"output_dir={output_dir}")
    print(
        "qc: "
        f"snr_improvement_db={metrics['snr_improvement_db']:.6g} "
        f"target_ratio={metrics['target_band_energy_ratio']:.6g} "
        f"reject_ratio={metrics['reject_band_energy_ratio']:.6g} "
        f"stack_noise_ratio={metrics['stack_noise_reduction_ratio']:.6g} "
        f"overall_pass={checks['overall_pass']}"
    )
    print_outputs(
        [
            output_dir / "s2_raw_gather.rsf",
            output_dir / "s2_processed_gather.rsf",
            output_dir / "s2_stack.rsf",
            output_dir / "s2_processed_quicklook.png",
            output_dir / "s2_qc_report.json",
        ]
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
