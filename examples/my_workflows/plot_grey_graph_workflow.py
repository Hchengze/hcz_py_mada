"""Generate grey and graph quicklook PNGs from synthetic RSF-style data."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from pymadagascar.io.rsf import RSFHeader, write_rsf
from pymadagascar.plot._common import pyplot
from pymadagascar.plot.graph import graph
from pymadagascar.plot.grey import grey

from _common import parse_output_dir, print_outputs


def main(argv: Sequence[str] | None = None) -> int:
    output_dir = parse_output_dir("plot_grey_graph", argv)
    trace_path = output_dir / "plot_trace.rsf"
    panel_path = output_dir / "plot_panel.rsf"
    graph_path = output_dir / "plot_trace_graph.png"
    grey_path = output_dir / "plot_panel_grey.png"

    n1 = 160
    n2 = 18
    t = np.linspace(0.0, 1.0, n1, dtype=np.float32)
    trace = (np.sin(2.0 * np.pi * 6.0 * t) * np.exp(-1.5 * t)).astype(np.float32)
    panel = np.stack(
        [np.sin(2.0 * np.pi * (5.0 + 0.2 * ix) * t + 0.2 * ix) * np.exp(-1.2 * t) for ix in range(n2)],
        axis=0,
    ).astype(np.float32)

    header = RSFHeader(
        {
            "o1": 0.0,
            "d1": 0.004,
            "label1": "Time",
            "unit1": "s",
            "o2": 0.0,
            "d2": 1.0,
            "label2": "Trace",
        }
    )
    write_rsf(trace_path, trace, RSFHeader({"o1": 0.0, "d1": 0.004, "label1": "Time", "unit1": "s"}))
    write_rsf(panel_path, panel, header)

    graph(trace, header, output_path=graph_path, title="Synthetic trace")
    grey(panel, header, output_path=grey_path, title="Synthetic panel")
    pyplot().close("all")

    print_outputs([trace_path, panel_path, graph_path, grey_path])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
