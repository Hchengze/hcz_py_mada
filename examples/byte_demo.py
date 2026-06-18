"""Demonstrate byte scaling for RSF quicklook workflows.

Run from the repository root:

    python examples/byte_demo.py
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

from pymadagascar.generic.byte import byte_rsf
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf
from pymadagascar.plot._common import pyplot
from pymadagascar.plot.grey import grey


def main(argv: list[str] | None = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)
    outdir = Path(args[0]) if args else Path("examples") / "_output"
    outdir.mkdir(parents=True, exist_ok=True)

    x = np.linspace(-1.0, 1.0, 96, dtype=np.float32)
    y = np.linspace(-1.0, 1.0, 64, dtype=np.float32)
    xx, yy = np.meshgrid(x, y)
    data = (np.sin(8.0 * xx) * np.exp(-3.0 * yy * yy)).astype(np.float32)
    data[8, 8] = np.nan

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

    input_path = outdir / "byte_input.rsf"
    byte_path = outdir / "byte_scaled.rsf"
    png_path = outdir / "byte_scaled.png"

    write_rsf(input_path, data, header)
    scaled = byte_rsf(input_path, byte_path, pclip=98.0)
    result = read_rsf(byte_path)
    print(f"Wrote {byte_path} as {result.header['data_format']} with dtype={result.data.dtype}")

    fig = grey(scaled.data, scaled.header, output_path=png_path, clip=255.0, pclip=None, colorbar=False)
    pyplot().close(fig)
    print(f"Wrote quicklook {png_path}")


if __name__ == "__main__":
    main()
