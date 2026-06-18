"""Generate a coordinate-based RSF math dataset."""

from __future__ import annotations

from pathlib import Path
import sys

from pymadagascar.generic.math import math_rsf
from pymadagascar.io.rsf import read_rsf, write_rsf


def main(argv: list[str] | None = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)
    output_dir = Path(args[0]) if args else Path("examples") / "math_demo_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "math_demo.rsf"
    rsf = math_rsf(
        'sin(2*pi*x1) + 0.25*cos(2*pi*x2)',
        axes=[
            {"n": 64, "o": 0.0, "d": 1.0 / 64.0, "label": "Time", "unit": "s"},
            {"n": 8, "o": 0.0, "d": 0.5, "label": "Trace", "unit": "km"},
        ],
    )
    write_rsf(output, rsf.data, rsf.header)

    loaded = read_rsf(output)
    print(f"Wrote {output}")
    print(f"NumPy shape: {loaded.data.shape}")
    print(f"RSF dimensions n1..nN: {loaded.header.dimensions}")
    print(f"Data range: {loaded.data.min():.6g} to {loaded.data.max():.6g}")


if __name__ == "__main__":
    main()
