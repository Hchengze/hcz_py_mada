"""Demo for Stage C-4 axis calculus and amplitude conditioning.

Run from the project root:
    python examples/axis_calculus_conditioning_demo.py
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

from pymadagascar import RSFData
from pymadagascar.io.rsf import RSFHeader, write_rsf
from pymadagascar.signal.calculus import causint_rsf, deriv_rsf, integral_rsf
from pymadagascar.signal.conditioning import clip2_rsf


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    output_dir = Path(args[0]) if args else Path("axis_calculus_conditioning_output")
    output_dir.mkdir(parents=True, exist_ok=True)

    input_path = output_dir / "synthetic_signal.rsf"
    deriv_path = output_dir / "synthetic_deriv.rsf"
    causint_path = output_dir / "synthetic_causint.rsf"
    integral_path = output_dir / "synthetic_integral.rsf"
    clip_path = output_dir / "synthetic_clip2.rsf"
    chain_path = output_dir / "synthetic_chain.rsf"

    n1 = 128
    dt = 0.004
    time = np.arange(n1, dtype=np.float32) * dt
    signal = (
        0.7 * np.sin(2.0 * np.pi * 10.0 * time)
        + 0.25 * np.sin(2.0 * np.pi * 28.0 * time)
    ).astype(np.float32)
    signal[48] = 3.0
    signal[82] = -2.5
    header = RSFHeader(
        {
            "n1": n1,
            "o1": 0.0,
            "d1": dt,
            "label1": "Time",
            "unit1": "s",
        }
    )
    write_rsf(input_path, signal, header)

    deriv_rsf(input_path, deriv_path, axis=1, method="central", scale_by_d=True)
    causint_rsf(input_path, causint_path, axis=1, scale_by_d=True)
    integral_rsf(input_path, integral_path, axis=1, method="trapezoid")
    clip2_rsf(input_path, clip_path, pclip=98.0, symmetric=True)

    chained = (
        RSFData(signal, header)
        .clip2(pclip=98.0, symmetric=True)
        .deriv(axis=1)
        .causint(axis=1, scale_by_d=True)
    )
    chained.write(chain_path)

    print(f"output_dir={output_dir}")
    for path in [input_path, deriv_path, causint_path, integral_path, clip_path, chain_path]:
        print(f"wrote {path}")
    print(f"RSFData chain shape={chained.shape}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
