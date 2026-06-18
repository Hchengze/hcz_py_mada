"""Combine spike generation, math expressions, and windowing."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from pymadagascar.core.axis import Axis
from pymadagascar.generic.math import math_rsf
from pymadagascar.generic.spike import spike
from pymadagascar.generic.window import window_rsf
from pymadagascar.io.rsf import RSFArray, write_rsf

from _common import parse_output_dir, print_outputs


def main(argv: Sequence[str] | None = None) -> int:
    output_dir = parse_output_dir("spike_math_window", argv)
    spike_path = output_dir / "spike_panel.rsf"
    math_path = output_dir / "math_panel.rsf"
    window_path = output_dir / "math_window.rsf"

    axes = [
        Axis(n=64, o=0.0, d=0.004, label="Time", unit="s", index=1),
        Axis(n=8, o=0.0, d=0.1, label="Trace", unit="km", index=2),
    ]

    # A small 2D spike panel is useful as a fixture and visual sanity check.
    spike_panel = spike((64, 8), locations=[(16, 3), (40, 6)], magnitudes=[1.0, -0.75], axes=axes)
    write_rsf(spike_path, spike_panel.data, spike_panel.header)

    # The expression uses x1/x2 coordinates in Madagascar style.
    math_panel = math_rsf("sin(2*pi*12*x1) * exp(-x2)", axes=axes)
    write_rsf(math_path, math_panel.data.astype(np.float32), math_panel.header)

    # Keep a time window from sample 9 through 40 on axis 1.
    windowed = window_rsf(RSFArray(math_panel.data, math_panel.header), {"f1": 8, "n1": 32})
    write_rsf(window_path, windowed.data, windowed.header)

    print(f"spike dimensions: {spike_panel.header.dimensions}")
    print(f"window dimensions: {windowed.header.dimensions}")
    print_outputs([spike_path, math_path, window_path])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
