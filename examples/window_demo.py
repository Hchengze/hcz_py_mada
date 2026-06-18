"""Window a small RSF cube."""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

from pymadagascar.generic.window import window_rsf
from pymadagascar.io.rsf import RSFHeader, RSFArray, read_rsf, write_rsf


def main(argv: list[str] | None = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)
    folder = Path(args[0]) if args else Path("examples") / "window_demo_output"
    folder.mkdir(parents=True, exist_ok=True)
    input_path = folder / "window_input.rsf"
    output_path = folder / "window_output.rsf"

    data = np.arange(3 * 4 * 6, dtype=np.float32).reshape(3, 4, 6)
    header = RSFHeader(
        {
            "n1": 6,
            "n2": 4,
            "n3": 3,
            "o1": 0.0,
            "d1": 0.004,
            "label1": "Time",
            "unit1": "s",
            "o2": 100.0,
            "d2": 25.0,
            "label2": "Offset",
            "unit2": "m",
            "o3": 1.0,
            "d3": 1.0,
            "label3": "Shot",
        }
    )
    write_rsf(input_path, data, header)

    result = window_rsf(RSFArray(data, header), {"f1": 1, "n1": 3, "j1": 2, "f2": 1, "n2": 2})
    write_rsf(output_path, result.data, result.header)
    loaded = read_rsf(output_path)

    print(f"Wrote {output_path}")
    print(f"NumPy shape: {loaded.data.shape}")
    print(f"RSF dimensions n1..nN: {loaded.header.dimensions}")
    print(f"o1={loaded.header['o1']} d1={loaded.header['d1']}")


if __name__ == "__main__":
    main()
