"""Small RSF read/write demo."""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf


def main(argv: list[str] | None = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)
    output_dir = Path(args[0]) if args else Path("examples") / "read_write_rsf_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "demo.rsf"
    data = np.arange(12, dtype=np.float32).reshape(3, 4)
    header = RSFHeader(
        {
            "o1": 0.0,
            "d1": 0.004,
            "label1": "Time",
            "unit1": "s",
            "o2": 100.0,
            "d2": 25.0,
            "label2": "Offset",
            "unit2": "m",
        }
    )

    write_rsf(output, data, header)
    rsf = read_rsf(output)

    print(f"Wrote {output}")
    print(f"Binary sidecar: {rsf.binary_path}")
    print(f"Shape: {rsf.data.shape}")
    print(f"RSF dimensions n1..nN: {rsf.header.dimensions}")
    print(f"Data format: {rsf.header['data_format']}")


if __name__ == "__main__":
    main()
