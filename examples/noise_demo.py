"""Demonstrate synthetic RSF noise generation and additive noise.

Run from the project root:

    python examples/noise_demo.py

Optionally pass an output directory:

    python examples/noise_demo.py noise_demo_output
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

from pymadagascar.core.axis import Axis
from pymadagascar.generic.noise import noise_rsf
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    output_dir = Path(args[0]) if args else Path("examples") / "noise_demo_output"
    output_dir.mkdir(parents=True, exist_ok=True)

    noise_path = output_dir / "noise.rsf"
    clean_path = output_dir / "clean_sine.rsf"
    noisy_path = output_dir / "noisy_sine.rsf"

    noise_rsf(
        output_path=noise_path,
        shape=(128,),
        seed=2026,
        std=0.1,
        axes=[Axis(n=128, o=0.0, d=0.004, label="Time", unit="s")],
    )

    t = np.arange(128, dtype=np.float32) * 0.004
    clean = np.sin(2.0 * np.pi * 12.0 * t).astype(np.float32)
    header = RSFHeader({"o1": 0.0, "d1": 0.004, "label1": "Time", "unit1": "s"})
    write_rsf(clean_path, clean, header)
    noise_rsf(clean_path, noisy_path, seed=2026, std=0.1)

    noisy = read_rsf(noisy_path).data

    print(f"wrote {noise_path}")
    print(f"wrote {clean_path}")
    print(f"wrote {noisy_path}")
    print("")
    print(f"noise mean: {read_rsf(noise_path).data.mean():.6g}")
    print(f"noisy sine std: {noisy.std():.6g}")
    print("")
    print("CLI equivalents:")
    print(f"python -m pymadagascar.cli.noise n1=128 out={noise_path} seed=2026 std=0.1")
    print(f"python -m pymadagascar.cli.noise {clean_path} out={noisy_path} seed=2026 std=0.1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
