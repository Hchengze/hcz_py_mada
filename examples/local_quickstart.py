"""Local pymadagascar quickstart.

Run from the project root after editable install:

    python examples/local_quickstart.py

The script writes a small set of RSF files and, when Matplotlib is available,
a PNG quicklook figure.
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

from pymadagascar.core.axis import Axis
from pymadagascar.generic.attr import attr_rsf, format_attr
from pymadagascar.generic.math import math_rsf
from pymadagascar.generic.spike import spike
from pymadagascar.generic.window import window_rsf
from pymadagascar.io.rsf import RSFArray, RSFHeader, read_rsf, write_rsf
from pymadagascar.signal.filter import bandpass_rsf


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    output_dir = Path(args[0]) if args else Path("local_quickstart_output")
    output_dir.mkdir(parents=True, exist_ok=True)

    input_path = output_dir / "input.rsf"
    spike_path = output_dir / "spike.rsf"
    wave_path = output_dir / "sine.rsf"
    window_path = output_dir / "sine_window.rsf"
    bandpass_path = output_dir / "sine_bandpass.rsf"
    plot_path = output_dir / "spike_grey.png"

    # 1. Write and read a small RSF array with explicit axis metadata.
    data = np.arange(32, dtype=np.float32).reshape(4, 8)
    header = RSFHeader(
        {
            "o1": 0.0,
            "d1": 0.004,
            "label1": "Time",
            "unit1": "s",
            "o2": 0.0,
            "d2": 0.1,
            "label2": "Trace",
            "unit2": "km",
        }
    )
    write_rsf(input_path, data, header)
    loaded = read_rsf(input_path)

    # 2. Generate a 2D spike panel.
    spike_rsf = spike(
        (8, 4),
        locations=(4, 2),
        axes=[
            Axis(n=8, o=0.0, d=0.004, label="Time", unit="s", index=1),
            Axis(n=4, o=0.0, d=0.1, label="Trace", unit="km", index=2),
        ],
    )
    write_rsf(spike_path, spike_rsf.data, spike_rsf.header)

    # 3. Build a deterministic sine trace with a Madagascar-style expression.
    wave = math_rsf(
        "sin(2*pi*10*x1)",
        axes=[Axis(n=128, o=0.0, d=0.004, label="Time", unit="s", index=1)],
    )
    write_rsf(wave_path, wave.data, wave.header)

    # 4. Window the sine trace in memory and write the result.
    windowed = window_rsf(RSFArray(wave.data, wave.header), {"f1": 16, "n1": 64})
    write_rsf(window_path, windowed.data, windowed.header)

    # 5. Apply a small zero-phase bandpass filter.
    bandpass_rsf(wave_path, bandpass_path, flo=5.0, fhi=20.0, axis=1, taper=2.0)

    # 6. Inspect attributes as text.
    stats_text = format_attr(attr_rsf(bandpass_path))

    # 7. Save a Matplotlib grey quicklook when plotting dependencies exist.
    try:
        from pymadagascar.plot.grey import grey
        from pymadagascar.plot._common import pyplot

        fig = grey(spike_rsf.data, spike_rsf.header, output_path=plot_path, title="Spike quicklook")
        pyplot().close(fig)
        plot_status = f"wrote {plot_path}"
    except ImportError:
        plot_status = "skipped grey plot because Matplotlib is not installed"

    print(f"input shape: {loaded.data.shape}, RSF dimensions: {loaded.header.dimensions}")
    print(f"wrote {input_path}")
    print(f"wrote {spike_path}")
    print(f"wrote {wave_path}")
    print(f"wrote {window_path}")
    print(f"wrote {bandpass_path}")
    print(plot_status)
    print("")
    print(stats_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
