from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from pymadagascar import RSFData
from pymadagascar.generic.unary import (
    UnaryMathError,
    abs_rsf,
    absolute,
    exp,
    histogram,
    histogram_rsf,
    log,
    power,
    quantile,
    quantile_rsf,
    sign,
    sqrt,
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
            "label1": "Sample",
            "unit1": "unit",
        }
    )


def _header_2d(n1: int, n2: int) -> RSFHeader:
    header = _header_1d(n1)
    header["n2"] = n2
    header["o2"] = 10.0
    header["d2"] = 2.0
    header["label2"] = "Trace"
    return header


def test_unary_array_apis_and_real_dtype_contract() -> None:
    data = np.array([-4.0, -1.0, 0.0, 1.0, 4.0], dtype=np.float32)

    np.testing.assert_array_equal(absolute(data), np.abs(data))
    np.testing.assert_array_equal(sign(data), np.array([-1, -1, 0, 1, 1], dtype=np.float32))
    np.testing.assert_allclose(sqrt(np.abs(data)), np.sqrt(np.abs(data)))
    np.testing.assert_allclose(log(np.array([1.0, 10.0], dtype=np.float32), base=10), [0.0, 1.0])
    np.testing.assert_allclose(exp(np.array([0.0, 1.0], dtype=np.float32)), [1.0, np.e])
    np.testing.assert_allclose(power(data, 2.0), data * data)

    assert absolute(data).dtype == np.float32
    assert power(data.astype(np.float64), 2.0).dtype == np.float64


def test_sqrt_log_invalid_nan_raise_and_inf_behavior() -> None:
    roots = sqrt(np.array([-1.0, np.nan, np.inf], dtype=np.float32))
    logs = log(np.array([-1.0, 0.0, np.nan, np.inf], dtype=np.float32))

    assert np.isnan(roots[0])
    assert np.isnan(roots[1])
    assert np.isposinf(roots[2])
    assert np.isnan(logs[0])
    assert np.isneginf(logs[1])
    assert np.isnan(logs[2])
    assert np.isposinf(logs[3])
    with pytest.raises(UnaryMathError, match="negative"):
        sqrt(np.array([-1.0]), invalid="raise")
    with pytest.raises(UnaryMathError, match="negative"):
        log(np.array([-1.0]), invalid="raise")


def test_complex_behavior_is_explicit() -> None:
    data = np.array([3.0 + 4.0j, 0.0 + 0.0j], dtype=np.complex64)

    result = absolute(data)
    np.testing.assert_array_equal(result, np.array([5.0, 0.0], dtype=np.float32))
    assert result.dtype == np.float32
    for operation in (sign, sqrt, log, exp):
        with pytest.raises(UnaryMathError, match="complex"):
            operation(data)
    with pytest.raises(UnaryMathError, match="complex"):
        power(data, 2.0)


def test_unary_rsf_preserves_shape_header_and_abs_changes_complex_dtype(tmp_path: Path) -> None:
    input_path = tmp_path / "complex.rsf"
    output_path = tmp_path / "abs.rsf"
    data = np.array([[3.0 + 4.0j, 0.0], [0.0, 5.0 + 12.0j]], dtype=np.complex64)
    write_rsf(input_path, data, _header_2d(n1=2, n2=2))

    abs_rsf(input_path, output_path)
    loaded = read_rsf(output_path)

    assert loaded.data.shape == data.shape
    assert loaded.data.dtype == np.float32
    assert loaded.header["label1"] == "Sample"
    assert loaded.header["label2"] == "Trace"
    np.testing.assert_allclose(loaded.data, np.array([[5.0, 0.0], [0.0, 13.0]], dtype=np.float32))


@pytest.mark.parametrize(
    ("module", "data", "extra", "expected"),
    [
        ("abs", [-2.0, 0.0, 3.0], [], [2.0, 0.0, 3.0]),
        ("sign", [-2.0, 0.0, 3.0], [], [-1.0, 0.0, 1.0]),
        ("sqrt", [0.0, 1.0, 4.0], ["invalid=raise"], [0.0, 1.0, 2.0]),
        ("log", [1.0, 10.0, 100.0], ["base=10"], [0.0, 1.0, 2.0]),
        ("exp", [0.0, 1.0, 2.0], [], [1.0, np.e, np.e**2]),
        ("pow", [-2.0, 0.0, 3.0], ["exponent=2"], [4.0, 0.0, 9.0]),
    ],
)
def test_unary_cli_subprocess(
    module: str,
    data: list[float],
    extra: list[str],
    expected: list[float],
    tmp_path: Path,
) -> None:
    input_path = tmp_path / f"{module}_input.rsf"
    output_path = tmp_path / f"{module}_output.rsf"
    write_rsf(input_path, np.asarray(data, dtype=np.float32), _header_1d(len(data)))

    result = _run_cli(module, [str(input_path), "out=" + str(output_path), *extra], tmp_path)

    assert result.returncode == 0, result.stderr
    np.testing.assert_allclose(read_rsf(output_path).data, expected, rtol=1e-6, atol=1e-6)


