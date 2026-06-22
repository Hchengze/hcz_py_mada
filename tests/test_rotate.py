from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys

import numpy as np
import pytest

from pymadagascar import RSFData, rotate_rsf as package_rotate_rsf
from pymadagascar.generic import rotate_rsf as generic_rotate_rsf
from pymadagascar.generic.rotate import RotateError, rotate_rsf
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf
from pymadagascar.testing.compare import assert_rsf_allclose
from pymadagascar.testing.runner import original_madagascar_available, run_original_madagascar


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _header() -> RSFHeader:
    return RSFHeader(
        {
            "o1": 10.0,
            "d1": 2.0,
            "label1": "Time",
            "unit1": "s",
            "o2": 100.0,
            "d2": 25.0,
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


def test_rotate_rsf_axis1_axis2_preserves_header(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "rotate.rsf"
    data = np.arange(12, dtype=np.float32).reshape(3, 4)
    write_rsf(input_path, data, _header())

    rotate_rsf(input_path, output_path, rotations={1: 1, 2: 2})
    result = read_rsf(output_path)

    expected = np.roll(np.roll(data, shift=-1, axis=1), shift=-2, axis=0)
    assert package_rotate_rsf is rotate_rsf
    assert generic_rotate_rsf is rotate_rsf
    np.testing.assert_array_equal(result.data, expected)
    assert result.header["o1"] == "10"
    assert result.header["d1"] == "2"
    assert result.header["o2"] == "100"
    assert result.header["d2"] == "25"


def test_rotate_rsf_negative_wrap_noop_and_invalid(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "rotate.rsf"
    data = np.array([1, 2, 3, 4], dtype=np.int32)
    write_rsf(input_path, data, RSFHeader({"o1": 0.0, "d1": 1.0}))

    rotate_rsf(input_path, output_path, rotations={1: -1})
    np.testing.assert_array_equal(read_rsf(output_path).data, np.array([4, 1, 2, 3], dtype=np.int32))

    noop_path = tmp_path / "noop.rsf"
    rotate_rsf(input_path, noop_path, rotations={})
    np.testing.assert_array_equal(read_rsf(noop_path).data, data)

    with pytest.raises(RotateError, match="smaller than n1"):
        rotate_rsf(input_path, tmp_path / "bad.rsf", rotations={1: 4})
    with pytest.raises(RotateError, match="outside input ndim"):
        rotate_rsf(input_path, tmp_path / "bad_axis.rsf", rotations={2: 1})


def test_rotate_rsfdata_chain_method(tmp_path: Path) -> None:
    data = RSFData(np.arange(6, dtype=np.float32).reshape(2, 3), _header())

    rotated = data.rotate({1: 2})

    np.testing.assert_array_equal(rotated.numpy(), np.array([[2, 0, 1], [5, 3, 4]], dtype=np.float32))
    np.testing.assert_array_equal(data.numpy(), np.arange(6, dtype=np.float32).reshape(2, 3))


def test_rotate_cli_subprocess(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "rotate.rsf"
    write_rsf(input_path, np.array([1, 2, 3, 4], dtype=np.float32), RSFHeader({"o1": 0.0, "d1": 1.0}))

    result = _run_cli("rotate", [str(input_path), "out=" + str(output_path), "rot1=2"], tmp_path)

    assert result.returncode == 0, result.stderr
    np.testing.assert_array_equal(read_rsf(output_path).data, np.array([3, 4, 1, 2], dtype=np.float32))


def test_scale_console_module_help_and_cli_path(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "scale.rsf"
    write_rsf(input_path, np.array([1, 2, 3], dtype=np.float32), RSFHeader({"o1": 0.0, "d1": 1.0}))

    help_result = _run_cli("scale", ["--help"], tmp_path)
    run_result = _run_cli("scale", [str(input_path), "out=" + str(output_path), "scale=2.0"], tmp_path)

    assert help_result.returncode == 0, help_result.stderr
    assert "pymada-scale" in help_result.stdout
    assert run_result.returncode == 0, run_result.stderr
    np.testing.assert_allclose(read_rsf(output_path).data, np.array([2, 4, 6], dtype=np.float32))


@pytest.mark.original_madagascar
def test_original_sfrotate_comparison_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfrotate"):
        pytest.skip("Original Madagascar sfrotate is not installed")

    input_path = tmp_path / "input.rsf"
    original_path = tmp_path / "original.rsf"
    python_path = tmp_path / "python.rsf"
    write_rsf(input_path, np.arange(6, dtype=np.float32), RSFHeader({"o1": 0.0, "d1": 1.0}))

    run_original_madagascar(
        ["sfrotate", "in=input.rsf", "out=original.rsf", "rot1=2"],
        cwd=tmp_path,
        require_program="sfrotate",
    )
    rotate_rsf(input_path, python_path, rotations={1: 2})

    assert_rsf_allclose(original_path, python_path, ignore_keys={"in"})
