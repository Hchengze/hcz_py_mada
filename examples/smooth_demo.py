"""Demonstrate triangle and box smoothing on a small RSF panel.

Run from the repository root:

    python examples/smooth_demo.py
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf
from pymadagascar.plot._common import pyplot
from pymadagascar.plot.grey import grey
from pymadagascar.signal.smooth import smooth_rsf


def main(argv: list[str] | None = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)
    outdir = Path(args[0]) if args else Path("examples") / "_output"
    outdir.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(2026)
    x = np.linspace(-1.0, 1.0, 96, dtype=np.float32)
    y = np.linspace(-1.0, 1.0, 64, dtype=np.float32)
    xx, yy = np.meshgrid(x, y)
    clean = np.exp(-12.0 * (xx * xx + yy * yy)).astype(np.float32)
    noisy = clean + rng.normal(0.0, 0.08, size=clean.shape).astype(np.float32)

    header = RSFHeader(
        {
            "o1": -1.0,
            "d1": float(x[1] - x[0]),
            "label1": "x",
            "o2": -1.0,
            "d2": float(y[1] - y[0]),
            "label2": "y",
        }
    )

    input_path = outdir / "smooth_input.rsf"
    triangle_path = outdir / "smooth_triangle.rsf"
    box_path = outdir / "smooth_box.rsf"
    png_path = outdir / "smooth_triangle.png"

    write_rsf(input_path, noisy, header)
    triangle = smooth_rsf(input_path, triangle_path, rect={1: 3, 2: 3}, repeat=1)
    smooth_rsf(input_path, box_path, rect={1: 3, 2: 3}, repeat=1, kind="box")

    loaded = read_rsf(triangle_path)
    print(f"Wrote {triangle_path} with shape={loaded.data.shape} dtype={loaded.data.dtype}")
    print(f"Wrote {box_path}")

    fig = grey(triangle.data, triangle.header, output_path=png_path, pclip=98.0, colorbar=False)
    pyplot().close(fig)
    print(f"Wrote quicklook {png_path}")


if __name__ == "__main__":
    main()
