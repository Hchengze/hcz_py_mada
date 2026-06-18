"""Demo for Stage C-4 seismic gather mute and QC tools.

Run from the project root:
    python examples/seismic_gather_qc_demo.py
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

from pymadagascar import RSFData
from pymadagascar.generic.difference import diff_rsf
from pymadagascar.io.rsf import RSFHeader, write_rsf
from pymadagascar.seismic.mute import mutter_rsf
from pymadagascar.seismic.stack import stacks_rsf


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    output_dir = Path(args[0]) if args else Path("seismic_gather_qc_output")
    output_dir.mkdir(parents=True, exist_ok=True)

    gather_path = output_dir / "synthetic_gather.rsf"
    muted_path = output_dir / "synthetic_muted.rsf"
    difference_path = output_dir / "mute_difference.rsf"
    stack_path = output_dir / "muted_stack.rsf"
    chain_path = output_dir / "conditioned_stack.rsf"

    n1 = 160
    n2 = 7
    dt = 0.004
    o2 = -450.0
    d2 = 150.0
    time = np.arange(n1, dtype=np.float32) * dt
    offsets = o2 + np.arange(n2, dtype=np.float32) * d2
    gather = np.zeros((n2, n1), dtype=np.float32)
    for itrace, offset in enumerate(offsets):
        event_time = 0.18 + abs(float(offset)) / 3000.0
        direct_time = 0.02 + abs(float(offset)) / 1400.0
        event = np.exp(-((time - event_time) / 0.018) ** 2)
        direct = 1.5 * np.exp(-((time - direct_time) / 0.012) ** 2)
        gather[itrace] = event + direct

    header = RSFHeader(
        {
            "n1": n1,
            "o1": 0.0,
            "d1": dt,
            "label1": "Time",
            "unit1": "s",
            "n2": n2,
            "o2": o2,
            "d2": d2,
            "label2": "Offset",
            "unit2": "m",
        }
    )
    write_rsf(gather_path, gather, header)

    mutter_rsf(
        gather_path,
        muted_path,
        v=1800.0,
        t0=0.015,
        side="above",
        taper=6,
    )
    diff_rsf(gather_path, muted_path, difference_path, metric="rms")
    stacks_rsf(muted_path, stack_path, axis=2, statistic="mean")

    conditioned = (
        RSFData(gather, header)
        .costaper(widths={1: 8})
        .clip2(pclip=99.0, symmetric=True)
        .mutter(v=1800.0, t0=0.015, side="above", taper=6)
        .stacks(axis=2, statistic="mean")
    )
    conditioned.write(chain_path)

    print(f"output_dir={output_dir}")
    for path in [gather_path, muted_path, difference_path, stack_path, chain_path]:
        print(f"wrote {path}")
    print(f"RSFData conditioned stack shape={conditioned.shape}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
