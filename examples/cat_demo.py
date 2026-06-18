"""Concatenate two small RSF panels."""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

from pymadagascar.generic.cat import cat_rsf
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf


def main(argv: list[str] | None = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)
    folder = Path(args[0]) if args else Path("examples") / "cat_demo_output"
    folder.mkdir(parents=True, exist_ok=True)
    first = folder / "cat_first.rsf"
    second = folder / "cat_second.rsf"
    output = folder / "cat_output.rsf"

    header = RSFHeader(
        {
            "o1": 0.0,
            "d1": 0.004,
            "label1": "Time",
            "unit1": "s",
            "o2": 100.0,
            "d2": 25.0,
            "label2": "Trace",
            "unit2": "m",
        }
    )
    write_rsf(first, np.ones((2, 4), dtype=np.float32), header)
    write_rsf(second, 2.0 * np.ones((3, 4), dtype=np.float32), header)

    cat_rsf([first, second], output, axis=2)
    result = read_rsf(output)
    print(f"Wrote {output}")
    print(f"NumPy shape: {result.data.shape}")
    print(f"RSF dimensions n1..nN: {result.header.dimensions}")


if __name__ == "__main__":
    main()
