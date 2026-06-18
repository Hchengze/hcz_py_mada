"""Demonstrate mask, cut, and reverse RSF utilities.

Run from the repository root:

    python examples/mask_cut_reverse_demo.py
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

from pymadagascar.generic.cut import cut_rsf
from pymadagascar.generic.mask import mask_rsf
from pymadagascar.generic.reverse import reverse_rsf
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf


def main(argv: list[str] | None = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)
    outdir = Path(args[0]) if args else Path("examples") / "_output"
    outdir.mkdir(parents=True, exist_ok=True)

    data = np.linspace(-2.0, 2.0, 24, dtype=np.float32).reshape(4, 6)
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

    input_path = outdir / "mcr_input.rsf"
    mask_path = outdir / "mcr_mask.rsf"
    cut_path = outdir / "mcr_cut.rsf"
    reverse_path = outdir / "mcr_reverse.rsf"

    write_rsf(input_path, data, header)
    mask_rsf(input_path, mask_path, min_value=-0.75, max_value=0.75)
    cut_rsf(input_path, cut_path, axis=1, f=2, n=2)
    reverse_rsf(input_path, reverse_path, axis=2)

    mask = read_rsf(mask_path)
    cut = read_rsf(cut_path)
    reversed_panel = read_rsf(reverse_path)
    print(f"Mask ones: {int(mask.data.sum())}")
    print(f"Cut nonzero samples: {int(np.count_nonzero(cut.data))}")
    print(f"Reverse o2={reversed_panel.header['o2']} d2={reversed_panel.header['d2']}")


if __name__ == "__main__":
    main()
