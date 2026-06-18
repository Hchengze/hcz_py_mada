from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys

import numpy as np
import pytest

from pymadagascar.generic.array_math import ArrayMathError, divide_rsf, multiply_rsf, tpow_rsf
from pymadagascar.generic.interleave import InterleaveError, interleave_rsf
from pymadagascar.io.rsf import RSFHeader, read_header, read_rsf, write_rsf
from pymadagascar.testing.compare import assert_rsf_allclose
from pymadagascar.testing.runner import original_madagascar_available, run_original_madagascar


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _header(**updates: object) -> RSFHeader:
    values: dict[str, object] = {
        "o1": 0.0,
        "d1": 0.5,
        "label1": "Time",
        "unit1": "s",
        "o2": 10.0,
        "d2": 2.0,
        "label2": "Trace",
    }
    values.update(updates)
    return RSFHeader(values)


def _write(path: Path, data: np.ndarray, *, header: RSFHeader | None = None) -> np.ndarray:
    write_rsf(path, data, _header() if header is None else header)
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


def test_multiply_rsf_file_and_scalar_header_dtype(tmp_path: Path) -> None:
    a = tmp_path / "a.rsf"
    b = tmp_path / "b.rsf"
    out_file = tmp_path / "mul_file.rsf"
    out_scalar = tmp_path / "mul_scalar.rsf"
    data_a = _write(a, np.array([[1, 2, 3], [4, 5, 6]], dtype=np.int32))
    data_b = _write(b, np.array([[2, 3, 4], [5, 6, 7]], dtype=np.int32))

    multiply_rsf(a, b, out_file)
    multiply_rsf(a, None, out_scalar, scalar=2.5)

    file_result = read_rsf(out_file)
    scalar_result = read_rsf(out_scalar)
    np.testing.assert_array_equal(file_result.data, data_a * data_b)
    assert file_result.data.dtype == np.dtype("int32")
    np.testing.assert_allclose(scalar_result.data, data_a.astype(np.float32) * 2.5)
    assert scalar_result.data.dtype == np.dtype("float32")
    assert read_header(out_scalar)["label1"] == "Time"


def test_multiply_rsf_shape_mismatch(tmp_path: Path) -> None:
    a = tmp_path / "a.rsf"
    b = tmp_path / "b.rsf"
    _write(a, np.ones((2, 3), dtype=np.float32))
    _write(b, np.ones((3, 2), dtype=np.float32))

    with pytest.raises(ArrayMathError, match="shape mismatch"):
        multiply_rsf(a, b, tmp_path / "out.rsf")


def test_mul_cli_subprocess(tmp_path: Path) -> None:
    a = tmp_path / "a.rsf"
    b = tmp_path / "b.rsf"
    out_file = tmp_path / "mul_file.rsf"
    out_scalar = tmp_path / "mul_scalar.rsf"
    _write(a, np.array([1.0, 2.0, 3.0], dtype=np.float32))
    _write(b, np.array([4.0, 5.0, 6.0], dtype=np.float32))

    result = _run_cli("mul", [str(a), str(b), "out=" + str(out_file)], tmp_path)
    assert result.returncode == 0, result.stderr
    np.testing.assert_allclose(read_rsf(out_file).data, np.array([4.0, 10.0, 18.0], dtype=np.float32))

    result = _run_cli("mul", [str(a), "out=" + str(out_scalar), "scalar=3.0"], tmp_path)
    assert result.returncode == 0, result.stderr
    np.testing.assert_allclose(read_rsf(out_scalar).data, np.array([3.0, 6.0, 9.0], dtype=np.float32))


def test_divide_rsf_file_scalar_and_zero_policies(tmp_path: Path) -> None:
    a = tmp_path / "a.rsf"
    b = tmp_path / "b.rsf"
    out_file = tmp_path / "div_file.rsf"
    out_scalar = tmp_path / "div_scalar.rsf"
    out_nan = tmp_path / "div_nan.rsf"
    _write(a, np.array([2, 4, 6], dtype=np.int32))
    _write(b, np.array([1, 2, 3], dtype=np.int32))

    divide_rsf(a, b, out_file)
    divide_rsf(a, None, out_scalar, scalar=2.0)

    np.testing.assert_allclose(read_rsf(out_file).data, np.array([2, 2, 2], dtype=np.float32))
    assert read_rsf(out_file).data.dtype == np.dtype("float32")
    np.testing.assert_allclose(read_rsf(out_scalar).data, np.array([1, 2, 3], dtype=np.float32))

    with pytest.raises(ArrayMathError, match="zero"):
        divide_rsf(a, None, tmp_path / "zero_scalar.rsf", scalar=0.0)

    _write(b, np.array([1, 0, 3], dtype=np.int32))
    with pytest.raises(ArrayMathError, match="zero"):
        divide_rsf(a, b, tmp_path / "zero_file.rsf")
    divide_rsf(a, b, out_nan, zero_policy="nan")
    result = read_rsf(out_nan).data
    assert np.isnan(result[1])
    assert result[0] == pytest.approx(2.0)


