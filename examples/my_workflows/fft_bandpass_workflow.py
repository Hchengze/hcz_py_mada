"""Create a synthetic trace, inspect its FFT, and apply a bandpass filter."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from pymadagascar.io.rsf import RSFHeader, write_rsf
from pymadagascar.signal.fft import rfft_rsf
from pymadagascar.signal.filter import bandpass_rsf

from _common import parse_output_dir, print_outputs


def main(argv: Sequence[str] | None = None) -> int:
    output_dir = parse_output_dir("fft_bandpass", argv)
    trace_path = output_dir / "mixed_trace.rsf"
    spectrum_path = output_dir / "mixed_trace_rfft.rsf"
    bandpass_path = output_dir / "mixed_trace_bandpass.rsf"

    n1 = 256
    d1 = 0.004
    time = d1 * np.arange(n1, dtype=np.float32)
    trace = (
        np.sin(2.0 * np.pi * 8.0 * time)
        + 0.4 * np.sin(2.0 * np.pi * 35.0 * time)
        + 0.2 * np.sin(2.0 * np.pi * 70.0 * time)
    ).astype(np.float32)

    header = RSFHeader({"o1": 0.0, "d1": d1, "label1": "Time", "unit1": "s"})
    write_rsf(trace_path, trace, header)

    # Use existing file-backed APIs so the workflow mirrors CLI-style use.
    rfft_rsf(trace_path, spectrum_path, axis=1)
    bandpass_rsf(trace_path, bandpass_path, flo=5.0, fhi=45.0, axis=1, taper=5.0)

    print(f"samples: {n1}")
    print_outputs([trace_path, spectrum_path, bandpass_path])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
