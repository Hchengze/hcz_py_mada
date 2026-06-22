from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys

import numpy as np
import pytest

from pymadagascar.api import RSFData
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf
from pymadagascar.signal import cosft as package_cosft
from pymadagascar.signal import cosft_rsf as package_cosft_rsf
from pymadagascar.signal import fft1_rsf as package_fft1_rsf
from pymadagascar.signal import spectra2 as package_spectra2
from pymadagascar.signal.transforms import (
    TransformError,
    cosft,
    cosft_rsf,
    fft1_rsf,
    spectra2,
    spectra2_rsf,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _run_cli(module: str, args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = (
        str(PROJECT_ROOT)
        if not env.get("PYTHONPATH")
        else str(PROJECT_ROOT) + os.pathsep + env["PYTHONPATH"]
    )
    return subprocess.run(
        [sys.executable, "-m", f"pymadagascar.cli.{module}", *args],
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def _header_1d(n1: int, *, d1: float = 0.01) -> RSFHeader:
    return RSFHeader({"n1": n1, "o1": 0.0, "d1": d1, "label1": "Time", "unit1": "s"})


def _header_2d(n1: int, n2: int, *, d1: float = 0.01, d2: float = 10.0) -> RSFHeader:
    header = _header_1d(n1, d1=d1)
    header["n2"] = n2
    header["o2"] = 0.0
    header["d2"] = d2
    header["label2"] = "Distance"
    header["unit2"] = "m"
    return header


def test_fft1_forward_inverse_round_trip_and_header(tmp_path: Path) -> None:
    n = 64
    d = 0.004
    time = np.arange(n, dtype=np.float64) * d
    data = np.sin(2.0 * np.pi * 15.625 * time).astype(np.float32)
    input_path = tmp_path / "input.rsf"
    spectrum_path = tmp_path / "fft1.rsf"
    round_trip_path = tmp_path / "ifft1.rsf"
    write_rsf(input_path, data, _header_1d(n, d1=d))

    fft1_rsf(input_path, spectrum_path)
    fft1_rsf(spectrum_path, round_trip_path, inverse=True)
    spectrum = read_rsf(spectrum_path)
    round_trip = read_rsf(round_trip_path)

    assert package_fft1_rsf is fft1_rsf
    assert spectrum.data.dtype == np.dtype("complex64")
    assert spectrum.data.shape == (n // 2 + 1,)
    assert spectrum.header["n1"] == str(n // 2 + 1)
    assert spectrum.header["fft_n1"] == str(n)
    assert spectrum.header["label1"] == "Frequency"
    assert spectrum.header["unit1"] == "Hz"
    np.testing.assert_allclose(round_trip.data, data, atol=1e-6)
    assert round_trip.header["n1"] == str(n)
    assert "fft_n1" not in round_trip.header


def test_fft1_rsfdata_chain_and_cli(tmp_path: Path) -> None:
    data = np.zeros(8, dtype=np.float32)
    data[1] = 1.0
    rsf = RSFData(data, _header_1d(8))
    result = rsf.fft1()

    np.testing.assert_array_equal(rsf.numpy(), data)
    assert result.shape == (5,)
    assert result.dtype == np.dtype("complex64")

    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "fft1_cli.rsf"
    write_rsf(input_path, data, _header_1d(8))
    completed = _run_cli("fft1", [str(input_path), "out=" + str(output_path), "axis=1"], tmp_path)

    assert completed.returncode == 0, completed.stderr
    assert read_rsf(output_path).data.shape == (5,)


def test_cosft_round_trip_header_and_cli(tmp_path: Path) -> None:
    data = np.array([0.0, 1.0, 0.5, -0.25, 0.0], dtype=np.float32)
    coeff = cosft(data, axis=1)
    restored = cosft(coeff, axis=1, inverse=True)

    assert package_cosft is cosft
    np.testing.assert_allclose(restored, data, atol=1e-6)
    assert coeff.dtype == np.dtype("float32")

    input_path = tmp_path / "input.rsf"
    coeff_path = tmp_path / "cosft.rsf"
    restored_path = tmp_path / "icosft.rsf"
    write_rsf(input_path, data, _header_1d(data.size, d1=0.5))
    cosft_rsf(input_path, coeff_path)
    completed = _run_cli("cosft", [str(coeff_path), "out=" + str(restored_path), "inv=y"], tmp_path)
    loaded = read_rsf(coeff_path)

    assert package_cosft_rsf is cosft_rsf
    assert completed.returncode == 0, completed.stderr
    assert loaded.header["cosft_label1"] == "Time"
    assert loaded.header["label1"] == "Frequency"
    np.testing.assert_allclose(read_rsf(restored_path).data, data, atol=1e-6)


def test_spectra2_frequency_wavenumber_peak_and_header(tmp_path: Path) -> None:
    n1, n2 = 64, 8
    d1, d2 = 0.004, 10.0
    time = np.arange(n1, dtype=np.float64) * d1
    space = np.arange(n2, dtype=np.float64) * d2
    data = np.sin(2.0 * np.pi * 31.25 * time[None, :] + 2.0 * np.pi * 0.025 * space[:, None])
    data = data.astype(np.float32)
    input_path = tmp_path / "panel.rsf"
    output_path = tmp_path / "spectra2.rsf"
    write_rsf(input_path, data, _header_2d(n1, n2, d1=d1, d2=d2))

    direct = spectra2(data, axes=(1, 2), d1=d1, d2=d2)
    spectra2_rsf(input_path, output_path, axes=(1, 2))
    loaded = read_rsf(output_path)

    assert package_spectra2 is spectra2
    assert direct.shape == (n2, n1 // 2 + 1)
    assert loaded.data.shape == direct.shape
    assert loaded.header["n1"] == str(n1 // 2 + 1)
    assert loaded.header["label1"] == "Frequency"
    assert loaded.header["unit1"] == "Hz"
    assert loaded.header["label2"] == "Wavenumber"
    assert loaded.header["unit2"] == "1/m"
    peak = np.unravel_index(int(np.argmax(loaded.data)), loaded.data.shape)
    assert peak[1] == 8


def test_spectra2_rsfdata_chain_average_cli_and_invalid_params(tmp_path: Path) -> None:
    data = np.ones((2, 4, 16), dtype=np.float32)
    rsf = RSFData(data, RSFHeader({"n1": 16, "n2": 4, "n3": 2, "d1": 0.01, "d2": 2.0}))

    result = rsf.spectra2(axes=(1, 2), average=True)

    np.testing.assert_array_equal(rsf.numpy(), data)
    assert result.shape == (4, 9)
    assert result.header.dimensions == (9, 4)

    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "spectra2_cli.rsf"
    write_rsf(input_path, data[0], _header_2d(16, 4, d1=0.01, d2=2.0))
    completed = _run_cli("spectra2", [str(input_path), "out=" + str(output_path), "axes=1,2"], tmp_path)
    assert completed.returncode == 0, completed.stderr
    assert read_rsf(output_path).data.shape == (4, 9)

    with pytest.raises(TransformError, match="distinct"):
        spectra2(np.ones((4, 4), dtype=np.float32), axes=(1, 1))
    with pytest.raises(TransformError, match="real-valued"):
        cosft(np.ones(4, dtype=np.complex64))
