from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys

import numpy as np
import pytest

from pymadagascar.generic import (
    cut_rsf as package_cut_rsf,
    mask_rsf as package_mask_rsf,
    reverse_rsf as package_reverse_rsf,
)
from pymadagascar.generic.cut import CutError, cut_rsf
from pymadagascar.generic.mask import MaskError, mask_rsf
from pymadagascar.generic.reverse import reverse_rsf
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


def test_mask_rsf_min_max_writes_native_int(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "mask.rsf"
    data = np.array([-1.0, 0.0, 0.5, 1.5, np.nan], dtype=np.float32)
    write_rsf(input_path, data, RSFHeader({"o1": 0.0, "d1": 1.0}))

    mask_rsf(input_path, output_path, min_value=0.0, max_value=1.0)
    result = read_rsf(output_path)

    assert package_mask_rsf is mask_rsf
    assert result.data.dtype == np.int32
    assert result.header["data_format"] == "native_int"
    np.testing.assert_array_equal(result.data, np.array([0, 1, 1, 0, 0], dtype=np.int32))


def test_mask_rejects_inverted_range(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    write_rsf(input_path, np.arange(3, dtype=np.float32), RSFHeader({"o1": 0.0, "d1": 1.0}))

    with pytest.raises(MaskError, match="min=.*<= max"):
        mask_rsf(input_path, tmp_path / "bad.rsf", min_value=2.0, max_value=1.0)


def test_cut_rsf_1d_zeroes_selected_range(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "cut.rsf"
    data = np.arange(6, dtype=np.float32)
    write_rsf(input_path, data, RSFHeader({"o1": 0.0, "d1": 1.0}))

    cut_rsf(input_path, output_path, axis=1, f=2, n=2)
    result = read_rsf(output_path)

    assert package_cut_rsf is cut_rsf
    np.testing.assert_array_equal(result.data, np.array([0, 1, 0, 0, 4, 5], dtype=np.float32))
    assert result.header.dimensions == (6,)


def test_cut_rsf_2d_uses_rsf_axis_order(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "cut2d.rsf"
    data = np.arange(12, dtype=np.float32).reshape(3, 4)
    write_rsf(input_path, data, _header())

    cut_rsf(input_path, output_path, axis=1, f=1, n=2)
    result = read_rsf(output_path)

    expected = data.copy()
    expected[:, 1:3] = 0
    np.testing.assert_array_equal(result.data, expected)
    assert result.header["o1"] == "10"
    assert result.header["d2"] == "25"


def test_cut_rsf_2d_multi_axis_window(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "cutbox.rsf"
    data = np.arange(12, dtype=np.float32).reshape(3, 4)
    write_rsf(input_path, data, _header())

    cut_rsf(input_path, output_path, axis=[1, 2], f=[1, 1], n=[2, 1])
    result = read_rsf(output_path)

    expected = data.copy()
    expected[1:2, 1:3] = 0
    np.testing.assert_array_equal(result.data, expected)


def test_cut_rejects_out_of_bounds_window(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    write_rsf(input_path, np.arange(4, dtype=np.float32), RSFHeader({"o1": 0.0, "d1": 1.0}))

    with pytest.raises(CutError, match="exceeds axis"):
        cut_rsf(input_path, tmp_path / "bad.rsf", axis=1, f=3, n=2)


def test_reverse_rsf_1d_updates_header(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "reverse.rsf"
    write_rsf(input_path, np.array([1, 2, 3], dtype=np.float32), RSFHeader({"o1": 10.0, "d1": 2.0}))

    reverse_rsf(input_path, output_path, axis=1)
    result = read_rsf(output_path)

    assert package_reverse_rsf is reverse_rsf
    np.testing.assert_array_equal(result.data, np.array([3, 2, 1], dtype=np.float32))
    assert result.header["o1"] == "14"
    assert result.header["d1"] == "-2"


def test_reverse_rsf_2d_axis2_updates_only_axis2_header(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "reverse2d.rsf"
    data = np.arange(12, dtype=np.float32).reshape(3, 4)
    write_rsf(input_path, data, _header())

    reverse_rsf(input_path, output_path, axis=2)
    result = read_rsf(output_path)

    np.testing.assert_array_equal(result.data, data[::-1, :])
    assert result.header["o1"] == "10"
    assert result.header["d1"] == "2"
    assert result.header["o2"] == "150"
    assert result.header["d2"] == "-25"


def test_reverse_rsf_can_preserve_header(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "reverse_keep.rsf"
    write_rsf(input_path, np.arange(4, dtype=np.float32), RSFHeader({"o1": 1.0, "d1": 0.5}))

    reverse_rsf(input_path, output_path, axis=1, update_header=False)
    result = read_rsf(output_path)

    np.testing.assert_array_equal(result.data, np.array([3, 2, 1, 0], dtype=np.float32))
    assert result.header["o1"] == "1"
    assert result.header["d1"] == "0.5"


def test_reverse_cli_which_zero_is_noop(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "noop.rsf"
    data = np.arange(4, dtype=np.float32)
    write_rsf(input_path, data, RSFHeader({"o1": 1.0, "d1": 0.5}))

    result = _run_cli("reverse", [str(input_path), "out=" + str(output_path), "which=0"], tmp_path)

    assert result.returncode == 0, result.stderr
    loaded = read_rsf(output_path)
    np.testing.assert_array_equal(loaded.data, data)
    assert loaded.header["o1"] == "1"
    assert loaded.header["d1"] == "0.5"


def test_mask_cut_reverse_cli_subprocess(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    mask_path = tmp_path / "mask.rsf"
    cut_path = tmp_path / "cut.rsf"
    reverse_path = tmp_path / "reverse.rsf"
    data = np.arange(6, dtype=np.float32)
    write_rsf(input_path, data, RSFHeader({"o1": 0.0, "d1": 1.0}))

    mask = _run_cli("mask", [str(input_path), "out=" + str(mask_path), "min=2", "max=4"], tmp_path)
    cut = _run_cli("cut", [str(input_path), "out=" + str(cut_path), "axis=1", "f=2", "n=2"], tmp_path)
    reverse = _run_cli("reverse", [str(input_path), "out=" + str(reverse_path), "axis=1"], tmp_path)

    assert mask.returncode == 0, mask.stderr
    assert cut.returncode == 0, cut.stderr
    assert reverse.returncode == 0, reverse.stderr
    np.testing.assert_array_equal(read_rsf(mask_path).data, np.array([0, 0, 1, 1, 1, 0], dtype=np.int32))
    np.testing.assert_array_equal(read_rsf(cut_path).data, np.array([0, 1, 0, 0, 4, 5], dtype=np.float32))
    np.testing.assert_array_equal(read_rsf(reverse_path).data, data[::-1])


@pytest.mark.original_madagascar
def test_original_sfmask_comparison_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfmask"):
        pytest.skip("Original Madagascar sfmask is not installed")

    input_path = tmp_path / "input.rsf"
    original_path = tmp_path / "original.rsf"
    python_path = tmp_path / "python.rsf"
    write_rsf(input_path, np.array([-1.0, 0.0, 0.5, 2.0], dtype=np.float32), RSFHeader({"o1": 0.0, "d1": 1.0}))

    run_original_madagascar(
        ["sfmask", "in=input.rsf", "out=original.rsf", "min=0", "max=1"],
        cwd=tmp_path,
        require_program="sfmask",
    )
    mask_rsf(input_path, python_path, min_value=0.0, max_value=1.0)

    assert_rsf_allclose(original_path, python_path, ignore_keys={"in"})


@pytest.mark.original_madagascar
def test_original_sfcut_comparison_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfcut"):
        pytest.skip("Original Madagascar sfcut is not installed")

    input_path = tmp_path / "input.rsf"
    original_path = tmp_path / "original.rsf"
    python_path = tmp_path / "python.rsf"
    write_rsf(input_path, np.arange(6, dtype=np.float32), RSFHeader({"o1": 0.0, "d1": 1.0}))

    run_original_madagascar(
        ["sfcut", "in=input.rsf", "out=original.rsf", "f1=2", "n1=2"],
        cwd=tmp_path,
        require_program="sfcut",
    )
    cut_rsf(input_path, python_path, axis=1, f=2, n=2)

    assert_rsf_allclose(original_path, python_path, ignore_keys={"in"})


@pytest.mark.original_madagascar
def test_original_sfreverse_comparison_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfreverse"):
        pytest.skip("Original Madagascar sfreverse is not installed")

    input_path = tmp_path / "input.rsf"
    original_path = tmp_path / "original.rsf"
    python_path = tmp_path / "python.rsf"
    write_rsf(input_path, np.array([1, 2, 3], dtype=np.float32), RSFHeader({"o1": 10.0, "d1": 2.0}))

    run_original_madagascar(
        ["sfreverse", "in=input.rsf", "out=original.rsf", "which=1"],
        cwd=tmp_path,
        require_program="sfreverse",
    )
    reverse_rsf(input_path, python_path, axis=1)

    assert_rsf_allclose(original_path, python_path, ignore_keys={"in"})
