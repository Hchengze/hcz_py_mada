"""Create basic Matplotlib figures from small RSF-style arrays."""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

from pymadagascar.io.rsf import RSFHeader
from pymadagascar.plot.graph import graph
from pymadagascar.plot.grey import grey
from pymadagascar.plot.wiggle import wiggle


def main(argv: list[str] | None = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)
    folder = Path(args[0]) if args else Path("examples") / "plot_demo_output"
    folder.mkdir(parents=True, exist_ok=True)
    header = RSFHeader(
        {
            "o1": 0.0,
            "d1": 0.004,
            "label1": "Time",
            "unit1": "s",
            "o2": 0.0,
            "d2": 25.0,
            "label2": "Trace",
            "unit2": "m",
        }
    )

    x = np.linspace(0.0, 2.0 * np.pi, 200, dtype=np.float32)
    trace = np.sin(x).astype(np.float32)
    panel = np.stack(
        [np.sin(x + 0.35 * itrace) * np.exp(-0.004 * np.arange(x.size)) for itrace in range(24)],
        axis=0,
    ).astype(np.float32)

    graph(trace, header, output_path=folder / "plot_graph.png", title="Synthetic trace")
    grey(panel, header, output_path=folder / "plot_grey.png", title="Synthetic panel", cmap="gray")
    wiggle(panel, header, output_path=folder / "plot_wiggle.png", title="Synthetic wiggle", scale=0.7)

    print(f"Wrote plots under {folder}")


if __name__ == "__main__":
    main()
