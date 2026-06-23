from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys

import numpy as np
import pytest

import pymadagascar
from pymadagascar.api import RSFData
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf
from pymadagascar.seismic.angle import (
    AngleTransformError,
    cos2ang,
    cos2ang_rsf,
    isin2ang,
    isin2ang_rsf,
)
from pymadagascar.seismic.map2coh import Map2CohError, map2coh, map2coh_rsf


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
        timeout=30,
    )


def _angle_header(nz: int, nt: int) -> RSFHeader:
    return RSFHeader(
        {
            "n1": nz,
            "o1": 0.0,
            "d1": 1.0,
            "label1": "Depth",
            "n2": nt,
            "o2": -2.0,
            "d2": 1.0,
            "label2": "Inverse trig coordinate",
        }
    )


def _map_header(nt: int, nmap: int) -> RSFHeader:
    return RSFHeader(
        {
            "n1": nt,
            "o1": 0.0,
            "d1": 0.004,
            "label1": "Time",
            "unit1": "s",
            "n2": nmap,
            "o2": 0.0,
            "d2": 1.0,
            "label2": "Slope",
        }
    )


def test_cos2ang_values_header_chain_cli_and_invalid_params(tmp_path: Path) -> None:
    source_coord = -2.0 + np.arange(5, dtype=np.float32)
    panel = np.column_stack([source_coord, source_coord + 10.0]).astype(np.float32)
    input_path = tmp_path / "cos_panel.rsf"
    output_path = tmp_path / "cos_angle.rsf"
    cli_path = tmp_path / "cos_cli.rsf"
    write_rsf(input_path, panel, _angle_header(nz=2, nt=5))

    direct = cos2ang(panel, t0=-2.0, dt=1.0, transform_axis=2, na=2, a0=60.0, da=-30.0)
    original = RSFData(panel, _angle_header(nz=2, nt=5))
    chained = original.cos2ang(transform_axis=2, na=2, a0=60.0, da=-30.0)
    cos2ang_rsf(input_path, output_path, transform_axis=2, na=2, a0=60.0, da=-30.0)
    result = _run_cli(
        "cos2ang",
        [str(input_path), "out=" + str(cli_path), "axis=2", "na=2", "a0=60", "da=-30"],
        tmp_path,
    )

    expected_coords = np.array([-2.0, -1.0 / np.cos(np.deg2rad(30.0))], dtype=np.float64)
    expected = np.column_stack([expected_coords, expected_coords + 10.0]).astype(np.float32)
    assert result.returncode == 0, result.stderr
    np.testing.assert_allclose(direct, expected, atol=1e-6)
    np.testing.assert_allclose(read_rsf(output_path).data, expected, atol=1e-6)
    np.testing.assert_allclose(read_rsf(cli_path).data, expected, atol=1e-6)
    np.testing.assert_allclose(chained.numpy(), expected, atol=1e-6)
    np.testing.assert_array_equal(original.numpy(), panel)
    header = read_rsf(output_path).header
    assert header.dimensions == (2, 2)
    assert header["label2"] == "Angle"
    assert header["cos2ang_source"] == "../src-master/system/seismic/Mcos2ang.c"
    assert not hasattr(pymadagascar, "cos2ang_rsf")
    with pytest.raises(AngleTransformError, match="at least two dimensions"):
        cos2ang(np.arange(5, dtype=np.float32), t0=-2.0, dt=1.0)
    with pytest.raises(AngleTransformError, match="dt"):
        cos2ang(panel, t0=-2.0, dt=0.0)


