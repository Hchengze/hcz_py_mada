"""Demonstrate Ricker wavelet generation for synthetic seismic workflows.

Run from the project root:

    python examples/ricker_demo.py

Optionally pass an output directory:

    python examples/ricker_demo.py ricker_demo_output
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

from pymadagascar.io.rsf import read_rsf
from pymadagascar.signal.wavelet import ricker_rsf, ricker_wavelet


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    output_dir = Path(args[0]) if args else Path("examples") / "ricker_demo_output"
    output_dir.mkdir(parents=True, exist_ok=True)

    wavelet_path = output_dir / "ricker_25hz.rsf"
    frequency = 25.0
    dt = 0.001
    nt = 256
    peak_time = 0.04

    samples = ricker_wavelet(frequency, dt, nt, peak_time=peak_time, amplitude=1.0)
    ricker_rsf(wavelet_path, frequency, dt, nt, peak_time=peak_time)
    loaded = read_rsf(wavelet_path)

    print(f"wrote {wavelet_path}")
    print("")
    print(f"shape: {loaded.data.shape}")
    print(f"dtype: {loaded.data.dtype}")
    print(f"peak sample: {int(np.argmax(samples))}")
    print(f"peak amplitude: {float(np.max(samples)):.6g}")
    print(f"minimum side lobe: {float(np.min(samples)):.6g}")
    print("")
    print("CLI equivalent:")
    print(
        "python -m pymadagascar.cli.ricker "
        f"out={wavelet_path} f={frequency:g} dt={dt:g} nt={nt} peak_time={peak_time:g}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
