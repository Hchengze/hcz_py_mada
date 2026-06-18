"""Demo for Stage C-3 signal correlation and conditioning tools.

Run from the project root:
    python examples/signal_correlation_conditioning_demo.py
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

from pymadagascar import RSFData
from pymadagascar.io.rsf import RSFHeader, write_rsf
from pymadagascar.seismic.stack import stacks_rsf
from pymadagascar.signal.conditioning import shifts_rsf
from pymadagascar.signal.convolution import autocorr_rsf, cconv_rsf, convolve_rsf, envcorr_rsf


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    output_dir = Path(args[0]) if args else Path("signal_correlation_conditioning_output")
    output_dir.mkdir(parents=True, exist_ok=True)

    signal_path = output_dir / "signal.rsf"
    panel_path = output_dir / "panel.rsf"
    wavelet_path = output_dir / "wavelet.rsf"
    autocorr_path = output_dir / "signal_autocorr.rsf"
    convolve_path = output_dir / "panel_convolved.rsf"
    cconv_path = output_dir / "panel_circular.rsf"
    envcorr_path = output_dir / "signal_envcorr.rsf"
    shifts_path = output_dir / "panel_shifted.rsf"
    stacks_path = output_dir / "panel_stacked.rsf"
    chain_path = output_dir / "rsfdata_chain.rsf"

    n1 = 64
    n2 = 3
    dt = 0.004
    time = np.arange(n1, dtype=np.float32) * dt
    signal = (
        np.sin(2.0 * np.pi * 16.0 * time)
        * np.exp(-((time - 0.12) ** 2) / (2.0 * 0.025**2))
    ).astype(np.float32)
    panel = np.vstack([np.roll(signal, shift) + 0.05 * itrace for itrace, shift in enumerate([0, 3, -2])]).astype(
        np.float32
    )
    wavelet = np.array([0.25, 0.5, 0.25], dtype=np.float32)
    shift_kernel = np.zeros(n1, dtype=np.float32)
    shift_kernel[2] = 1.0

    signal_header = RSFHeader({"n1": n1, "o1": 0.0, "d1": dt, "label1": "Time", "unit1": "s"})
    panel_header = signal_header.copy()
    panel_header["n2"] = n2
    panel_header["o2"] = 0.0
    panel_header["d2"] = 1.0
    panel_header["label2"] = "Trace"
    write_rsf(signal_path, signal, signal_header)
    write_rsf(panel_path, panel, panel_header)
    write_rsf(wavelet_path, wavelet, RSFHeader({"n1": wavelet.size, "o1": 0.0, "d1": dt, "label1": "Time"}))
    circular_kernel_path = output_dir / "circular_kernel.rsf"
    write_rsf(circular_kernel_path, shift_kernel, signal_header)

    autocorr_rsf(signal_path, autocorr_path, axis=1, max_lag=12, normalize=True)
    convolve_rsf(panel_path, wavelet_path, convolve_path, axis=1, mode="same")
    cconv_rsf(panel_path, circular_kernel_path, cconv_path, axis=1)
    envcorr_rsf(signal_path, signal_path, envcorr_path, axis=1, mode="same", normalize=True)
    shifts_rsf(panel_path, shifts_path, axis=1, shift=4, fill=0.0)
    stacks_rsf(panel_path, stacks_path, axis=2, statistic="mean")

    chained = (
        RSFData(panel, panel_header)
        .convolve(wavelet, axis=1, mode="same")
        .shifts(shift=2, axis=1)
        .stacks(axis=2, statistic="mean")
    )
    chained.write(chain_path)

    print(f"output_dir={output_dir}")
    for path in [
        signal_path,
        panel_path,
        wavelet_path,
        circular_kernel_path,
        autocorr_path,
        convolve_path,
        cconv_path,
        envcorr_path,
        shifts_path,
        stacks_path,
        chain_path,
    ]:
        print(f"wrote {path}")
    print(f"RSFData chain shape={chained.shape}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
