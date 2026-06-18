from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys

import numpy as np
import pytest

from pymadagascar import RSFData
from pymadagascar.generic.statistics import (
    StatisticsError,
    fillnan,
    fillnan_rsf,
    finite_mask,
    isnan_mask,
    isnan_rsf,
    mean,
    mean_rsf,
    median,
    median_rsf,
    range_rsf,
    range_stats,
    rms,
    rms_rsf,
    std,
    std_rsf,
    var_rsf,
    variance,
)
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf
from pymadagascar.testing.runner import original_madagascar_available, run_original_madagascar


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


def _header_1d(n1: int) -> RSFHeader:
    return RSFHeader(
        {
            "n1": n1,
            "o1": 0.5,
            "d1": 0.25,
            "label1": "Time",
            "unit1": "s",
        }
    )


def _header_2d(n1: int, n2: int) -> RSFHeader:
    header = _header_1d(n1)
    header["n2"] = n2
    header["o2"] = 10.0
    header["d2"] = 2.0
    header["label2"] = "Trace"
    return header


def test_global_statistics_are_float64_single_sample_outputs() -> None:
    data = np.array([-2.0, 0.0, 2.0, 4.0], dtype=np.float32)

    np.testing.assert_allclose(mean(data), [1.0])
    np.testing.assert_allclose(rms(data), [np.sqrt(6.0)])
    np.testing.assert_allclose(variance(data), [5.0])
    np.testing.assert_allclose(std(data), [np.sqrt(5.0)])
    np.testing.assert_allclose(median(data), [1.0])
    np.testing.assert_allclose(range_stats(data), [-2.0, 4.0])
    for result in (
        mean(data),
        rms(data),
        variance(data),
        std(data),
        median(data),
        range_stats(data),
    ):
        assert result.dtype == np.float64


def test_axis_statistics_use_one_based_rsf_axes() -> None:
    data = np.arange(12, dtype=np.float32).reshape(3, 4)

    np.testing.assert_allclose(mean(data, axis=1), np.mean(data, axis=1))
    np.testing.assert_allclose(mean(data, axis=2), np.mean(data, axis=0))
    np.testing.assert_allclose(rms(data, axis=1), np.sqrt(np.mean(data**2, axis=1)))
    np.testing.assert_allclose(variance(data, axis=2, ddof=1), np.var(data, axis=0, ddof=1))
    np.testing.assert_allclose(std(data, axis=1), np.std(data, axis=1))
    np.testing.assert_allclose(median(data, axis=2), np.median(data, axis=0))
    np.testing.assert_allclose(
        range_stats(data, axis=1),
        np.stack((np.min(data, axis=1), np.max(data, axis=1)), axis=-1),
    )


def test_nan_policy_propagate_omit_and_raise() -> None:
    data = np.array([[1.0, np.nan], [3.0, 5.0]], dtype=np.float32)

    propagated = mean(data, axis=1)
    omitted = mean(data, axis=1, nan_policy="omit")
    assert np.isnan(propagated[0])
    np.testing.assert_allclose(omitted, [1.0, 4.0])
    np.testing.assert_allclose(median(data, nan_policy="omit"), [3.0])
    np.testing.assert_allclose(range_stats(data, nan_policy="omit"), [1.0, 5.0])
    with pytest.raises(StatisticsError, match="NaN"):
        rms(data, nan_policy="raise")


def test_complex_statistics_reject_but_masks_and_fill_support_complex() -> None:
    data = np.array([1.0 + 2.0j, np.nan + 0.0j, 3.0 + np.inf * 1j], dtype=np.complex64)

    for operation in (mean, rms, variance, std, median, range_stats):
        with pytest.raises(StatisticsError, match="complex"):
            operation(data)

    np.testing.assert_array_equal(isnan_mask(data), [False, True, True])
    np.testing.assert_array_equal(isnan_mask(data, "inf"), [False, False, True])
    filled = fillnan(data, 7.0, mode="nonfinite")
    assert filled.dtype == np.complex64
    np.testing.assert_array_equal(filled, np.array([1.0 + 2.0j, 7.0 + 0.0j, 7.0 + 0.0j]))


