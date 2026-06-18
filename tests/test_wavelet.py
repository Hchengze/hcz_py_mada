from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys

import numpy as np
import pytest

from pymadagascar.io.rsf import read_rsf, write_rsf
from pymadagascar.modeling.acoustic2d import ricker_wavelet as acoustic_ricker_wavelet
from pymadagascar.signal import (
    WaveletError,
    ricker_rsf as package_ricker_rsf,
    ricker_wavelet as package_ricker_wavelet,
)
from pymadagascar.signal.wavelet import ricker_rsf, ricker_wavelet
from pymadagascar.testing.runner import original_madagascar_available, run_original_madagascar


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _run_ricker_cli(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = (
        str(PROJECT_ROOT)
        if not env.get("PYTHONPATH")
        else str(PROJECT_ROOT) + os.pathsep + env["PYTHONPATH"]
    )
    return subprocess.run(
        [sys.executable, "-m", "pymadagascar.cli.ricker", *args],
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_ricker_wavelet_peak_amplitude_and_shape() -> None:
    wavelet = ricker_wavelet(25.0, 0.001, 101, peak_time=0.04, amplitude=2.5)

    assert package_ricker_wavelet is ricker_wavelet
    assert wavelet.shape == (101,)
    assert wavelet.dtype == np.float32
    assert int(np.argmax(wavelet)) == 40
    assert wavelet[40] == pytest.approx(2.5)
    assert np.min(wavelet) < 0.0


def test_ricker_wavelet_frequency_controls_width() -> None:
    low = ricker_wavelet(10.0, 0.001, 201, peak_time=0.1)
    high = ricker_wavelet(40.0, 0.001, 201, peak_time=0.1)

    assert np.count_nonzero(low > 0.5) > np.count_nonzero(high > 0.5)


def test_ricker_rsf_writes_header(tmp_path: Path) -> None:
    path = tmp_path / "wavelet.rsf"

    result = ricker_rsf(path, frequency=30.0, dt=0.002, nt=64, t0=0.02, amplitude=1.25)
    loaded = read_rsf(path)

    assert package_ricker_rsf is ricker_rsf
    assert result.header_path == path.resolve()
    assert loaded.data.shape == (64,)
    assert loaded.data.dtype == np.float32
    assert loaded.header.dimensions == (64,)
    assert loaded.header["d1"] == "0.002"
    assert loaded.header["o1"] == "0"
    assert loaded.header["label1"] == "Time"
    assert loaded.header["unit1"] == "s"
    assert loaded.header["ricker_frequency"] == "30"
    assert loaded.header["ricker_peak_time"] == "0.02"
    assert loaded.header["ricker_amplitude"] == "1.25"


def test_ricker_wavelet_rejects_invalid_parameters() -> None:
    with pytest.raises(WaveletError, match="frequency= must be positive"):
        ricker_wavelet(0.0, 0.001, 64)
    with pytest.raises(WaveletError, match="dt= must be positive"):
        ricker_wavelet(25.0, 0.0, 64)
    with pytest.raises(WaveletError, match="nt= must be positive"):
        ricker_wavelet(25.0, 0.001, 0)
    with pytest.raises(WaveletError, match="must match"):
        ricker_wavelet(25.0, 0.001, 64, t0=0.02, peak_time=0.03)


@pytest.mark.cli
def test_ricker_cli_subprocess_smoke(tmp_path: Path) -> None:
    output_path = tmp_path / "wavelet.rsf"

    result = _run_ricker_cli(
        [
            "out=" + str(output_path),
            "f=25",
            "dt=0.001",
            "nt=80",
            "peak_time=0.03",
            "amplitude=3",
        ],
        tmp_path,
    )
    loaded = read_rsf(output_path)

    assert result.returncode == 0, result.stderr
    assert loaded.header.dimensions == (80,)
    assert loaded.header["ricker_frequency"] == "25"
    assert int(np.argmax(loaded.data)) == 30
    assert loaded.data[30] == pytest.approx(3.0)


def test_acoustic2d_ricker_wrapper_uses_signal_wavelet() -> None:
    old_api = acoustic_ricker_wavelet(101, 0.001, 25.0, t0=0.04)
    new_api = ricker_wavelet(25.0, 0.001, 101, peak_time=0.04)

    np.testing.assert_array_equal(old_api, new_api)


@pytest.mark.original_madagascar
def test_original_sfricker1_impulse_smoke_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfricker1"):
        pytest.skip("Original Madagascar sfricker1 is not installed")

    input_path = tmp_path / "impulse.rsf"
    original_path = tmp_path / "original.rsf"
    data = np.zeros(64, dtype=np.float32)
    data[32] = 1.0
    write_rsf(input_path, data, {"o1": 0.0, "d1": 0.001, "label1": "Time", "unit1": "s"})

    run_original_madagascar(
        ["sfricker1", "in=impulse.rsf", "out=original.rsf", "frequency=25"],
        cwd=tmp_path,
        require_program="sfricker1",
    )
    original = read_rsf(original_path)
    python_wavelet = ricker_wavelet(25.0, 0.001, 64, peak_time=0.032)

    assert original.data.shape == python_wavelet.shape
    assert np.all(np.isfinite(original.data))
    assert np.max(np.abs(original.data)) > 0.0
