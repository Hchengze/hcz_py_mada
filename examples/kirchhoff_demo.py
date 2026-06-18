"""Create and migrate a small synthetic diffraction with the Kirchhoff prototype."""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

from pymadagascar.imaging.kirchhoff import kirchhoff_time_migration
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf


def main(argv: list[str] | None = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)
    root = Path(args[0]) if args else Path("examples") / "kirchhoff_demo_output"
    root.mkdir(parents=True, exist_ok=True)
    input_path = root / "kirchhoff_diffraction.rsf"
    output_path = root / "kirchhoff_image.rsf"
    velocity = 2000.0
    nt, nx = 121, 41
    dt, dx = 0.004, 25.0
    time = dt * np.arange(nt, dtype=np.float64)
    x = dx * (np.arange(nx, dtype=np.float64) - nx // 2)
    tau0 = 0.24
    x0 = 0.0
    sigma = 0.006
    data = np.zeros((nx, nt), dtype=np.float32)
    for ix, xpos in enumerate(x):
        travel = np.sqrt(tau0 * tau0 + (2.0 * (xpos - x0) / velocity) ** 2)
        data[ix] = np.exp(-0.5 * ((time - travel) / sigma) ** 2).astype(np.float32)

    header = RSFHeader(
        {
            "n1": nt,
            "o1": 0.0,
            "d1": dt,
            "label1": "Time",
            "unit1": "s",
            "n2": nx,
            "o2": float(x[0]),
            "d2": dx,
            "label2": "Midpoint",
            "unit2": "m",
        }
    )
    write_rsf(input_path, data, header)
    kirchhoff_time_migration(input_path, output_path, velocity=velocity, normalize=True)
    image = read_rsf(output_path)
    peak = np.unravel_index(int(np.argmax(image.data)), image.data.shape)
    print(f"Peak image sample: x_index={peak[0]} time_index={peak[1]}")


if __name__ == "__main__":
    main()