def test_histogram_api_counts_density_and_nonfinite_omission() -> None:
    data = np.array([0.25, 0.75, 1.25, 2.25, np.nan, np.inf], dtype=np.float32)
    counts = histogram(data, bins=3, range=(0.0, 3.0))
    density = histogram(data, bins=3, range=(0.0, 3.0), density=True)

    np.testing.assert_allclose(counts[:, 0], [0.5, 1.5, 2.5])
    np.testing.assert_array_equal(counts[:, 1], [2.0, 1.0, 1.0])
    assert counts.dtype == np.float64
    np.testing.assert_allclose(np.sum(density[:, 1]), 1.0)


def test_histogram_rsf_header_and_cli(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    api_path = tmp_path / "hist_api.rsf"
    cli_path = tmp_path / "hist_cli.rsf"
    data = np.array([0.25, 0.75, 1.25, 2.25], dtype=np.float32)
    write_rsf(input_path, data, _header_1d(data.size))

    histogram_rsf(input_path, api_path, bins=3, min_value=0.0, max_value=3.0)
    result = _run_cli(
        "histogram",
        [str(input_path), "out=" + str(cli_path), "bins=3", "min=0", "max=3"],
        tmp_path,
    )

    assert result.returncode == 0, result.stderr
    loaded = read_rsf(api_path)
    assert loaded.data.shape == (3, 2)
    assert loaded.header.dimensions == (2, 3)
    assert loaded.header["histogram_fields"] == "center,value"
    assert loaded.header["histogram_value"] == "count"
    np.testing.assert_allclose(read_rsf(cli_path).data, loaded.data)


def test_quantile_global_axis_and_nan_policy() -> None:
    data = np.arange(12, dtype=np.float32).reshape(3, 4)
    global_result = quantile(data, [0.0, 0.5, 1.0])
    axis_result = quantile(data, [0.25, 0.75], axis=1)

    np.testing.assert_allclose(global_result, [0.0, 5.5, 11.0])
    assert global_result.shape == (3,)
    assert axis_result.shape == (3, 2)
    np.testing.assert_allclose(axis_result, np.quantile(data, [0.25, 0.75], axis=1).T)
    assert np.isnan(quantile(np.array([1.0, np.nan]), 0.5)[0])
    np.testing.assert_allclose(quantile(np.array([1.0, np.nan]), 0.5, nan_policy="omit"), [1.0])


def test_quantile_rsf_shape_header_and_cli(tmp_path: Path) -> None:
    input_path = tmp_path / "panel.rsf"
    global_path = tmp_path / "q_global.rsf"
    axis_path = tmp_path / "q_axis.rsf"
    cli_path = tmp_path / "q_cli.rsf"
    data = np.arange(12, dtype=np.float32).reshape(3, 4)
    write_rsf(input_path, data, _header_2d(n1=4, n2=3))

    quantile_rsf(input_path, global_path, q=[0.25, 0.5, 0.75])
    quantile_rsf(input_path, axis_path, q=[0.25, 0.75], axis=1)
    result = _run_cli(
        "quantile",
        [str(input_path), "out=" + str(cli_path), "q=0.25,0.75", "axis=1"],
        tmp_path,
    )

    assert result.returncode == 0, result.stderr
    global_loaded = read_rsf(global_path)
    axis_loaded = read_rsf(axis_path)
    assert global_loaded.data.shape == (3,)
    assert global_loaded.header["quantiles"] == "0.25,0.5,0.75"
    assert axis_loaded.data.shape == (3, 2)
    assert axis_loaded.header.dimensions == (2, 3)
    assert axis_loaded.header["label1"] == "Quantile"
    assert axis_loaded.header["label2"] == "Trace"
    assert axis_loaded.header["quantile_axis"] == "1"
    np.testing.assert_allclose(read_rsf(cli_path).data, axis_loaded.data)


def test_rsfdata_unary_distribution_methods_and_inplace_contract() -> None:
    source = RSFData(np.array([-4.0, -1.0, 0.0, 1.0, 4.0], dtype=np.float32), _header_1d(5))

    positive = source.abs()
    chain = positive.sqrt().pow(2.0).log(invalid="raise").exp()
    signs = source.sign()
    hist = source.histogram(bins=4, min_value=-4.0, max_value=4.0)
    qs = source.quantile([0.25, 0.5, 0.75])

    np.testing.assert_array_equal(source.numpy(), [-4.0, -1.0, 0.0, 1.0, 4.0])
    np.testing.assert_allclose(chain.numpy(), positive.numpy())
    np.testing.assert_array_equal(signs.numpy(), [-1.0, -1.0, 0.0, 1.0, 1.0])
    assert hist.shape == (4, 2)
    assert qs.shape == (3,)
    returned = positive.sqrt(inplace=True)
    assert returned is positive
    np.testing.assert_allclose(positive.numpy(), [2.0, 1.0, 0.0, 1.0, 2.0])


def test_invalid_parameters_raise_clear_errors() -> None:
    with pytest.raises(UnaryMathError, match="bins"):
        histogram(np.ones(4), bins=0)
    with pytest.raises(UnaryMathError, match="between 0 and 1"):
        quantile(np.ones(4), 1.5)
    with pytest.raises(UnaryMathError, match="axis"):
        quantile(np.ones(4), 0.5, axis=2)
    with pytest.raises(UnaryMathError, match="base"):
        log(np.ones(4), base=1)
    with pytest.raises(UnaryMathError, match="finite"):
        histogram(np.array([np.nan, np.inf]))


@pytest.mark.parametrize(
    ("name", "expression", "data"),
    [
        ("abs", "abs(input)", [-2.0, 0.5, 3.0]),
        ("sign", "sign(input)", [-2.0, 0.5, 3.0]),
        ("sqrt", "sqrt(input)", [0.25, 1.0, 4.0]),
        ("log", "log(input)", [0.25, 1.0, 4.0]),
        ("exp", "exp(input)", [0.25, 1.0, 2.0]),
        ("pow", "input^2", [-2.0, 0.5, 3.0]),
    ],
)
@pytest.mark.original_madagascar
def test_original_sfmath_unary_comparison_when_available(
    name: str,
    expression: str,
    data: list[float],
    tmp_path: Path,
) -> None:
    if not original_madagascar_available("sfmath"):
        pytest.skip("Original Madagascar sfmath is not installed")

    input_path = tmp_path / "input.rsf"
    original_path = tmp_path / "original.rsf"
    python_path = tmp_path / "python.rsf"
    write_rsf(input_path, np.asarray(data, dtype=np.float32), _header_1d(len(data)))
    run_original_madagascar(
        ["sfmath", "in=input.rsf", "out=original.rsf", f"output={expression}"],
        cwd=tmp_path,
        require_program="sfmath",
    )
    args = [str(input_path), "out=" + str(python_path)]
    if name == "pow":
        args.append("exponent=2")
    result = _run_cli(name, args, tmp_path)

    assert result.returncode == 0, result.stderr
    np.testing.assert_allclose(
        read_rsf(python_path).data,
        read_rsf(original_path).data,
        rtol=1e-5,
        atol=1e-6,
    )


@pytest.mark.original_madagascar
def test_original_sfhistogram_count_comparison_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfhistogram"):
        pytest.skip("Original Madagascar sfhistogram is not installed")

    input_path = tmp_path / "input.rsf"
    original_path = tmp_path / "original.rsf"
    python_path = tmp_path / "python.rsf"
    data = np.array([0.25, 0.75, 1.25, 2.25], dtype=np.float32)
    write_rsf(input_path, data, _header_1d(data.size))
    run_original_madagascar(
        [
            "sfhistogram",
            "in=input.rsf",
            "out=original.rsf",
            "n1=3",
            "o1=0",
            "d1=1",
        ],
        cwd=tmp_path,
        require_program="sfhistogram",
    )
    histogram_rsf(input_path, python_path, bins=3, min_value=0.0, max_value=3.0)

    np.testing.assert_array_equal(
        read_rsf(python_path).data[:, 1],
        read_rsf(original_path).data,
    )


@pytest.mark.original_madagascar
def test_original_sfquantile_scalar_comparison_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfquantile"):
        pytest.skip("Original Madagascar sfquantile is not installed")

    input_path = tmp_path / "input.rsf"
    # Upstream sfquantile selects an order statistic while NumPy's default
    # quantile interpolates. A center plateau exercises their shared subset.
    data = np.array([0.0, 1.0, 2.0, 2.0, 4.0], dtype=np.float32)
    write_rsf(input_path, data, _header_1d(data.size))
    result = run_original_madagascar(
        ["sfquantile", "pclip=50"],
        cwd=tmp_path,
        require_program="sfquantile",
        stdin_path=input_path,
        decode_stdout=True,
    )

    assert float(result.stdout.strip()) == pytest.approx(float(quantile(data, 0.5)[0]))
