"""Demo for Stage C-7 signal and small-gather QC foundations.

Run from the project root:
    python examples/signal_qc_foundation_demo.py [output_directory]
"""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile

import numpy as np

from pymadagascar import RSFData
from pymadagascar.io.rsf import RSFHeader, write_rsf
from pymadagascar.signal.qc import bandstop_rsf, localrms_rsf


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    output_dir = (
        Path(args[0])
        if args
        else Path(tempfile.mkdtemp(prefix="pymada_signal_qc_"))
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(7)
    ntime = 1000
    ntrace = 4
    dt = 0.001
    time = np.arange(ntime, dtype=np.float64) * dt
    clean = np.sin(2.0 * np.pi * 12.0 * time)
    interference = 0.45 * np.sin(2.0 * np.pi * 50.0 * time)
    panel = np.vstack(
        [
            clean + interference + 0.6 * time + 0.4 * trace
            for trace in range(ntrace)
        ]
    )
    panel += 0.05 * rng.standard_normal(panel.shape)
    panel = panel.astype(np.float32)

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
        "input": output_dir / "signal_qc_input.rsf",
        "bandstop": output_dir / "signal_qc_bandstop.rsf",
        "localrms": output_dir / "signal_qc_localrms.rsf",
        "chain": output_dir / "signal_qc_chain.rsf",
    }
    write_rsf(paths["input"], panel, header)
    bandstop_rsf(paths["input"], paths["bandstop"], fmin=47.0, fmax=53.0, axis=1, taper=1.0)
    localrms_rsf(paths["bandstop"], paths["localrms"], rect=41, axis=1)

    chained = (
        RSFData(panel, header)
        .demean(axis=1)
        .detrend(axis=1, type="linear")
        .notch(axis=1, f0=50.0, width=6.0, taper=1.0)
        .decimate(4, axis=1, anti_alias=True)
        .localrms(axis=1, rect=11)
    )
    chained.write(paths["chain"])

    print(f"output_dir={output_dir}")
    for name, path in paths.items():
        print(f"{name}={path}")
    print(f"input_shape={panel.shape}")
    print(f"chain_shape={chained.shape}")
    print(f"chain_d1={chained.header['d1']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
