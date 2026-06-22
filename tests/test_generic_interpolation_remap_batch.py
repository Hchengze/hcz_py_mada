from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys

import numpy as np
import pytest

from pymadagascar.api import RSFData
from pymadagascar.generic import remap1 as package_remap1
from pymadagascar.generic import spline as package_spline
from pymadagascar.generic import t2warp as package_t2warp
from pymadagascar.generic.remap import (
    RemapError,
    remap1,
    remap1_rsf,
    spline,
    spline_rsf,
    t2warp,
    t2warp_rsf,
)
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf


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


def _header_1d(n1: int, *, o1: float = 0.0, d1: float = 1.0) -> RSFHeader:
    return RSFHeader({"n1": n1, "o1": o1, "d1": d1, "label1": "Time", "unit1": "s"})


def _header_2d(n1: int, n2: int, *, o1: float = 0.0, d1: float = 1.0) -> RSFHeader:
    header = _header_1d(n1, o1=o1, d1=d1)
    header["n2"] = n2
    header["o2"] = 0.0
    header["d2"] = 1.0
    header["label2"] = "Trace"
    return header


def test_remap1_regular_axis_values_header_and_chain(tmp_path: Path) -> None:
    data = np.vstack([np.arange(4), np.arange(4) + 10.0]).astype(np.float32)
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "remap1.rsf"
    write_rsf(input_path, data, _header_2d(4, 2))

    direct = remap1(data, axis=1, n=7, o=0.0, d=0.5)
    remap1_rsf(input_path, output_path, axis=1, n=7, o=0.0, d=0.5)
    loaded = read_rsf(output_path)
    chained = RSFData(data, _header_2d(4, 2)).remap1(axis=1, n=7, d=0.5)

    assert package_remap1 is remap1
    np.testing.assert_allclose(direct[0], np.arange(7, dtype=np.float32) * 0.5)
    np.testing.assert_allclose(loaded.data, direct)
    np.testing.assert_allclose(chained.numpy(), direct)
    assert loaded.header.dimensions == (7, 2)
    assert loaded.header["d1"] == "0.5"
    assert loaded.header["remap1_order"] == "1"


def test_remap1_fill_invalid_order_and_cli(tmp_path: Path) -> None:
    data = np.arange(4, dtype=np.float32)
    filled = remap1(data, n=6, o=-1.0, d=1.0, fill_value=-9.0)

    np.testing.assert_allclose(filled, np.array([-9.0, 0.0, 1.0, 2.0, 3.0, -9.0], dtype=np.float32))
    with pytest.raises(RemapError, match="order=1"):
        remap1(data, order=3)

    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "remap1_cli.rsf"
    write_rsf(input_path, data, _header_1d(4))
    result = _run_cli(
        "remap1",
        [str(input_path), "out=" + str(output_path), "n=7", "o=0", "d=0.5"],
        tmp_path,
    )

    assert result.returncode == 0, result.stderr
    assert read_rsf(output_path).data.shape == (7,)


def test_spline_natural_cubic_header_chain_and_cli(tmp_path: Path) -> None:
    x = np.arange(5, dtype=np.float64)
    data = (x**3).astype(np.float32)
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "spline.rsf"
    cli_path = tmp_path / "spline_cli.rsf"
    write_rsf(input_path, data, _header_1d(data.size))

    direct = spline(data, n=9, o=0.0, d=0.5)
    spline_rsf(input_path, output_path, n=9, o=0.0, d=0.5)
    result = _run_cli("spline", [str(input_path), "out=" + str(cli_path), "n=9", "o=0", "d=0.5"], tmp_path)
    chained = RSFData(data, _header_1d(data.size)).spline(n=9, o=0.0, d=0.5)

    assert package_spline is spline
    assert result.returncode == 0, result.stderr
    np.testing.assert_allclose(read_rsf(output_path).data, direct)
    np.testing.assert_allclose(read_rsf(cli_path).data, direct)
    np.testing.assert_allclose(chained.numpy(), direct)
    assert read_rsf(output_path).header["spline_boundary"] == "natural"
    assert np.isfinite(direct).all()
    with pytest.raises(RemapError, match="at least two"):
        spline(np.ones(1, dtype=np.float32), n=3)


def test_t2warp_forward_inverse_header_chain_and_cli(tmp_path: Path) -> None:
    n = 6
    data = np.arange(n, dtype=np.float32)
    input_path = tmp_path / "input.rsf"
    warp_path = tmp_path / "t2warp.rsf"
    inverse_path = tmp_path / "it2warp.rsf"
    cli_path = tmp_path / "t2warp_cli.rsf"
    write_rsf(input_path, data, _header_1d(n, o1=0.0, d1=1.0))

    direct = t2warp(data, pad=11, input_o=0.0, input_d=1.0)
    t2warp_rsf(input_path, warp_path, pad=11)
    t2warp_rsf(warp_path, inverse_path, inverse=True)
    result = _run_cli("t2warp", [str(input_path), "out=" + str(cli_path), "pad=11"], tmp_path)
    chained = RSFData(data, _header_1d(n)).t2warp(pad=11)

    assert package_t2warp is t2warp
    assert result.returncode == 0, result.stderr
    np.testing.assert_allclose(read_rsf(warp_path).data, direct)
    np.testing.assert_allclose(read_rsf(cli_path).data, direct)
    np.testing.assert_allclose(chained.numpy(), direct)
    assert read_rsf(warp_path).header["n1"] == "11"
    assert read_rsf(warp_path).header["n1_t2warp"] == str(n)
    assert read_rsf(warp_path).header["t2warp_interpolation"] == "linear"
    assert read_rsf(inverse_path).header["n1"] == str(n)
    assert "n1_t2warp" not in read_rsf(inverse_path).header


def test_t2warp_invalid_negative_axis_and_no_inplace_mutation() -> None:
    data = np.arange(5, dtype=np.float32)
    rsf = RSFData(data, _header_1d(5))
    result = rsf.t2warp(pad=7)

    np.testing.assert_array_equal(rsf.numpy(), data)
    assert result.shape == (7,)
    with pytest.raises(RemapError, match="nonnegative"):
        t2warp(data, input_o=-1.0, input_d=1.0, pad=5)
    with pytest.raises(RemapError, match="real-valued"):
        remap1(np.ones(4, dtype=np.complex64), n=8)
