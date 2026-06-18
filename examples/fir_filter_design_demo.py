"""Stage C-10 FIR design, response, filtering, and band-QC demonstration."""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile

import numpy as np

from pymadagascar import read
from pymadagascar.io.rsf import RSFHeader, write_rsf
from pymadagascar.signal.fir import (
    bandenergy_rsf,
    filterbank_rsf,
    filtfilt_rsf,
    firfilter_rsf,
    firwin_rsf,
    freqz_rsf,
)


def _output_directory(argv: list[str]) -> Path:
    if argv:
        output = Path(argv[0])
        output.mkdir(parents=True, exist_ok=True)
        return output
    return Path(tempfile.mkdtemp(prefix="pymadagascar_c10_"))


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    output = _output_directory(args)
    rng = np.random.default_rng(20260614)
    ntime = 1024
    ntrace = 3
    dt = 0.002
    fs = 1.0 / dt
    time = np.arange(ntime, dtype=np.float64) * dt
    low = np.sin(2.0 * np.pi * 18.0 * time)
    high = 0.65 * np.sin(2.0 * np.pi * 75.0 * time)
    panel = np.vstack(
        [
            low + high + 0.08 * rng.standard_normal(ntime)
            for _ in range(ntrace)
        ]
    ).astype(np.float32)
    header = RSFHeader(
        {
            "n1": ntime,
            "o1": 0.0,
            "d1": dt,
            "label1": "Time",
            "unit1": "s",
            "n2": ntrace,
            "o2": 0.0,
            "d2": 5.0,
            "label2": "Channel",
            "unit2": "m",
        }
    )

    input_path = output / "fir_input.rsf"
    taps_path = output / "fir_lowpass_taps.rsf"
    write_rsf(input_path, panel, header)
    firwin_rsf(
        taps_path,
        numtaps=101,
        cutoff=35.0,
        fs=fs,
        window="hamming",
    )
    freqz_rsf(
        taps_path,
        output / "fir_response.rsf",
        fs=fs,
        nfft=1024,
        mode="amplitude",
    )
    firfilter_rsf(input_path, taps_path, output / "fir_filtered.rsf")
    filtfilt_rsf(input_path, taps_path, output / "fir_zero_phase.rsf")
    bandenergy_rsf(
        input_path,
        output / "fir_band_energy.rsf",
        bands="10:30,60:90",
        mode="rms",
        average=False,
    )
    filterbank_rsf(
        input_path,
        output / "fir_filter_bank.rsf",
        bands="10:30,60:90",
        numtaps=101,
        window="hann",
    )

    chained = (
        read(input_path)
        .filtfilt(taps_path)
        .bandenergy(bands="10:30,60:90", mode="rms", average=False)
    )
    chained.write(output / "fir_chain_band_energy.rsf")

    print(f"Stage C-10 outputs: {output}")
    print("Signal bands: 18 Hz primary and 75 Hz interference.")
    print(f"Filter taps: {taps_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
