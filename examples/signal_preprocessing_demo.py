"""Demo for Stage C-1 signal preprocessing tools.

Run from the project root:
    python examples/signal_preprocessing_demo.py
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

from pymadagascar import RSFData
from pymadagascar.io.rsf import RSFHeader, write_rsf
from pymadagascar.signal.preprocessing import costaper_rsf, envelope_rsf, spectra_rsf, threshold_rsf


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    output_dir = Path(args[0]) if args else Path("signal_preprocessing_output")
    output_dir.mkdir(parents=True, exist_ok=True)

    input_path = output_dir / "synthetic_panel.rsf"
    tapered_path = output_dir / "synthetic_tapered.rsf"
    threshold_path = output_dir / "synthetic_thresholded.rsf"
    spectra_path = output_dir / "synthetic_spectra.rsf"
    envelope_path = output_dir / "synthetic_envelope.rsf"
    chained_path = output_dir / "synthetic_chain.rsf"

    n1 = 128
    n2 = 4
    dt = 0.004
    time = np.arange(n1, dtype=np.float32) * dt
    traces = []
    for itrace in range(n2):
        signal = np.sin(2.0 * np.pi * (12.0 + itrace) * time)
        signal += 0.35 * np.sin(2.0 * np.pi * 32.0 * time)
        signal += 0.05 * itrace
        traces.append(signal)
    panel = np.asarray(traces, dtype=np.float32)
    header = RSFHeader(
        {
            "n1": n1,
            "o1": 0.0,
            "d1": dt,
            "label1": "Time",
            "unit1": "s",
            "n2": n2,
            "o2": 0.0,
            "d2": 1.0,
            "label2": "Trace",
        }
    )
    write_rsf(input_path, panel, header)

    costaper_rsf(input_path, tapered_path, widths={1: 8, 2: 1})
    threshold_rsf(tapered_path, threshold_path, value=0.15, mode="soft")
    spectra_rsf(threshold_path, spectra_path, axis=1, mode="amplitude", average=True)
    envelope_rsf(threshold_path, envelope_path, axis=1)

    chained = RSFData(panel, header).costaper(widths={1: 8}).threshold(value=0.15, mode="hard").envelope(axis=1)
    chained.write(chained_path)

    print(f"output_dir={output_dir}")
    for path in [input_path, tapered_path, threshold_path, spectra_path, envelope_path, chained_path]:
        print(f"wrote {path}")
    print(f"RSFData chain shape={chained.shape}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
