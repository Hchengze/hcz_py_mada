"""Demonstrate RSF header queries with the sfget-style Python subset.

Run from the project root:

    python examples/get_demo.py

Optionally pass an output directory:

    python examples/get_demo.py get_demo_output
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

from pymadagascar.generic.info import (
    format_header_values,
    get_header_value,
    get_header_values,
)
from pymadagascar.io.rsf import RSFHeader, write_rsf


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    output_dir = Path(args[0]) if args else Path("examples") / "get_demo_output"
    output_dir.mkdir(parents=True, exist_ok=True)

    rsf_path = output_dir / "sample.rsf"
    data = np.arange(6, dtype=np.float32).reshape(2, 3)
    write_rsf(
        rsf_path,
        data,
        RSFHeader(
            {
                "o1": 0.0,
                "d1": 0.004,
                "label1": "Time",
                "unit1": "s",
                "o2": 0.0,
                "d2": 1.0,
                "label2": "Trace",
            }
        ),
    )

    n1 = get_header_value(rsf_path, "n1", cast="int")
    d1 = get_header_value(rsf_path, "d1", cast="float")
    values = get_header_values(rsf_path, ["n1", "n2", "d1", "label1"])
    missing_with_default = get_header_value(rsf_path, "survey", default="demo")

    print(f"wrote {rsf_path}")
    print(f"n1 as int: {n1}")
    print(f"d1 as float: {d1:g}")
    print("selected header values:")
    print(format_header_values(values))
    print(f"survey with default: {missing_with_default}")
    print("")
    print("CLI equivalent:")
    print(f"python -m pymadagascar.cli.get {rsf_path} key=n1,n2,d1,label1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
