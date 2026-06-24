from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from pymadagascar import RSFData
from pymadagascar.generic.otsu import OtsuError, otsu_rsf, otsu_threshold
from pymadagascar.generic.tclip import TClipError, tclip, tclip_rsf
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf
from pymadagascar.seismic.ai2refl import AI2ReflError, refl2ai, refl2ai_rsf


ROOT = Path(__file__).resolve().parents[1]


def _header_1d(n1: int) -> RSFHeader:
    return RSFHeader({"n1": n1, "o1": 0.0, "d1": 1.0})


def _header_2d(n1: int, n2: int) -> RSFHeader:
    return RSFHeader({"n1": n1, "n2": n2, "o1": 0.0, "d1": 1.0, "o2": 0.0, "d2": 1.0})


def test_tclip_numeric_rsf_and_rsfdata_no_inplace(tmp_path: Path) -> None:
    data = np.array([-0.5, 0.2, 0.5, 0.8, 1.5], dtype=np.float32)
    expected = np.array([0.0, 0.2, 0.5, 0.8, 1.0], dtype=np.float32)

    np.testing.assert_array_equal(tclip(data, lowercut=0.2, uppercut=0.8), expected)
    np.testing.assert_array_equal(data, np.array([-0.5, 0.2, 0.5, 0.8, 1.5], dtype=np.float32))

    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "output.rsf"
    write_rsf(input_path, data, _header_1d(data.size))
    tclip_rsf(input_path, output_path, lowercut=0.2, uppercut=0.8)
    rsf = read_rsf(output_path)
    np.testing.assert_array_equal(rsf.data, expected)
    assert rsf.header["tclip_source"] == "../src-master/system/generic/Mtclip.c"

    source = RSFData(data, _header_1d(data.size))
    result = source.tclip(lowercut=0.2, uppercut=0.8)
    assert result is not source
    np.testing.assert_array_equal(result.numpy(), expected)
    np.testing.assert_array_equal(source.numpy(), data)


def test_tclip_invalid_params_and_cli(tmp_path: Path) -> None:
    with pytest.raises(TClipError, match="lowercut"):
        tclip([0.0, 1.0], lowercut=2.0, uppercut=1.0)
    with pytest.raises(TClipError, match="real-valued"):
        tclip(np.array([1 + 1j]))

    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "output.rsf"
    write_rsf(input_path, np.array([-1.0, 0.5, 2.0], dtype=np.float32), _header_1d(3))
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pymadagascar.cli.tclip",
            str(input_path),
            f"out={output_path}",
            "lowercut=0.0",
            "uppercut=1.0",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    np.testing.assert_array_equal(read_rsf(output_path).data, np.array([0.0, 0.5, 1.0], dtype=np.float32))


def test_otsu_threshold_rsf_cli_and_invalid_input(tmp_path: Path) -> None:
    hist = np.array([6, 4, 0, 0, 4, 6], dtype=np.int32)
    assert otsu_threshold(hist, o1=10.0, d1=2.0) == 13.0

    input_path = tmp_path / "hist.rsf"
    write_rsf(input_path, hist, RSFHeader({"n1": hist.size, "o1": 10.0, "d1": 2.0}))
    assert otsu_rsf(input_path) == 13.0

    result = subprocess.run(
        [sys.executable, "-m", "pymadagascar.cli.otsu", str(input_path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert result.stdout.strip() == "threshold=13"

    with pytest.raises(OtsuError, match="integer"):
        otsu_threshold(np.array([1.0, 2.0]))
    with pytest.raises(OtsuError, match="nonnegative"):
        otsu_threshold(np.array([1, -1]))


def test_refl2ai_numeric_rsf_rsfdata_and_cli(tmp_path: Path) -> None:
    refl = np.array([[0.0, 0.2, -0.2], [0.1, 0.0, 0.25]], dtype=np.float32)
    a0 = np.array([1000.0, 2000.0], dtype=np.float32)
    expected = np.array(
        [
            [1000.0, 1000.0, 1500.0],
            [2000.0, 2444.444444, 2444.444444],
        ],
        dtype=np.float32,
    )
    np.testing.assert_allclose(refl2ai(refl, a0, axis=1), expected, rtol=1e-6)

    input_path = tmp_path / "refl.rsf"
    a0_path = tmp_path / "a0.rsf"
    output_path = tmp_path / "ai.rsf"
    write_rsf(input_path, refl, _header_2d(n1=3, n2=2))
    write_rsf(a0_path, a0, RSFHeader({"n1": 2}))
    refl2ai_rsf(input_path, a0_path, output_path, axis=1)
    rsf = read_rsf(output_path)
    np.testing.assert_allclose(rsf.data, expected, rtol=1e-6)
    assert rsf.header["refl2ai_source"] == "../src-master/system/seismic/Mrefl2ai.c"

    source = RSFData(refl, _header_2d(n1=3, n2=2))
    result = source.refl2ai(a0, axis=1)
    assert result is not source
    np.testing.assert_allclose(result.numpy(), expected, rtol=1e-6)
    np.testing.assert_array_equal(source.numpy(), refl)

    cli_output = tmp_path / "cli_ai.rsf"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pymadagascar.cli.refl2ai",
            str(input_path),
            f"out={cli_output}",
            f"a0={a0_path}",
            "axis=1",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=20,
    )
    assert completed.returncode == 0, completed.stderr + completed.stdout
    np.testing.assert_allclose(read_rsf(cli_output).data, expected, rtol=1e-6)


def test_refl2ai_invalid_inputs() -> None:
    with pytest.raises(AI2ReflError, match="one initial impedance"):
        refl2ai(np.zeros((2, 3), dtype=np.float32), np.ones(3, dtype=np.float32), axis=1)
    with pytest.raises(AI2ReflError, match="reflectivity is 1"):
        refl2ai(np.array([1.0], dtype=np.float32), np.array([1000.0], dtype=np.float32), axis=1)
    with pytest.raises(AI2ReflError, match="real-valued"):
        refl2ai(np.array([0.1 + 0.1j]), np.array([1000.0]), axis=1)