def test_isnan_modes_and_fillnan_dtype_contract() -> None:
    data = np.array([0.0, np.nan, np.inf, -np.inf, 4.0], dtype=np.float32)

    np.testing.assert_array_equal(isnan_mask(data, "nan"), [0, 1, 0, 0, 0])
    np.testing.assert_array_equal(isnan_mask(data, "inf"), [0, 0, 1, 1, 0])
    np.testing.assert_array_equal(isnan_mask(data, "nonfinite"), [0, 1, 1, 1, 0])
    np.testing.assert_array_equal(finite_mask(data), [1, 0, 0, 0, 1])
    nan_filled = fillnan(data, -1.0, mode="nan")
    all_filled = fillnan(data, 2.0, mode="nonfinite")
    assert nan_filled.dtype == np.float32
    np.testing.assert_array_equal(nan_filled, [0.0, -1.0, np.inf, -np.inf, 4.0])
    np.testing.assert_array_equal(all_filled, [0.0, 2.0, 2.0, 2.0, 4.0])


def test_stat_rsf_global_axis_and_header_contract(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    global_path = tmp_path / "mean.rsf"
    axis_path = tmp_path / "std_axis.rsf"
    data = np.arange(12, dtype=np.float32).reshape(3, 4)
    write_rsf(input_path, data, _header_2d(n1=4, n2=3))

    mean_rsf(input_path, global_path)
    std_rsf(input_path, axis_path, axis=1)

    global_result = read_rsf(global_path)
    axis_result = read_rsf(axis_path)
    assert global_result.data.shape == (1,)
    assert global_result.data.dtype == np.float64
    assert global_result.header["label1"] == "Mean"
    assert global_result.header["statistic_axis"] == "global"
    assert axis_result.data.shape == (3,)
    assert axis_result.header.dimensions == (3,)
    assert axis_result.header["label1"] == "Trace"
    assert axis_result.header["statistic_axis"] == "1"
    np.testing.assert_allclose(axis_result.data, np.std(data, axis=1))


def test_range_rsf_uses_explicit_field_axis_and_preserves_remaining_axes(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    global_path = tmp_path / "global_range.rsf"
    axis_path = tmp_path / "axis_range.rsf"
    data = np.arange(12, dtype=np.float32).reshape(3, 4)
    write_rsf(input_path, data, _header_2d(n1=4, n2=3))

    range_rsf(input_path, global_path)
    range_rsf(input_path, axis_path, axis=1)

    global_result = read_rsf(global_path)
    axis_result = read_rsf(axis_path)
    assert global_result.data.shape == (2,)
    assert global_result.header["range_fields"] == "min,max"
    assert axis_result.data.shape == (3, 2)
    assert axis_result.header.dimensions == (2, 3)
    assert axis_result.header["label1"] == "Range field"
    assert axis_result.header["label2"] == "Trace"


def test_mask_and_fill_rsf_preserve_shape_header_and_expected_dtype(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    mask_path = tmp_path / "mask.rsf"
    filled_path = tmp_path / "filled.rsf"
    data = np.array([[1.0, np.nan], [np.inf, 4.0]], dtype=np.float32)
    write_rsf(input_path, data, _header_2d(n1=2, n2=2))

    isnan_rsf(input_path, mask_path, mode="nonfinite")
    fillnan_rsf(input_path, filled_path, mode="nonfinite", value=-2.0)

    mask = read_rsf(mask_path)
    filled = read_rsf(filled_path)
    assert mask.data.dtype == np.int32
    assert mask.data.shape == data.shape
    assert mask.header["label1"] == "Time"
    assert mask.header["mask_mode"] == "nonfinite"
    assert filled.data.dtype == np.float32
    assert filled.header["label2"] == "Trace"
    np.testing.assert_array_equal(filled.data, [[1.0, -2.0], [-2.0, 4.0]])


@pytest.mark.parametrize(
    ("module", "expected"),
    [
        ("mean", [2.5]),
        ("rms", [np.sqrt(7.5)]),
        ("var", [1.25]),
        ("std", [np.sqrt(1.25)]),
        ("median", [2.5]),
        ("range", [1.0, 4.0]),
    ],
)
def test_statistics_cli_subprocess(
    module: str,
    expected: list[float],
    tmp_path: Path,
) -> None:
    input_path = tmp_path / f"{module}_input.rsf"
    output_path = tmp_path / f"{module}_output.rsf"
    write_rsf(input_path, np.arange(1, 5, dtype=np.float32), _header_1d(4))

    result = _run_cli(
        module,
        [str(input_path), "out=" + str(output_path), "nan_policy=omit"],
        tmp_path,
    )

    assert result.returncode == 0, result.stderr
    np.testing.assert_allclose(read_rsf(output_path).data, expected)


def test_isnan_and_fillnan_cli_subprocess(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    mask_path = tmp_path / "mask.rsf"
    filled_path = tmp_path / "filled.rsf"
    write_rsf(
        input_path,
        np.array([1.0, np.nan, np.inf], dtype=np.float32),
        _header_1d(3),
    )

    mask_result = _run_cli(
        "isnan",
        [str(input_path), "out=" + str(mask_path), "mode=nonfinite"],
        tmp_path,
    )
    fill_result = _run_cli(
        "fillnan",
        [str(input_path), "out=" + str(filled_path), "mode=nonfinite", "value=-3"],
        tmp_path,
    )

    assert mask_result.returncode == 0, mask_result.stderr
    assert fill_result.returncode == 0, fill_result.stderr
    np.testing.assert_array_equal(read_rsf(mask_path).data, [0, 1, 1])
    np.testing.assert_array_equal(read_rsf(filled_path).data, [1.0, -3.0, -3.0])


def test_rsfdata_statistics_nan_methods_and_inplace_contract() -> None:
    data = np.array([[1.0, np.nan, 3.0], [4.0, 5.0, np.inf]], dtype=np.float32)
    source = RSFData(data, _header_2d(n1=3, n2=2))

    cleaned = source.fillnan(0.0, mode="nonfinite")
    means = cleaned.mean(axis=1)
    ranges = cleaned.range_stats(axis=1)
    mask = source.isnan(mode="nonfinite")

    assert cleaned is not source
    assert means.shape == (2,)
    assert ranges.shape == (2, 2)
    assert mask.dtype == np.int32
    np.testing.assert_array_equal(mask.numpy(), [[0, 1, 0], [0, 0, 1]])
    returned = source.fillnan(-1.0, mode="nonfinite", inplace=True)
    assert returned is source
    np.testing.assert_array_equal(source.numpy(), [[1.0, -1.0, 3.0], [4.0, 5.0, -1.0]])


def test_invalid_parameters_raise_clear_errors() -> None:
    with pytest.raises(StatisticsError, match="axis"):
        mean(np.ones(3), axis=2)
    with pytest.raises(StatisticsError, match="ddof"):
        variance(np.ones(3), ddof=-1)
    with pytest.raises(StatisticsError, match="nan_policy"):
        median(np.ones(3), nan_policy="ignore")
    with pytest.raises(StatisticsError, match="mode"):
        isnan_mask(np.ones(3), mode="bad")
    with pytest.raises(StatisticsError, match="mode"):
        fillnan(np.ones(3), mode="finite")


@pytest.mark.parametrize(
    ("want", "operation"),
    [
        ("mean", lambda data: mean(data)[0]),
        ("rms", lambda data: rms(data)[0]),
        ("var", lambda data: variance(data, ddof=1)[0]),
        ("std", lambda data: std(data, ddof=1)[0]),
    ],
)
@pytest.mark.original_madagascar
def test_original_sfattr_global_comparison_when_available(
    want: str,
    operation: object,
    tmp_path: Path,
) -> None:
    if not original_madagascar_available("sfattr"):
        pytest.skip("Original Madagascar sfattr is not installed")

    input_path = tmp_path / "input.rsf"
    data = np.array([-2.0, 0.0, 2.0, 4.0], dtype=np.float32)
    write_rsf(input_path, data, _header_1d(data.size))
    result = run_original_madagascar(
        ["sfattr", f"want={want}"],
        cwd=tmp_path,
        require_program="sfattr",
        stdin_path=input_path,
        decode_stdout=True,
    )
    match = re.search(r"=\s*([-+0-9.eE]+)", result.stdout)
    assert match is not None
    expected = operation(data)  # type: ignore[operator]
    assert float(match.group(1)) == pytest.approx(float(expected), rel=1e-5)


@pytest.mark.original_madagascar
def test_original_sfmedian_axis1_comparison_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfmedian"):
        pytest.skip("Original Madagascar sfmedian is not installed")

    input_path = tmp_path / "input.rsf"
    original_path = tmp_path / "original.rsf"
    python_path = tmp_path / "python.rsf"
    data = np.array([[1.0, 4.0, 2.0], [9.0, 5.0, 7.0]], dtype=np.float32)
    write_rsf(input_path, data, _header_2d(n1=3, n2=2))
    run_original_madagascar(
        ["sfmedian", "in=input.rsf", "out=original.rsf"],
        cwd=tmp_path,
        require_program="sfmedian",
    )
    median_rsf(input_path, python_path, axis=1)

    np.testing.assert_allclose(
        read_rsf(python_path).data.ravel(),
        read_rsf(original_path).data.ravel(),
        rtol=1e-6,
        atol=1e-6,
    )
