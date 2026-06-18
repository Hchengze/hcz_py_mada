"""Demo for Stage C-2 generic sampling and picking tools.

Run from the project root:
    python examples/generic_sampling_demo.py
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

from pymadagascar import RSFData
from pymadagascar.generic.sampling import bin_rsf, linear_rsf, max1_rsf, slice_rsf
from pymadagascar.io.rsf import RSFHeader, write_rsf


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    output_dir = Path(args[0]) if args else Path("generic_sampling_output")
    output_dir.mkdir(parents=True, exist_ok=True)

    panel_path = output_dir / "panel.rsf"
    linear_path = output_dir / "panel_linear.rsf"
    slice_path = output_dir / "cube_slice.rsf"
    max_value_path = output_dir / "panel_max_value.rsf"
    max_coord_path = output_dir / "panel_max_coord.rsf"
    points_path = output_dir / "points.rsf"
    grid_path = output_dir / "points_grid.rsf"
    chain_path = output_dir / "rsfdata_chain.rsf"

    n1 = 8
    n2 = 3
    x = np.arange(n1, dtype=np.float32)
    panel = np.vstack(
        [
            np.sin(0.5 * x),
            np.sin(0.5 * x) + 0.25,
            np.cos(0.5 * x),
        ]
    ).astype(np.float32)
    panel_header = RSFHeader(
        {
            "n1": n1,
            "o1": 0.0,
            "d1": 1.0,
            "label1": "Sample",
            "n2": n2,
            "o2": 0.0,
            "d2": 1.0,
            "label2": "Trace",
        }
    )
    write_rsf(panel_path, panel, panel_header)
    linear_rsf(panel_path, linear_path, axis=1, n=15, o=0.0, d=0.5)
    max1_rsf(panel_path, max_value_path, axis=1, mode="value")
    max1_rsf(panel_path, max_coord_path, axis=1, mode="coord")

    cube = np.stack([panel, panel + 1.0], axis=0).astype(np.float32)
    cube_path = output_dir / "cube.rsf"
    cube_header = panel_header.copy()
    cube_header["n3"] = 2
    cube_header["o3"] = 0.0
    cube_header["d3"] = 1.0
    cube_header["label3"] = "Shot"
    write_rsf(cube_path, cube, cube_header)
    slice_rsf(cube_path, slice_path, axis=3, index=1)

    points = np.array(
        [
            [0.1, 0.1, 1.0],
            [0.2, 0.2, 3.0],
            [1.2, 0.2, 5.0],
            [1.5, 1.2, 7.0],
        ],
        dtype=np.float32,
    )
    write_rsf(
        points_path,
        points,
        RSFHeader({"n1": 3, "n2": len(points), "label1": "Column", "label2": "Point"}),
    )
    bin_rsf(points_path, grid_path, n1=3, o1=0.0, d1=1.0, n2=3, o2=0.0, d2=1.0)

    chained = RSFData(panel, panel_header).linear(axis=1, n=15, d=0.5).max1(axis=1, mode="index")
    chained.write(chain_path)

    print(f"output_dir={output_dir}")
    for path in [
        panel_path,
        linear_path,
        cube_path,
        slice_path,
        max_value_path,
        max_coord_path,
        points_path,
        grid_path,
        chain_path,
    ]:
        print(f"wrote {path}")
    print(f"RSFData chain shape={chained.shape}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
