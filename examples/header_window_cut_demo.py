"""Demo for headerwindow/headercut Python mask subsets.

Run from the project root:
    python examples/header_window_cut_demo.py
"""

from __future__ import annotations

from pathlib import Path
import tempfile

import numpy as np

from pymadagascar.generic.header_mask import header_cut_rsf, header_window_rsf
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf


def main() -> None:
    workdir = Path(tempfile.mkdtemp(prefix="pymada_header_mask_demo_"))
    data_path = workdir / "gather.rsf"
    mask_path = workdir / "trace_mask.rsf"
    window_path = workdir / "headerwindow.rsf"
    cut_path = workdir / "headercut.rsf"

    header = RSFHeader(
        {
            "o1": 0.0,
            "d1": 0.004,
            "label1": "Time",
            "unit1": "s",
            "o2": 100.0,
            "d2": 25.0,
            "label2": "Trace",
        }
    )
    data = np.arange(20, dtype=np.float32).reshape(5, 4)
    mask = np.array([0, 1, 1, 1, 0], dtype=np.int32)

    write_rsf(data_path, data, header)
    write_rsf(mask_path, mask, RSFHeader({"label1": "Trace mask"}))

    header_window_rsf(data_path, mask_path, window_path, axis=2)
    header_cut_rsf(data_path, mask_path, cut_path, axis=2)

    print(f"workdir={workdir}")
    for path in [data_path, mask_path, window_path, cut_path]:
        print(f"{path.name}: {path} data={read_rsf(path).data.tolist()}")


if __name__ == "__main__":
    main()