def test_isin2ang_values_header_chain_cli_and_invalid_params(tmp_path: Path) -> None:
    source_coord = 1.0 + np.arange(5, dtype=np.float32)
    panel = np.column_stack([source_coord, 2.0 * source_coord]).astype(np.float32)
    input_path = tmp_path / "sin_panel.rsf"
    output_path = tmp_path / "sin_angle.rsf"
    cli_path = tmp_path / "sin_cli.rsf"
    header = _angle_header(nz=2, nt=5)
    header["o2"] = 1.0
    write_rsf(input_path, panel, header)

    direct = isin2ang(panel, t0=1.0, dt=1.0, transform_axis=2, na=2, a0=30.0, da=30.0)
    original = RSFData(panel, header)
    chained = original.isin2ang(transform_axis=2, na=2, a0=30.0, da=30.0)
    isin2ang_rsf(input_path, output_path, transform_axis=2, na=2, a0=30.0, da=30.0)
    result = _run_cli(
        "isin2ang",
        [str(input_path), "out=" + str(cli_path), "axis=2", "na=2", "a0=30", "da=30"],
        tmp_path,
    )

    expected_coords = np.array(
        [1.0 / np.sin(np.deg2rad(30.0)), 1.0 / np.sin(np.deg2rad(60.0))],
        dtype=np.float64,
    )
    expected = np.column_stack([expected_coords, 2.0 * expected_coords]).astype(np.float32)
    assert result.returncode == 0, result.stderr
    np.testing.assert_allclose(direct, expected, atol=1e-6)
    np.testing.assert_allclose(read_rsf(output_path).data, expected, atol=1e-6)
    np.testing.assert_allclose(read_rsf(cli_path).data, expected, atol=1e-6)
    np.testing.assert_allclose(chained.numpy(), expected, atol=1e-6)
    np.testing.assert_array_equal(original.numpy(), panel)
    assert read_rsf(output_path).header["isin2ang_source"] == "../src-master/system/seismic/Misin2ang.c"
    assert not hasattr(pymadagascar, "isin2ang_rsf")
    with pytest.raises(AngleTransformError, match="na"):
        isin2ang(panel, t0=1.0, dt=1.0, na=0)
    with pytest.raises((AngleTransformError, ValueError), match="axis"):
        isin2ang(panel, t0=1.0, dt=1.0, transform_axis=3)


def test_map2coh_values_header_chain_cli_and_invalid_params(tmp_path: Path) -> None:
    data = np.array([[1.0, 2.0, 0.0], [3.0, 0.0, 4.0]], dtype=np.float32)
    parameter_map = np.array([[0.0, 1.0, 2.0], [1.0, 2.0, 0.0]], dtype=np.float32)
    input_path = tmp_path / "cmp.rsf"
    map_path = tmp_path / "map.rsf"
    output_path = tmp_path / "coh.rsf"
    cli_path = tmp_path / "coh_cli.rsf"
    header = _map_header(nt=3, nmap=2)
    write_rsf(input_path, data, header)
    write_rsf(map_path, parameter_map, header)

    direct = map2coh(data, parameter_map, nv=3, v0=0.0, dv=1.0, axis_time=1, axis_map=2)
    original = RSFData(data, header)
    chained = original.map2coh(parameter_map, nv=3, v0=0.0, dv=1.0)
    map2coh_rsf(input_path, map_path, output_path, nv=3, v0=0.0, dv=1.0)
    result = _run_cli(
        "map2coh",
        [str(input_path), "map=" + str(map_path), "out=" + str(cli_path), "nv=3", "v0=0", "dv=1"],
        tmp_path,
    )

    expected = np.array([[1.0, 0.0, 4.0], [3.0, 2.0, 0.0], [0.0, 0.0, 0.0]], dtype=np.float32)
    assert result.returncode == 0, result.stderr
    np.testing.assert_allclose(direct, expected, atol=1e-6)
    np.testing.assert_allclose(read_rsf(output_path).data, expected, atol=1e-6)
    np.testing.assert_allclose(read_rsf(cli_path).data, expected, atol=1e-6)
    np.testing.assert_allclose(chained.numpy(), expected, atol=1e-6)
    np.testing.assert_array_equal(original.numpy(), data)
    out_header = read_rsf(output_path).header
    assert out_header.dimensions == (3, 3)
    assert out_header["label2"] == "Velocity"
    assert out_header["map2coh_source"] == "../src-master/system/seismic/Mmap2coh.c"
    assert not hasattr(pymadagascar, "map2coh_rsf")
    with pytest.raises(Map2CohError, match="same shape"):
        map2coh(data, parameter_map[:, :2], nv=3, v0=0.0, dv=1.0)
    with pytest.raises(Map2CohError, match="axis_time"):
        map2coh(data, parameter_map, nv=3, v0=0.0, dv=1.0, axis_time=1, axis_map=1)


@pytest.mark.parametrize("module", ["cos2ang", "isin2ang", "map2coh"])
def test_console_script_help_smoke(module: str) -> None:
    result = subprocess.run(
        [sys.executable, "-m", f"pymadagascar.cli.{module}", "--help"],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=20,
    )
    assert result.returncode == 0
    assert "Madagascar-style parameters" in result.stdout
