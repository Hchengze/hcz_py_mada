"""Transpose and reshape small RSF datasets."""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

from pymadagascar.generic.transp import reshape_rsf, transpose_rsf
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf


def main(argv: list[str] | None = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)
    folder = Path(args[0]) if args else Path("examples") / "transp_demo_output"
    folder.mkdir(parents=True, exist_ok=True)
    input_path = folder / "transp_input.rsf"
    transposed_path = folder / "transp_output.rsf"
    reshaped_path = folder / "reshape_output.rsf"

    data = np.arange(12, dtype=np.float32).reshape(3, 4)
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
    write_rsf(input_path, data, header)

    transpose_rsf(input_path, transposed_path, order=(2, 1))
    reshape_rsf(input_path, reshaped_path, shape=(6, 2))

    transposed = read_rsf(transposed_path)
    reshaped = read_rsf(reshaped_path)
    print(f"Transposed shape: {transposed.data.shape}, RSF dims: {transposed.header.dimensions}")
    print(f"Reshaped shape: {reshaped.data.shape}, RSF dims: {reshaped.header.dimensions}")


if __name__ == "__main__":
    main()