def test_div_cli_subprocess(tmp_path: Path) -> None:
    a = tmp_path / "a.rsf"
    b = tmp_path / "b.rsf"
    out_file = tmp_path / "div_file.rsf"
    out_scalar = tmp_path / "div_scalar.rsf"
    _write(a, np.array([8.0, 10.0], dtype=np.float32))
    _write(b, np.array([2.0, 5.0], dtype=np.float32))

    result = _run_cli("div", [str(a), str(b), "out=" + str(out_file)], tmp_path)
    assert result.returncode == 0, result.stderr
    np.testing.assert_allclose(read_rsf(out_file).data, np.array([4.0, 2.0], dtype=np.float32))

    result = _run_cli("div", [str(a), "out=" + str(out_scalar), "scalar=2.0"], tmp_path)
    assert result.returncode == 0, result.stderr
    np.testing.assert_allclose(read_rsf(out_scalar).data, np.array([4.0, 5.0], dtype=np.float32))


def test_tpow_rsf_1d_2d_axes_header_and_nonpositive(tmp_path: Path) -> None:
    one_d = tmp_path / "one_d.rsf"
    out_one = tmp_path / "one_d_tpow.rsf"
    _write(one_d, np.ones(4, dtype=np.float32), header=_header(o1=1.0, d1=0.5))
    tpow_rsf(one_d, out_one, power=2.0, axis=1)
    np.testing.assert_allclose(read_rsf(out_one).data, np.array([1.0, 2.25, 4.0, 6.25], dtype=np.float32))

    two_d = tmp_path / "two_d.rsf"
    out_axis1 = tmp_path / "axis1.rsf"
    out_axis2 = tmp_path / "axis2.rsf"
    data = np.ones((2, 3), dtype=np.float32)
    _write(two_d, data, header=_header(o1=0.0, d1=1.0, o2=2.0, d2=1.0))
    tpow_rsf(two_d, out_axis1, power=1.0, axis=1)
    tpow_rsf(two_d, out_axis2, power=1.0, axis=2)
    np.testing.assert_allclose(read_rsf(out_axis1).data, np.array([[0, 1, 2], [0, 1, 2]], dtype=np.float32))
    np.testing.assert_allclose(read_rsf(out_axis2).data, np.array([[2, 2, 2], [3, 3, 3]], dtype=np.float32))

    out_power0 = tmp_path / "power0.rsf"
    tpow_rsf(two_d, out_power0, power=0.0, axis=1)
    np.testing.assert_allclose(read_rsf(out_power0).data, data)

    negative = tmp_path / "negative.rsf"
    out_negative = tmp_path / "negative_tpow.rsf"
    _write(negative, np.ones(3, dtype=np.float32), header=_header(o1=-1.0, d1=1.0))
    tpow_rsf(negative, out_negative, power=0.5, axis=1)
    np.testing.assert_allclose(read_rsf(out_negative).data, np.array([0.0, 0.0, np.sqrt(1.0)], dtype=np.float32))

    out_abs = tmp_path / "abs_tpow.rsf"
    tpow_rsf(negative, out_abs, power=0.5, axis=1, abs_time=True)
    np.testing.assert_allclose(read_rsf(out_abs).data, np.array([1.0, 0.0, 1.0], dtype=np.float32))


def test_tpow_cli_subprocess(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output = tmp_path / "tpow.rsf"
    _write(input_path, np.ones(3, dtype=np.float32), header=_header(o1=1.0, d1=1.0))

    result = _run_cli("tpow", [str(input_path), "out=" + str(output), "power=2.0", "axis=1"], tmp_path)
    assert result.returncode == 0, result.stderr
    np.testing.assert_allclose(read_rsf(output).data, np.array([1.0, 4.0, 9.0], dtype=np.float32))


def test_interleave_rsf_1d_2d_three_inputs_and_header(tmp_path: Path) -> None:
    a = tmp_path / "a.rsf"
    b = tmp_path / "b.rsf"
    c = tmp_path / "c.rsf"
    out_1d = tmp_path / "interleave_1d.rsf"
    _write(a, np.array([1, 2, 3], dtype=np.int32))
    _write(b, np.array([10, 20, 30], dtype=np.int32))
    _write(c, np.array([100, 200, 300], dtype=np.int32))
    interleave_rsf([a, b, c], out_1d, axis=1)
    np.testing.assert_array_equal(read_rsf(out_1d).data, np.array([1, 10, 100, 2, 20, 200, 3, 30, 300]))
    assert int(read_header(out_1d)["n1"]) == 9
    assert float(read_header(out_1d)["d1"]) == 0.5

    a2 = tmp_path / "a2.rsf"
    b2 = tmp_path / "b2.rsf"
    out_axis1 = tmp_path / "axis1.rsf"
    out_axis2 = tmp_path / "axis2.rsf"
    data_a = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.float32)
    data_b = np.array([[10, 20, 30], [40, 50, 60]], dtype=np.float32)
    _write(a2, data_a)
    _write(b2, data_b)
    interleave_rsf([a2, b2], out_axis1, axis=1)
    interleave_rsf([a2, b2], out_axis2, axis=2)
    np.testing.assert_allclose(
        read_rsf(out_axis1).data,
        np.array([[1, 10, 2, 20, 3, 30], [4, 40, 5, 50, 6, 60]], dtype=np.float32),
    )
    np.testing.assert_allclose(
        read_rsf(out_axis2).data,
        np.array([[1, 2, 3], [10, 20, 30], [4, 5, 6], [40, 50, 60]], dtype=np.float32),
    )
    assert int(read_header(out_axis2)["n2"]) == 4


