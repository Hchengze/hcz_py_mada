from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys

import numpy as np
import pytest

from pymadagascar.api import RSFData
from pymadagascar.generic import laplac as package_laplac
from pymadagascar.generic import laplac_rsf as package_laplac_rsf
from pymadagascar.generic.laplac import LaplacError, laplac, laplac_rsf
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf
from pymadagascar.signal import trapez_filter as package_trapez_filter
from pymadagascar.signal import trapez_rsf as package_trapez_rsf
from pymadagascar.signal.smooth import box_smooth, triangle_smooth
from pymadagascar.signal.trapez import TrapezError, trapez_filter, trapez_rsf


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _header_1d(n1: int, *, d1: float = 1.0) -> RSFHeader:
    return RSFHeader({"n1": n1, "o1": 0.0, "d1": d1, "label1": "Sample", "unit1": "s"})


def _header_2d(n1: int, n2: int) -> RSFHeader:
    header = _header_1d(n1)
    header["n2"] = n2
    header["o2"] = 0.0
    header["d2"] = 1.0
    header["label2"] = "Trace"
    header["unit2"] = "m"
    return header


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


def test_laplac_1d_source_aligned_second_difference() -> None:
    data = np.array([0.0, 1.0, 4.0, 9.0], dtype=np.float32)

    result = laplac(data, axes=1)

    assert package_laplac is laplac
    np.testing.assert_array_equal(result, np.array([-1.0, -2.0, -2.0, 5.0], dtype=np.float32))


def test_laplac_2d_impulse_graph_laplacian() -> None:
    data = np.zeros((3, 3), dtype=np.float32)
    data[1, 1] = 1.0

    result = laplac(data, axes=(1, 2))

    expected = np.array(
        [[0.0, -1.0, 0.0], [-1.0, 4.0, -1.0], [0.0, -1.0, 0.0]],
        dtype=np.float32,
    )
    np.testing.assert_array_equal(result, expected)


def test_laplac_rsf_uses_header_spacing_and_preserves_header(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "laplac.rsf"
    data = np.array([0.0, 1.0, 4.0, 9.0], dtype=np.float32)
    write_rsf(input_path, data, _header_1d(4, d1=2.0))

    result = laplac_rsf(input_path, output_path, axes=1)
    loaded = read_rsf(output_path)

    assert package_laplac_rsf is laplac_rsf
    assert result.header_path == output_path.resolve()
    np.testing.assert_array_equal(
        loaded.data,
        np.array([-0.25, -0.5, -0.5, 1.25], dtype=np.float32),
    )
    assert loaded.header["d1"] == "2"
    assert loaded.header["label1"] == "Sample"


def test_laplac_rsfdata_chain_and_invalid_params() -> None:
    data = np.array([0.0, 1.0, 4.0, 9.0], dtype=np.float32)
    rsf = RSFData(data, _header_1d(4))

    result = rsf.laplac(axes=1, spacing_from_header=False)

    np.testing.assert_array_equal(rsf.numpy(), data)
    np.testing.assert_array_equal(result.numpy(), np.array([-1.0, -2.0, -2.0, 5.0], dtype=np.float32))
    with pytest.raises(LaplacError, match="boundary"):
        laplac(data, axes=1, boundary="constant")


def test_laplac_cli_subprocess(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "laplac.rsf"
    write_rsf(input_path, np.array([0.0, 1.0, 4.0, 9.0], dtype=np.float32), _header_1d(4))

    result = _run_cli(
        "laplac",
        [str(input_path), "out=" + str(output_path), "axis=1", "spacing_from_header=n"],
        tmp_path,
    )

    assert result.returncode == 0, result.stderr
    np.testing.assert_array_equal(
        read_rsf(output_path).data,
        np.array([-1.0, -2.0, -2.0, 5.0], dtype=np.float32),
    )


def test_rsfdata_smooth_is_triangle_not_boxsmooth() -> None:
    data = np.zeros(7, dtype=np.float32)
    data[3] = 1.0
    rsf = RSFData(data, _header_1d(7))

    triangle = rsf.smooth(rect=3, axes=1)
    box = rsf.boxsmooth(rect=3, axes=1)

    np.testing.assert_array_equal(rsf.numpy(), data)
    np.testing.assert_allclose(triangle.numpy(), triangle_smooth(data, rect=3, axes=1))
    np.testing.assert_allclose(box.numpy(), box_smooth(data, rect=3, axes=1))
    assert not np.allclose(triangle.numpy(), box.numpy())


def test_trapez_filter_suppresses_out_of_band_sine_and_preserves_header(tmp_path: Path) -> None:
    n = 256
    d = 0.004
    time = np.arange(n, dtype=np.float64) * d
    low = np.sin(2.0 * np.pi * 10.0 * time)
    high = 0.8 * np.sin(2.0 * np.pi * 80.0 * time)
    data = (low + high).astype(np.float32)
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "trapez.rsf"
    write_rsf(input_path, data, _header_1d(n, d1=d))

    trapez_rsf(input_path, output_path, frequency=(5.0, 8.0, 20.0, 25.0))
    loaded = read_rsf(output_path)

    assert package_trapez_filter is trapez_filter
    assert package_trapez_rsf is trapez_rsf
    assert loaded.data.shape == data.shape
    assert loaded.header["d1"] == "0.004"
    freq = np.fft.rfftfreq(n, d=d)
    spectrum = np.abs(np.fft.rfft(loaded.data.astype(np.float64)))
    low_bin = int(np.argmin(np.abs(freq - 10.0)))
    high_bin = int(np.argmin(np.abs(freq - 80.0)))
    assert spectrum[low_bin] > 20.0 * spectrum[high_bin]


def test_trapez_rsfdata_chain_and_invalid_frequency() -> None:
    n = 64
    d = 0.01
    time = np.arange(n, dtype=np.float64) * d
    data = np.sin(2.0 * np.pi * 10.0 * time).astype(np.float32)
    rsf = RSFData(data, _header_1d(n, d1=d))

    result = rsf.trapez(axis=1, frequency=(5.0, 8.0, 20.0, 25.0))

    np.testing.assert_array_equal(rsf.numpy(), data)
    assert result.shape == rsf.shape
    assert result.header["d1"] == "0.01"
    with pytest.raises(TrapezError, match="f1 <= f2"):
        trapez_filter(data, d=d, frequency=(10.0, 5.0, 20.0, 25.0))


def test_trapez_cli_subprocess(tmp_path: Path) -> None:
    n = 64
    d = 0.01
    time = np.arange(n, dtype=np.float64) * d
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "trapez.rsf"
    write_rsf(
        input_path,
        np.sin(2.0 * np.pi * 10.0 * time).astype(np.float32),
        _header_1d(n, d1=d),
    )

    result = _run_cli(
        "trapez",
        [str(input_path), "out=" + str(output_path), "axis=1", "frequency=5,8,20,25"],
        tmp_path,
    )

    assert result.returncode == 0, result.stderr
    loaded = read_rsf(output_path)
    assert loaded.data.shape == (n,)
    assert loaded.header["label1"] == "Sample"
