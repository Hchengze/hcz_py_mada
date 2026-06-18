from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys

import numpy as np
import pytest

from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf
from pymadagascar.signal import (
    box_smooth as package_box_smooth,
    smooth_rsf as package_smooth_rsf,
    triangle_smooth as package_triangle_smooth,
)
from pymadagascar.signal.smooth import SmoothError, box_smooth, smooth_rsf, triangle_smooth
from pymadagascar.testing.compare import assert_rsf_allclose
from pymadagascar.testing.runner import original_madagascar_available, run_original_madagascar


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _header() -> RSFHeader:
    return RSFHeader(
        {
            "o1": 0.25,
            "d1": 0.5,
            "label1": "Time",
            "unit1": "s",
            "o2": 10.0,
            "d2": 2.0,
            "label2": "Trace",
            "unit2": "m",
        }
    )


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


def test_triangle_smooth_impulse_response() -> None:
    data = np.zeros(7, dtype=np.float32)
    data[3] = 1.0

    result = triangle_smooth(data, rect=3, axes=1)

    assert package_triangle_smooth is triangle_smooth
    np.testing.assert_allclose(
        result,
        np.array([0.0, 1.0, 2.0, 3.0, 2.0, 1.0, 0.0], dtype=np.float32) / 9.0,
        rtol=1e-6,
        atol=1e-7,
    )


def test_box_smooth_impulse_response() -> None:
    data = np.zeros(7, dtype=np.float32)
    data[3] = 1.0

    result = box_smooth(data, rect=2, axes=1)

    assert package_box_smooth is box_smooth
    np.testing.assert_allclose(
        result,
        np.array([0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0], dtype=np.float32) / 3.0,
        rtol=1e-6,
        atol=1e-7,
    )


def test_constant_data_is_unchanged() -> None:
    data = np.full((4, 5), 3.5, dtype=np.float32)

    np.testing.assert_allclose(triangle_smooth(data, rect=(2, 3)), data)
    np.testing.assert_allclose(box_smooth(data, rect=(2, 3)), data)


def test_triangle_smooth_2d_axes_are_rsf_order() -> None:
    data = np.zeros((5, 5), dtype=np.float32)
    data[2, 2] = 1.0

    result = triangle_smooth(data, rect={1: 2, 2: 2})

    assert result.shape == data.shape
    assert np.isclose(float(result.sum()), 1.0)
    assert np.isclose(float(result[2, 2]), 0.25)


def test_repeat_applies_multiple_passes_per_axis() -> None:
    data = np.zeros(9, dtype=np.float32)
    data[4] = 1.0

    result = triangle_smooth(data, rect=2, axes=1, repeat=2)

    np.testing.assert_allclose(
        result,
        np.array([0, 0, 1, 4, 6, 4, 1, 0, 0], dtype=np.float32) / 16.0,
        rtol=1e-6,
        atol=1e-7,
    )


def test_smooth_rejects_complex_data() -> None:
    with pytest.raises(SmoothError, match="real-valued"):
        triangle_smooth(np.array([1.0 + 1.0j], dtype=np.complex64), rect=2)


def test_smooth_rsf_inherits_header_and_preserves_shape(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "smooth.rsf"
    data = np.arange(15, dtype=np.float32).reshape(3, 5)
    write_rsf(input_path, data, _header())

    result = smooth_rsf(input_path, output_path, rect={1: 2, 2: 1})
    loaded = read_rsf(output_path)

    assert package_smooth_rsf is smooth_rsf
    assert result.header_path == output_path.resolve()
    assert loaded.data.shape == data.shape
    assert loaded.data.dtype == np.float32
    assert loaded.header.dimensions == (5, 3)
    assert loaded.header["label1"] == "Time"
    assert loaded.header["unit2"] == "m"


def test_smooth_cli_subprocess(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "smooth.rsf"
    data = np.zeros(7, dtype=np.float32)
    data[3] = 1.0
    write_rsf(input_path, data, RSFHeader({"o1": 0.0, "d1": 1.0}))

    result = _run_cli("smooth", [str(input_path), "out=" + str(output_path), "rect1=3"], tmp_path)

    assert result.returncode == 0, result.stderr
    np.testing.assert_allclose(
        read_rsf(output_path).data,
        np.array([0.0, 1.0, 2.0, 3.0, 2.0, 1.0, 0.0], dtype=np.float32) / 9.0,
        rtol=1e-6,
        atol=1e-7,
    )


def test_boxsmooth_cli_subprocess(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "box.rsf"
    data = np.zeros(7, dtype=np.float32)
    data[3] = 1.0
    write_rsf(input_path, data, RSFHeader({"o1": 0.0, "d1": 1.0}))

    result = _run_cli("boxsmooth", [str(input_path), "out=" + str(output_path), "rect1=2"], tmp_path)

    assert result.returncode == 0, result.stderr
    np.testing.assert_allclose(
        read_rsf(output_path).data,
        np.array([0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0], dtype=np.float32) / 3.0,
        rtol=1e-6,
        atol=1e-7,
    )


@pytest.mark.original_madagascar
def test_original_sfsmooth_constant_comparison_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfsmooth"):
        pytest.skip("Original Madagascar sfsmooth is not installed")

    input_path = tmp_path / "input.rsf"
    original_path = tmp_path / "original.rsf"
    python_path = tmp_path / "python.rsf"
    data = np.ones(11, dtype=np.float32)
    write_rsf(input_path, data, RSFHeader({"o1": 0.0, "d1": 1.0}))

    run_original_madagascar(
        ["sfsmooth", "in=input.rsf", "out=original.rsf", "rect1=3", "repeat=2"],
        cwd=tmp_path,
        require_program="sfsmooth",
    )
    smooth_rsf(input_path, python_path, rect={1: 3}, repeat=2)

    assert_rsf_allclose(original_path, python_path, ignore_keys={"in"})
