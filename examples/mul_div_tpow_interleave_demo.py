"""Small local demo for B-2 array operations.

Run from the project root:
    python examples/mul_div_tpow_interleave_demo.py
"""

from __future__ import annotations

from pathlib import Path
import tempfile

import numpy as np

from pymadagascar.generic.array_math import divide_rsf, multiply_rsf, tpow_rsf
from pymadagascar.generic.interleave import interleave_rsf
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf


def main() -> None:
    workdir = Path(tempfile.mkdtemp(prefix="pymada_b2_demo_"))
    header = RSFHeader({"o1": 0.0, "d1": 0.5, "label1": "Time", "unit1": "s"})

    a = workdir / "a.rsf"
    b = workdir / "b.rsf"
    mul_scalar = workdir / "mul_scalar.rsf"
    mul_file = workdir / "mul_file.rsf"
    div_scalar = workdir / "div_scalar.rsf"
    tpow_out = workdir / "tpow.rsf"
    interleaved = workdir / "interleave.rsf"

    write_rsf(a, np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float32), header)
    write_rsf(b, np.array([10.0, 20.0, 30.0, 40.0], dtype=np.float32), header)

    multiply_rsf(a, None, mul_scalar, scalar=2.0)
    multiply_rsf(a, b, mul_file)
    divide_rsf(b, None, div_scalar, scalar=10.0)
    tpow_rsf(a, tpow_out, power=1.0, axis=1)
    interleave_rsf([a, b], interleaved, axis=1)

    print(f"workdir={workdir}")
    for path in [a, b, mul_scalar, mul_file, div_scalar, tpow_out, interleaved]:
        print(f"{path.name}: {path} data={read_rsf(path).data.tolist()}")


if __name__ == "__main__":
    main()
