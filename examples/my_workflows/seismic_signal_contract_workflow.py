"""S1 contract workflow built only from existing pymadagascar processing APIs.

The workflow is a deterministic regression fixture, not a production seismic
processing recipe.
"""

from __future__ import annotations

from collections.abc import Sequence
import json
from pathlib import Path

import numpy as np

from pymadagascar.io.rsf import read_rsf
from pymadagascar.plot._common import pyplot
from pymadagascar.plot.grey import grey
from pymadagascar.seismic.agc import agc_rsf
from pymadagascar.seismic.mute import mutter_rsf
from pymadagascar.seismic.stack import stack_rsf
from pymadagascar.signal.filter import bandpass_rsf
from pymadagascar.signal.qc import demean_rsf, detrend_rsf
from pymadagascar.signal.spectral import psd_rsf
from pymadagascar.testing.seismic_fixtures import make_hyperbolic_gather_fixture

from _common import parse_output_dir, print_outputs


def run_pipeline(output_dir: Path) -> dict[str, object]:
    """Run the S1 fixture pipeline and return deterministic acceptance metrics."""

    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "raw": output_dir / "s1_synthetic_gather.rsf",
        "demean": output_dir / "s1_demean.rsf",
        "detrend": output_dir / "s1_detrend.rsf",
        "bandpass": output_dir / "s1_bandpass.rsf",
        "agc": output_dir / "s1_agc.rsf",
        "processed": output_dir / "s1_processed_gather.rsf",
        "stack": output_dir / "s1_stack.rsf",
        "psd": output_dir / "s1_stack_psd.rsf",
        "quicklook": output_dir / "s1_processed_quicklook.png",
        "metrics": output_dir / "s1_metrics.json",
    }

    make_hyperbolic_gather_fixture(path=paths["raw"])
    demean_rsf(paths["raw"], paths["demean"], axis=1, nan_policy="raise")
    detrend_rsf(paths["demean"], paths["detrend"], axis=1, type="linear", nan_policy="raise")
    bandpass_rsf(
        paths["detrend"],
        paths["bandpass"],
        flo=8.0,
        fhi=45.0,
        axis=1,
        taper=5.0,
    )
    agc_rsf(paths["bandpass"], paths["agc"], rect=0.080, axis=1)
    mutter_rsf(
        paths["agc"],
        paths["processed"],
        time_axis=1,
        offset_axis=2,
        t0=0.080,
        v=4000.0,
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
    psd_rsf(paths["stack"], paths["psd"], axis=1, window="hann", scaling="density")

    raw = read_rsf(paths["raw"])
    detrended = read_rsf(paths["detrend"])
    bandpassed = read_rsf(paths["bandpass"])
    processed = read_rsf(paths["processed"])
    stacked = read_rsf(paths["stack"])
    spectrum = read_rsf(paths["psd"])

    fig = grey(
        processed.data,
        processed.header,
        output_path=paths["quicklook"],
        title="S1 deterministic processed gather",
        pclip=99.0,
    )
    pyplot().close(fig)

    metrics = _pipeline_metrics(
        raw.data,
        detrended.data,
        bandpassed.data,
        processed.data,
        stacked.data,
        dt=float(raw.header["d1"]),
        offset_o=float(raw.header["o2"]),
        offset_d=float(raw.header["d2"]),
    )
    payload: dict[str, object] = {
        "workflow": "seismic_topic_s1_contract_regression",
        "status": "internal_testing_contract",
        "data_layout": "RSF axis 1 is time; NumPy gather shape is (trace, time).",
        "geometry": {
            "axis2": "regular signed offset",
            "offset_sign": "receiver_minus_source",
            "source_receiver_geometry": "not encoded",
            "trace_headers": "ordinary RSF only; no SEG-Y trace-header model",
        },
        "pipeline": [
            "demean",
            "detrend",
            "bandpass",
            "agc",
            "mutter",
            "stack",
            "psd",
        ],
        "shapes": {
            "raw": list(raw.data.shape),
            "processed": list(processed.data.shape),
            "stack": list(stacked.data.shape),
            "psd": list(spectrum.data.shape),
        },
        "metrics": metrics,
    }
    paths["metrics"].write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def _pipeline_metrics(
    raw: np.ndarray,
    detrended: np.ndarray,
    bandpassed: np.ndarray,
    processed: np.ndarray,
    stacked: np.ndarray,
    *,
    dt: float,
    offset_o: float,
    offset_d: float,
) -> dict[str, float | bool]:
    frequencies = np.fft.rfftfreq(raw.shape[-1], d=dt)
    source_spectrum = np.mean(np.abs(np.fft.rfft(detrended, axis=-1)), axis=0)
    filtered_spectrum = np.mean(np.abs(np.fft.rfft(bandpassed, axis=-1)), axis=0)
    pass_index = int(np.argmin(np.abs(frequencies - 24.0)))
    stop_index = int(np.argmin(np.abs(frequencies - 70.0)))
    eps = np.finfo(np.float64).eps
    passband_ratio = float(
        filtered_spectrum[pass_index] / max(source_spectrum[pass_index], eps)
    )
    stopband_ratio = float(
        filtered_spectrum[stop_index] / max(source_spectrum[stop_index], eps)
    )

    offsets = offset_o + offset_d * np.arange(processed.shape[0], dtype=np.float64)
    time = dt * np.arange(processed.shape[1], dtype=np.float64)
    mute_boundary = 0.080 + np.abs(offsets) / 4000.0
    muted_region = time[None, :] < mute_boundary[:, None]
    mute_max = float(np.max(np.abs(processed[muted_region])))

    tail = time >= 1.2
    trace_noise_rms = float(np.sqrt(np.mean(np.square(processed[:, tail]))))
    stack_noise_rms = float(np.sqrt(np.mean(np.square(stacked[tail]))))
    return {
        "all_finite": bool(
            np.all(np.isfinite(raw))
            and np.all(np.isfinite(processed))
            and np.all(np.isfinite(stacked))
        ),
        "shape_preserved_before_stack": bool(processed.shape == raw.shape),
        "passband_amplitude_ratio": passband_ratio,
        "stopband_amplitude_ratio": stopband_ratio,
        "mute_preboundary_max_abs": mute_max,
        "trace_tail_noise_rms": trace_noise_rms,
        "stack_tail_noise_rms": stack_noise_rms,
        "stack_noise_ratio": stack_noise_rms / max(trace_noise_rms, eps),
        "processed_checksum": float(np.sum(processed, dtype=np.float64)),
        "stack_checksum": float(np.sum(stacked, dtype=np.float64)),
    }


def main(argv: Sequence[str] | None = None) -> int:
    output_dir = parse_output_dir("seismic_signal_contract", argv)
    payload = run_pipeline(output_dir)
    metrics = payload["metrics"]
    assert isinstance(metrics, dict)
    print(f"output_dir={output_dir}")
    print(
        "acceptance: "
        f"passband_ratio={metrics['passband_amplitude_ratio']:.6g} "
        f"stopband_ratio={metrics['stopband_amplitude_ratio']:.6g} "
        f"stack_noise_ratio={metrics['stack_noise_ratio']:.6g}"
    )
    print_outputs(
        [
            output_dir / "s1_synthetic_gather.rsf",
            output_dir / "s1_processed_gather.rsf",
            output_dir / "s1_stack.rsf",
            output_dir / "s1_stack_psd.rsf",
            output_dir / "s1_processed_quicklook.png",
            output_dir / "s1_metrics.json",
        ]
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
