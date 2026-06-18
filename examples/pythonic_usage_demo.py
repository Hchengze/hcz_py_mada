"""Demonstrate the high-level RSFData API.

Run from the repository root:

    python examples/pythonic_usage_demo.py
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

from pymadagascar import read, write
from pymadagascar.io.rsf import RSFHeader
from pymadagascar.plot._common import pyplot


def main(argv: list[str] | None = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)
    outdir = Path(args[0]) if args else Path("examples") / "_output"
    outdir.mkdir(parents=True, exist_ok=True)

    n1 = 512
    n2 = 24
    dt = 0.002
    t = np.arange(n1, dtype=np.float64) * dt
    offsets = np.arange(n2, dtype=np.float64)
    signal = np.sin(2.0 * np.pi * 25.0 * t)
    noise = 0.2 * np.sin(2.0 * np.pi * 140.0 * t)
    panel = np.stack([(1.0 + 0.01 * offset) * (signal + noise) for offset in offsets]).astype(
        np.float32
    )

    header = RSFHeader(
        {
            "o1": 0.0,
            "d1": dt,
            "label1": "Time",
            "unit1": "s",
            "o2": 0.0,
            "d2": 25.0,
            "label2": "Offset",
            "unit2": "m",
        }
    )

    input_path = outdir / "pythonic_input.rsf"
    output_path = outdir / "pythonic_processed.rsf"
    png_path = outdir / "pythonic_processed.png"

    write(input_path, panel, header)

    processed = (
        read(input_path)
        .window(axis=1, f=0, n=400)
        .bandpass(flo=5.0, fhi=80.0)
        .agc(rect=0.12)
    )
    written = processed.write(output_path)
    stats = written.attr()

    fig = written.plot_grey(output_path=png_path, pclip=99.0, colorbar=False)
    pyplot().close(fig)

    print(f"Wrote {output_path} shape={written.shape} dtype={written.dtype}")
    print(f"min={stats['min']:.4g} max={stats['max']:.4g} rms={stats['rms']:.4g}")
    print(f"Wrote quicklook {png_path}")


if __name__ == "__main__":
    main()