def test_interleave_rsf_shape_mismatch_and_cli(tmp_path: Path) -> None:
    a = tmp_path / "a.rsf"
    b = tmp_path / "b.rsf"
    out = tmp_path / "out.rsf"
    _write(a, np.array([1, 2, 3], dtype=np.float32))
    _write(b, np.array([10, 20], dtype=np.float32))

    with pytest.raises(InterleaveError, match="shape mismatch"):
        interleave_rsf([a, b], out, axis=1)

    _write(b, np.array([10, 20, 30], dtype=np.float32))
    result = _run_cli("interleave", [str(a), str(b), "out=" + str(out), "axis=1"], tmp_path)
    assert result.returncode == 0, result.stderr
    np.testing.assert_allclose(read_rsf(out).data, np.array([1, 10, 2, 20, 3, 30], dtype=np.float32))


def test_original_sfmul_comparison_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfmul"):
        pytest.skip("Original Madagascar sfmul is not installed")

    a = tmp_path / "a.rsf"
    b = tmp_path / "b.rsf"
    original = tmp_path / "original.rsf"
    python = tmp_path / "python.rsf"
    _write(a, np.array([1.0, 2.0, 3.0], dtype=np.float32))
    _write(b, np.array([4.0, 5.0, 6.0], dtype=np.float32))

    run_original_madagascar(["sfmul", "in=a.rsf", "b.rsf", "out=original.rsf"], cwd=tmp_path, require_program="sfmul")
    multiply_rsf(a, b, python)
    assert_rsf_allclose(original, python, ignore_keys={"in"})


def test_original_sfdiv_comparison_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfdiv"):
        pytest.skip("Original Madagascar sfdiv is not installed")

    a = tmp_path / "a.rsf"
    b = tmp_path / "b.rsf"
    original = tmp_path / "original.rsf"
    python = tmp_path / "python.rsf"
    _write(a, np.array([8.0, 10.0], dtype=np.float32))
    _write(b, np.array([2.0, 5.0], dtype=np.float32))

    run_original_madagascar(["sfdiv", "in=a.rsf", "b.rsf", "out=original.rsf"], cwd=tmp_path, require_program="sfdiv")
    divide_rsf(a, b, python)
    assert_rsf_allclose(original, python, ignore_keys={"in"})


def test_original_sftpow_comparison_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sftpow"):
        pytest.skip("Original Madagascar sftpow is not installed")

    input_path = tmp_path / "input.rsf"
    original = tmp_path / "original.rsf"
    python = tmp_path / "python.rsf"
    _write(input_path, np.ones(3, dtype=np.float32), header=_header(o1=2.0, d1=0.0))

    run_original_madagascar(["sftpow", "in=input.rsf", "out=original.rsf", "tpow=2.0"], cwd=tmp_path, require_program="sftpow")
    tpow_rsf(input_path, python, power=2.0, axis=1)
    assert_rsf_allclose(
        original,
        python,
        ignore_keys={"in", "data_format", "esize"},
    )


def test_original_sfinterleave_comparison_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfinterleave"):
        pytest.skip("Original Madagascar sfinterleave is not installed")

    a = tmp_path / "a.rsf"
    b = tmp_path / "b.rsf"
    original = tmp_path / "original.rsf"
    python = tmp_path / "python.rsf"
    _write(a, np.array([1.0, 2.0, 3.0], dtype=np.float32))
    _write(b, np.array([10.0, 20.0, 30.0], dtype=np.float32))

    run_original_madagascar(
        ["sfinterleave", "in=a.rsf", "b.rsf", "out=original.rsf", "axis=1"],
        cwd=tmp_path,
        require_program="sfinterleave",
    )
    interleave_rsf([a, b], python, axis=1)
    assert_rsf_allclose(
        original,
        python,
        ignore_keys={"in", "o2", "d2", "label2", "unit2"},
    )
