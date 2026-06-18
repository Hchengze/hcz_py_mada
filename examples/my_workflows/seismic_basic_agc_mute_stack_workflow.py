"""Small gather workflow: AGC, linear mute, and stack."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf
from pymadagascar.plot._common import pyplot
from pymadagascar.plot.graph import graph
from pymadagascar.seismic.agc import agc_rsf
from pymadagascar.seismic.mute import mute_rsf
from pymadagascar.seismic.stack import stack_rsf

from _common import parse_output_dir, print_outputs


def main(argv: Sequence[str] | None = None) -> int:
    output_dir = parse_output_dir("seismic_basic_agc_mute_stack", argv)
    gather_path = output_dir / "synthetic_gather.rsf"
    agc_path = output_dir / "synthetic_gather_agc.rsf"
    mute_path = output_dir / "synthetic_gather_mute.rsf"
    stack_path = output_dir / "synthetic_stack.rsf"
    stack_png = output_dir / "synthetic_stack_graph.png"

    n1 = 160
    n2 = 12
    d1 = 0.004
    offsets = -550.0 + 100.0 * np.arange(n2, dtype=np.float32)
    time = d1 * np.arange(n1, dtype=np.float32)

    gather = np.empty((n2, n1), dtype=np.float32)
    for itrace, offset in enumerate(offsets):
        center = 0.22 + abs(float(offset)) / 5000.0
        event = np.exp(-((time - center) ** 2) / (2.0 * 0.012**2))
        wave = np.sin(2.0 * np.pi * 18.0 * time)
        gather[itrace] = (event * wave + 0.05 * np.sin(2.0 * np.pi * 4.0 * time + itrace)).astype(np.float32)

    header = RSFHeader(
        {
            "o1": 0.0,
            "d1": d1,
            "label1": "Time",
            "unit1": "s",
            "o2": float(offsets[0]),
            "d2": 100.0,
            "label2": "Offset",
            "unit2": "m",
        }
    )
    write_rsf(gather_path, gather, header)

    agc_rsf(gather_path, agc_path, rect=0.048, axis=1)
    mute_rsf(agc_path, mute_path, t0=0.04, v=2500.0, axis=1, offset_axis=2, taper=0.04)
    stack_rsf(mute_path, stack_path, axis=2, mode="mean", nonzero=False)

    stacked = read_rsf(stack_path)
    graph(stacked.data, stacked.header, output_path=stack_png, title="AGC + mute + stack")
    pyplot().close("all")

    print(f"gather shape: {gather.shape}")
    print(f"stack dimensions: {stacked.header.dimensions}")
    print_outputs([gather_path, agc_path, mute_path, stack_path, stack_png])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
