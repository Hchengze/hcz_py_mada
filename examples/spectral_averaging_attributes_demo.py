"""Stage C-9 Welch averaging and spectral-attribute demonstration."""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile

import numpy as np

from pymadagascar import read
from pymadagascar.io.rsf import RSFHeader, write_rsf
from pymadagascar.signal.spectral import (
    freqattr_rsf,
    specnorm_rsf,
    transfer_rsf,
    welch_rsf,
    welchcsd_rsf,
    whiten_rsf,
)


def _output_directory() -> Path:
    if len(sys.argv) > 1:
        output = Path(sys.argv[1])
        output.mkdir(parents=True, exist_ok=True)
        return output
    return Path(tempfile.mkdtemp(prefix="pymadagascar_c9_"))


def main() -> None:
    output = _output_directory()
    rng = np.random.default_rng(20260614)
    n = 1024
    dt = 0.002
    time = np.arange(n, dtype=np.float64) * dt

    source = (
        np.sin(2.0 * np.pi * 18.0 * time)
        + 0.35 * np.sin(2.0 * np.pi * 48.0 * time)
        + 0.12 * rng.standard_normal(n)
    ).astype(np.float32)
    response = np.convolve(
        source,
        np.array([0.2, 0.6, 0.2], dtype=np.float32),
        mode="same",
    ).astype(np.float32)
    response += (0.05 * rng.standard_normal(n)).astype(np.float32)

    header = RSFHeader(
        {
            "n1": n,
            "o1": 0.0,
            "d1": dt,
            "label1": "Time",
            "unit1": "s",
        }
    )
    source_path = output / "source.rsf"
    response_path = output / "response.rsf"
    write_rsf(source_path, source, header)
    write_rsf(response_path, response, header)

    welch_rsf(source_path, output / "welch_psd.rsf", nperseg=256, noverlap=128)
    welchcsd_rsf(
        source_path,
        response_path,
        output / "welch_csd.rsf",
        nperseg=256,
        noverlap=128,
    )
    transfer_rsf(
        source_path,
        response_path,
        output / "transfer_h1.rsf",
        nperseg=256,
        noverlap=128,
    )
    whiten_rsf(source_path, output / "whitened.rsf", smooth=7)
    specnorm_rsf(
        source_path,
        output / "normalized.rsf",
        fmin=5.0,
        fmax=80.0,
    )
    freqattr_rsf(
        source_path,
        output / "frequency_attributes.rsf",
        fmin=5.0,
        fmax=80.0,
    )

    chained = (
        read(source_path)
        .whiten(smooth=7)
        .specnorm(fmin=5.0, fmax=80.0)
        .welch(nperseg=256, noverlap=128)
    )
    chained.write(output / "chained_whitened_welch.rsf")

    print(f"Stage C-9 outputs: {output}")
    print("Expected dominant frequencies are near 18 Hz and 48 Hz.")


if __name__ == "__main__":
    main()
