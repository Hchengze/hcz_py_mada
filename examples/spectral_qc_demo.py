"""Demo for Stage C-8 window functions and spectral QC.

Run from the project root:
    python examples/spectral_qc_demo.py [output_directory]
"""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile

import numpy as np

from pymadagascar import RSFData
from pymadagascar.io.rsf import RSFHeader, write_rsf
from pymadagascar.signal.spectral import (
    coherence_rsf,
    psd_rsf,
    snr_rsf,
    spectrogram_rsf,
    windowfunc_rsf,
)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    output_dir = (
        Path(args[0])
        if args
        else Path(tempfile.mkdtemp(prefix="pymada_spectral_qc_"))
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(18)
    ntime = 512
    ntrace = 3
    dt = 0.002
    time = np.arange(ntime, dtype=np.float64) * dt
    primary = np.sin(2.0 * np.pi * 18.0 * time)
    interference = 0.35 * np.sin(2.0 * np.pi * 50.0 * time)
    panel = np.vstack(
        [
            primary + interference + 0.08 * rng.standard_normal(ntime)
            for _ in range(ntrace)
        ]
    ).astype(np.float32)
    reference = np.vstack(
        [primary + 0.08 * rng.standard_normal(ntime) for _ in range(ntrace)]
    ).astype(np.float32)

    header = RSFHeader(
        {
            "n1": ntime,
            "o1": 0.0,
            "d1": dt,
            "label1": "Time",
            "unit1": "s",
            "n2": ntrace,
            "o2": 0.0,
            "d2": 5.0,
            "label2": "Channel",
            "unit2": "m",
        }
    )
    paths = {
        "input": output_dir / "spectral_input.rsf",
        "reference": output_dir / "spectral_reference.rsf",
        "windowed": output_dir / "spectral_windowed.rsf",
        "psd": output_dir / "spectral_psd.rsf",
        "coherence": output_dir / "spectral_coherence.rsf",
        "spectrogram": output_dir / "spectral_spectrogram.rsf",
        "snr": output_dir / "spectral_snr.rsf",
        "chain": output_dir / "spectral_chain_psd.rsf",
    }
    write_rsf(paths["input"], panel, header)
    write_rsf(paths["reference"], reference, header)
    windowfunc_rsf(paths["input"], paths["windowed"], kind="hann", axis=1, apply=True)
    psd_rsf(paths["input"], paths["psd"], axis=1, average=True)
    coherence_rsf(
        paths["input"],
        paths["reference"],
        paths["coherence"],
        axis=1,
        nperseg=128,
        noverlap=64,
    )
    spectrogram_rsf(
        paths["input"],
        paths["spectrogram"],
        axis=1,
        nperseg=128,
        noverlap=64,
    )
    snr_rsf(
        paths["input"],
        paths["snr"],
        axis=1,
        signal_window=(96, 448),
        noise_window=(0, 64),
    )

    chained = RSFData(panel, header).windowfunc(kind="hamming").psd(average=True)
    chained.write(paths["chain"])

    print(f"output_dir={output_dir}")
    for name, path in paths.items():
        print(f"{name}={path}")
    print(f"input_shape={panel.shape}")
    print(f"psd_shape={chained.shape}")
    print(f"frequency_spacing={chained.header['d1']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
