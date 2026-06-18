from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys

import numpy as np
import pytest

from pymadagascar.generic.header_mask import (
    HeaderMaskError,
    header_cut_rsf,
    header_window_rsf,
)
from pymadagascar.io.rsf import RSFHeader, read_header, read_rsf, write_rsf
from pymadagascar.testing.compare import assert_rsf_allclose
from pymadagascar.testing.runner import original_madagascar_available, run_original_madagascar


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _header(**updates: object) -> RSFHeader:
    values: dict[str, object] = {
        "o1": 0.0,
        "d1": 1.0,
        "label1": "Sample",
        "o2": 10.0,
        "d2": 2.0,
        "label2": "Trace",
    }
    values.update(updates)
    return RSFHeader(values)


def _write(path: Path, data: np.ndarray, *, header: RSFHeader | None = None) -> np.ndarray:
    write_rsf(path, data, _header() if header is None else header)
    return data


def _write_mask(path: Path, values: list[int] | np.ndarray) -> np.ndarray:
    data = np.asarray(values, dtype=np.int32)
    write_rsf(path, data, RSFHeader({"o1": 0.0, "d1": 1.0, "label1": "Mask"}))
    return data


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


def test_header_window_1d_continuous_mask_updates_axis(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    mask_path = tmp_path / "mask.rsf"
    output_path = tmp_path / "window.rsf"
    data = _write(input_path, np.arange(5, dtype=np.float32), header=_header(o1=0.5, d1=0.25))
    _write_mask(mask_path, [0, 1, 1, 1, 0])

    header_window_rsf(input_path, mask_path, output_path, axis=1)
    result = read_rsf(output_path)

    np.testing.assert_allclose(result.data, data[1:4])
    header = read_header(output_path)
    assert int(header["n1"]) == 3
    assert float(header["o1"]) == pytest.approx(0.75)
    assert float(header["d1"]) == pytest.approx(0.25)


def test_header_window_2d_axis1_and_axis2(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    axis1_mask = tmp_path / "axis1_mask.rsf"
    axis2_mask = tmp_path / "axis2_mask.rsf"
    axis1_out = tmp_path / "axis1.rsf"
    axis2_out = tmp_path / "axis2.rsf"
    data = _write(input_path, np.arange(12, dtype=np.float32).reshape(3, 4))
    _write_mask(axis1_mask, [0, 1, 1, 0])
    _write_mask(axis2_mask, [0, 1, 1])

    header_window_rsf(input_path, axis1_mask, axis1_out, axis=1)
    header_window_rsf(input_path, axis2_mask, axis2_out, axis=2)

    np.testing.assert_allclose(read_rsf(axis1_out).data, data[:, 1:3])
    assert int(read_header(axis1_out)["n1"]) == 2
    assert float(read_header(axis1_out)["o1"]) == pytest.approx(1.0)
    np.testing.assert_allclose(read_rsf(axis2_out).data, data[1:3, :])
    assert int(read_header(axis2_out)["n2"]) == 2
    assert float(read_header(axis2_out)["o2"]) == pytest.approx(12.0)


def test_header_window_rejects_noncontinuous_and_mismatched_masks(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    noncontinuous = tmp_path / "noncontinuous.rsf"
    mismatch = tmp_path / "mismatch.rsf"
    _write(input_path, np.arange(5, dtype=np.float32), header=_header(o1=0.0, d1=1.0))
    _write_mask(noncontinuous, [1, 0, 1, 0, 0])
    _write_mask(mismatch, [1, 1])

    with pytest.raises(HeaderMaskError, match="continuous"):
        header_window_rsf(input_path, noncontinuous, tmp_path / "bad.rsf", axis=1)
    with pytest.raises(HeaderMaskError, match="does not match"):
        header_window_rsf(input_path, mismatch, tmp_path / "bad2.rsf", axis=1)


def test_header_cut_1d_and_cut_nonzero_policy(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    mask_path = tmp_path / "mask.rsf"
    cut_nonzero = tmp_path / "cut_nonzero.rsf"
    cut_zero = tmp_path / "cut_zero.rsf"
    data = _write(input_path, np.array([1, 2, 3, 4], dtype=np.int32), header=_header(o1=0.0, d1=1.0))
    _write_mask(mask_path, [1, 0, 1, 0])

    header_cut_rsf(input_path, mask_path, cut_nonzero, axis=1)
    header_cut_rsf(input_path, mask_path, cut_zero, axis=1, cut_nonzero=False)

    np.testing.assert_array_equal(read_rsf(cut_nonzero).data, np.array([0, 2, 0, 4], dtype=np.int32))
    np.testing.assert_array_equal(read_rsf(cut_zero).data, np.array([1, 0, 3, 0], dtype=np.int32))
    np.testing.assert_array_equal(read_rsf(input_path).data, data)


def test_header_cut_2d_axes_and_header_inheritance(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    axis1_mask = tmp_path / "axis1_mask.rsf"
    axis2_mask = tmp_path / "axis2_mask.rsf"
    axis1_out = tmp_path / "axis1_cut.rsf"
    axis2_out = tmp_path / "axis2_cut.rsf"
    data = _write(input_path, np.arange(12, dtype=np.float32).reshape(3, 4))
    _write_mask(axis1_mask, [0, 1, 0, 1])
    _write_mask(axis2_mask, [0, 1, 0])

    header_cut_rsf(input_path, axis1_mask, axis1_out, axis=1)
    header_cut_rsf(input_path, axis2_mask, axis2_out, axis=2, cut_nonzero=False)

    expected_axis1 = data.copy()
    expected_axis1[:, [1, 3]] = 0
    np.testing.assert_allclose(read_rsf(axis1_out).data, expected_axis1)
    expected_axis2 = data.copy()
    expected_axis2[[0, 2], :] = 0
    np.testing.assert_allclose(read_rsf(axis2_out).data, expected_axis2)
    assert read_header(axis1_out)["label2"] == "Trace"
    assert read_rsf(axis1_out).data.shape == data.shape


def test_header_cut_rejects_mismatched_mask(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    mask_path = tmp_path / "mask.rsf"
    _write(input_path, np.arange(6, dtype=np.float32).reshape(2, 3))
    _write_mask(mask_path, [1, 0])

    with pytest.raises(HeaderMaskError, match="does not match"):
        header_cut_rsf(input_path, mask_path, tmp_path / "out.rsf", axis=1)


def test_headerwindow_and_headercut_cli_subprocess(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    mask_path = tmp_path / "mask.rsf"
    window_out = tmp_path / "window.rsf"
    cut_out = tmp_path / "cut.rsf"
    data = _write(input_path, np.arange(12, dtype=np.float32).reshape(3, 4))
    _write_mask(mask_path, [0, 1, 1])

    window_result = _run_cli(
        "headerwindow",
        [str(input_path), str(mask_path), "out=" + str(window_out), "axis=2"],
        tmp_path,
    )
    assert window_result.returncode == 0, window_result.stderr
    np.testing.assert_allclose(read_rsf(window_out).data, data[1:3, :])

    cut_result = _run_cli(
        "headercut",
        [str(input_path), "mask=" + str(mask_path), "out=" + str(cut_out), "axis=2", "cut_nonzero=n"],
        tmp_path,
    )
    assert cut_result.returncode == 0, cut_result.stderr
    expected = data.copy()
    expected[0, :] = 0
    np.testing.assert_allclose(read_rsf(cut_out).data, expected)


def test_original_sfheaderwindow_comparison_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfheaderwindow"):
        pytest.skip("Original Madagascar sfheaderwindow is not installed")

    input_path = tmp_path / "input.rsf"
    mask_path = tmp_path / "mask.rsf"
    original = tmp_path / "original.rsf"
    python = tmp_path / "python.rsf"
    data = np.arange(12, dtype=np.float32).reshape(4, 3)
    _write(input_path, data, header=_header(o2=0.0, d2=1.0))
    _write_mask(mask_path, [1, 1, 0, 0])

    run_original_madagascar(
        ["sfheaderwindow", "in=input.rsf", "mask=mask.rsf", "out=original.rsf"],
        cwd=tmp_path,
        require_program="sfheaderwindow",
    )
    header_window_rsf(input_path, mask_path, python, axis=2)
    assert_rsf_allclose(original, python, ignore_keys={"in"})


def test_original_sfheadercut_comparison_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfheadercut"):
        pytest.skip("Original Madagascar sfheadercut is not installed")

    input_path = tmp_path / "input.rsf"
    mask_path = tmp_path / "mask.rsf"
    original = tmp_path / "original.rsf"
    python = tmp_path / "python.rsf"
    _write(input_path, np.arange(12, dtype=np.float32).reshape(4, 3))
    _write_mask(mask_path, [1, 0, 1, 0])

    run_original_madagascar(
        ["sfheadercut", "in=input.rsf", "mask=mask.rsf", "out=original.rsf"],
        cwd=tmp_path,
        require_program="sfheadercut",
    )
    header_cut_rsf(input_path, mask_path, python, axis=2, cut_nonzero=False)
    assert_rsf_allclose(original, python, ignore_keys={"in"})
