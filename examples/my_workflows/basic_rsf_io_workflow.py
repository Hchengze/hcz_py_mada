"""Basic RSF read/write workflow for local experiments."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf

from _common import parse_output_dir, print_outputs


def main(argv: Sequence[str] | None = None) -> int:
    output_dir = parse_output_dir("basic_rsf_io", argv)
    input_path = output_dir / "basic_input.rsf"
    copy_path = output_dir / "basic_copy.rsf"

    # NumPy arrays use the pymadagascar convention: n1 is the last axis.
    data = np.arange(24, dtype=np.float32).reshape(3, 8)
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

    write_rsf(input_path, data, header)
    loaded = read_rsf(input_path)

    # Write a harmless copy so the workflow demonstrates roundtrip reuse.
    write_rsf(copy_path, loaded.data, loaded.header)

    print(f"shape: {loaded.data.shape}")
    print(f"RSF dimensions: {loaded.header.dimensions}")
    print_outputs([input_path, copy_path])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
