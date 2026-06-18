"""Demonstrate stable text dumps for small RSF arrays.

Run from the project root:

    python examples/disfil_demo.py

Optionally pass an output directory:

    python examples/disfil_demo.py disfil_demo_output
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

from pymadagascar.generic.info import disfil_array, disfil_rsf
from pymadagascar.io.rsf import RSFHeader, write_rsf


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    output_dir = Path(args[0]) if args else Path("examples") / "disfil_demo_output"
    output_dir.mkdir(parents=True, exist_ok=True)

    trace_path = output_dir / "trace.rsf"
    panel_path = output_dir / "panel.rsf"
    complex_path = output_dir / "complex.rsf"

    header = RSFHeader({"o1": 0.0, "d1": 0.004, "label1": "Time", "unit1": "s"})
    write_rsf(trace_path, np.array([0.0, 1.25, 2.5], dtype=np.float32), header)
    write_rsf(panel_path, np.arange(6, dtype=np.float32).reshape(2, 3), header)
    write_rsf(complex_path, np.array([1 + 2j, 3 - 4j], dtype=np.complex64), header)

    print(f"wrote {trace_path}")
    print(f"wrote {panel_path}")
    print(f"wrote {complex_path}")
    print("")
    print("1D flat dump:")
    print(disfil_rsf(trace_path, max_values=10))
    print("")
    print("2D RSF-index dump:")
    print(disfil_rsf(panel_path, max_values=6, axis_format="rsf"))
    print("")
    print("Complex dump:")
    print(disfil_array(np.array([1 + 2j, 3 - 4j], dtype=np.complex64)))
    print("")
    print("CLI equivalent:")
    print(f"python -m pymadagascar.cli.disfil {panel_path} max=6 axis_format=rsf")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
