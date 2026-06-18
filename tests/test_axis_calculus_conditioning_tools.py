from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys

import numpy as np
import pytest

from pymadagascar import RSFData
from pymadagascar.generic.difference import DifferenceError, diff_rsf, difference_metric
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf
from pymadagascar.seismic.mute import MuteError, mutter, mutter_rsf
from pymadagascar.signal.calculus import (
    CalculusError,
    causal_integrate,
    causint_rsf,
    deriv,
    deriv_rsf,
    integral,
    integral_rsf,
)
from pymadagascar.signal.conditioning import ConditioningError, clip2, clip2_rsf
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


def _header_1d(n1: int, *, o1: float = 0.0, d1: float = 1.0) -> RSFHeader:
    return RSFHeader({"n1": n1, "o1": o1, "d1": d1, "label1": "Time", "unit1": "s"})


def _header_2d(
    n1: int,
    n2: int,
    *,
    o1: float = 0.0,
    d1: float = 1.0,
    o2: float = 0.0,
    d2: float = 1.0,
) -> RSFHeader:
    header = _header_1d(n1, o1=o1, d1=d1)
    header["n2"] = n2
    header["o2"] = o2
    header["d2"] = d2
    header["label2"] = "Offset"
    header["unit2"] = "m"
    return header


def test_deriv_linear_constant_methods_and_scale() -> None:
    x = np.arange(5, dtype=np.float32) * 0.5
    linear = 3.0 * x + 2.0

    for method in ("central", "forward", "backward"):
        np.testing.assert_allclose(
            deriv(linear, method=method, d=0.5),
            np.full(5, 3.0, dtype=np.float32),
        )
    np.testing.assert_allclose(deriv(np.ones(5, dtype=np.float32)), 0.0)
    np.testing.assert_allclose(deriv(linear, scale_by_d=False), 1.5)

    panel = np.repeat(np.array([[0.0], [2.0], [4.0]], dtype=np.float32), 4, axis=1)
    np.testing.assert_allclose(deriv(panel, axis=2, d=2.0), 1.0)


def test_deriv_rsf_header_and_cli(tmp_path: Path) -> None:
    input_path = tmp_path / "linear.rsf"
    api_path = tmp_path / "deriv_api.rsf"
    cli_path = tmp_path / "deriv_cli.rsf"
    data = (2.0 * np.arange(5, dtype=np.float32) * 0.25 + 1.0).astype(np.float32)
    write_rsf(input_path, data, _header_1d(5, d1=0.25))

    deriv_rsf(input_path, api_path)
    result = _run_cli(
        "deriv",
        [str(input_path), "out=" + str(cli_path), "axis=1", "method=forward", "scale_by_d=y"],
        tmp_path,
    )

    assert result.returncode == 0, result.stderr
    np.testing.assert_allclose(read_rsf(api_path).data, 2.0)
    np.testing.assert_allclose(read_rsf(cli_path).data, 2.0)
    assert read_rsf(cli_path).header["label1"] == "Time"


def test_causint_api_axis_scale_header_and_cli(tmp_path: Path) -> None:
    ones = np.ones(4, dtype=np.float32)
    np.testing.assert_allclose(causal_integrate(ones), [1.0, 2.0, 3.0, 4.0])
    np.testing.assert_allclose(
        causal_integrate(ones, d=0.5, scale_by_d=True),
        [0.5, 1.0, 1.5, 2.0],
    )
    panel = np.ones((3, 4), dtype=np.float32)
    np.testing.assert_allclose(
        causal_integrate(panel, axis=2),
        np.array([[1.0] * 4, [2.0] * 4, [3.0] * 4], dtype=np.float32),
    )

    input_path = tmp_path / "ones.rsf"
    api_path = tmp_path / "causint_api.rsf"
    cli_path = tmp_path / "causint_cli.rsf"
    write_rsf(input_path, ones, _header_1d(4, d1=0.5))
    causint_rsf(input_path, api_path, scale_by_d=True)
    result = _run_cli(
        "causint",
        [str(input_path), "out=" + str(cli_path), "scale_by_d=y"],
        tmp_path,
    )

    assert result.returncode == 0, result.stderr
    np.testing.assert_allclose(read_rsf(api_path).data, [0.5, 1.0, 1.5, 2.0])
    np.testing.assert_allclose(read_rsf(cli_path).data, read_rsf(api_path).data)
    assert read_rsf(api_path).header["d1"] == "0.5"


def test_integral_cumsum_trapezoid_axis_and_cli(tmp_path: Path) -> None:
    linear = np.arange(4, dtype=np.float32)
    np.testing.assert_allclose(
        integral(linear, method="trapezoid", d=1.0),
        [0.0, 0.5, 2.0, 4.5],
    )
    np.testing.assert_allclose(
        integral(np.ones(4, dtype=np.float32), method="cumsum", d=0.25),
        [0.25, 0.5, 0.75, 1.0],
    )
    panel = np.repeat(linear.reshape(-1, 1), 2, axis=1)
    assert integral(panel, axis=2, method="trapezoid").shape == panel.shape

    input_path = tmp_path / "linear.rsf"
    api_path = tmp_path / "integral_api.rsf"
    cli_path = tmp_path / "integral_cli.rsf"
    write_rsf(input_path, linear, _header_1d(4, d1=1.0))
    integral_rsf(input_path, api_path, method="trapezoid")
    result = _run_cli(
        "integral",
        [str(input_path), "out=" + str(cli_path), "method=cumsum", "scale_by_d=n"],
        tmp_path,
    )

    assert result.returncode == 0, result.stderr
    np.testing.assert_allclose(read_rsf(api_path).data, [0.0, 0.5, 2.0, 4.5])
    np.testing.assert_allclose(read_rsf(cli_path).data, [0.0, 1.0, 3.0, 6.0])


def test_clip2_explicit_percentile_symmetric_header_and_cli(tmp_path: Path) -> None:
    data = np.array([-10.0, -2.0, 0.0, 2.0, 10.0], dtype=np.float32)
    np.testing.assert_allclose(
        clip2(data, min_value=-1.0, max_value=3.0),
        [-1.0, -1.0, 0.0, 2.0, 3.0],
    )
    limit = float(np.percentile(np.abs(data), 60.0))
    np.testing.assert_allclose(
        clip2(data, pclip=60.0, symmetric=True),
        np.clip(data, -limit, limit),
    )

    input_path = tmp_path / "amplitude.rsf"
    api_path = tmp_path / "clip2_api.rsf"
    cli_path = tmp_path / "clip2_cli.rsf"
    write_rsf(input_path, data, _header_1d(data.size))
    clip2_rsf(input_path, api_path, min_value=-1.0, max_value=1.0)
    result = _run_cli(
        "clip2",
        [str(input_path), "out=" + str(cli_path), "pclip=60", "symmetric=y"],
        tmp_path,
    )

    assert result.returncode == 0, result.stderr
    np.testing.assert_allclose(read_rsf(api_path).data, np.clip(data, -1.0, 1.0))
    np.testing.assert_allclose(read_rsf(cli_path).data, np.clip(data, -limit, limit))
    assert read_rsf(cli_path).header["label1"] == "Time"


def test_mutter_above_below_taper_header_and_cli(tmp_path: Path) -> None:
    gather = np.ones((2, 5), dtype=np.float32)
    above = mutter(gather, v=1.0, time_d=1.0, offset_d=1.0, side="above")
    below = mutter(gather, v=1.0, time_d=1.0, offset_d=1.0, side="below")
    tapered = mutter(gather, v=1.0, time_d=1.0, offset_d=1.0, side="above", taper=2)

    np.testing.assert_allclose(above, [[1, 1, 1, 1, 1], [0, 1, 1, 1, 1]])
    np.testing.assert_allclose(below, [[1, 0, 0, 0, 0], [1, 1, 0, 0, 0]])
    np.testing.assert_allclose(tapered[0], [0.0, 0.5, 1.0, 1.0, 1.0], atol=1e-6)

    input_path = tmp_path / "gather.rsf"
    api_path = tmp_path / "mutter_api.rsf"
    cli_path = tmp_path / "mutter_cli.rsf"
    write_rsf(input_path, gather, _header_2d(5, 2))
    mutter_rsf(input_path, api_path, v=1.0, side="above")
    result = _run_cli(
        "mutter",
        [str(input_path), "out=" + str(cli_path), "v=1", "side=below", "taper=0"],
        tmp_path,
    )

    assert result.returncode == 0, result.stderr
    np.testing.assert_allclose(read_rsf(api_path).data, above)
    np.testing.assert_allclose(read_rsf(cli_path).data, below)
    assert read_rsf(cli_path).header.dimensions == (5, 2)


def test_difference_metrics_rsf_and_cli(tmp_path: Path) -> None:
    left = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    right = np.array([1.0, 4.0, 0.0], dtype=np.float32)
    np.testing.assert_allclose(difference_metric(left, right), 13.0)
    np.testing.assert_allclose(difference_metric(left, right, metric="rms"), np.sqrt(13.0 / 3.0))
    np.testing.assert_allclose(difference_metric(left, right, metric="max_abs"), 3.0)

    left_path = tmp_path / "left.rsf"
    right_path = tmp_path / "right.rsf"
    api_path = tmp_path / "diff_api.rsf"
    cli_path = tmp_path / "diff_cli.rsf"
    write_rsf(left_path, left, _header_1d(3))
    write_rsf(right_path, right, _header_1d(3))
    diff_rsf(left_path, right_path, api_path)
    result = _run_cli(
        "diff",
        [str(left_path), str(right_path), "out=" + str(cli_path), "metric=max_abs"],
        tmp_path,
    )

    assert result.returncode == 0, result.stderr
    np.testing.assert_allclose(read_rsf(api_path).data, [13.0])
    np.testing.assert_allclose(read_rsf(cli_path).data, [3.0])
    assert read_rsf(api_path).header["difference_metric"] == "sum_square"


def test_rsfdata_stage_c4_methods_are_non_mutating() -> None:
    trace = np.arange(5, dtype=np.float32)
    rsf = RSFData(trace, _header_1d(5, d1=0.5))
    gather = RSFData(np.ones((2, 5), dtype=np.float32), _header_2d(5, 2))

    derivative = rsf.deriv()
    causal = rsf.causint(scale_by_d=True)
    integrated = rsf.integral()
    clipped = rsf.clip2(max_value=2.0)
    muted = gather.mutter(v=1.0, side="above")
    difference = rsf.diff(rsf.clip2(max_value=2.0), metric="sum_square")

    np.testing.assert_allclose(rsf.numpy(), trace)
    np.testing.assert_allclose(derivative.numpy(), 2.0)
    np.testing.assert_allclose(causal.numpy(), np.cumsum(trace) * 0.5)
    assert integrated.shape == rsf.shape
    np.testing.assert_allclose(clipped.numpy(), np.minimum(trace, 2.0))
    assert muted.shape == gather.shape
    np.testing.assert_allclose(difference.numpy(), [5.0])


def test_invalid_parameters_raise_clear_errors() -> None:
    with pytest.raises(CalculusError, match="method"):
        deriv(np.ones(4), method="high_order")
    with pytest.raises(CalculusError, match="nonzero"):
        integral(np.ones(4), d=0.0)
    with pytest.raises(ConditioningError, match="real-valued"):
        clip2(np.ones(4, dtype=np.complex64), max_value=1.0)
    with pytest.raises(ConditioningError, match="cannot be combined"):
        clip2(np.ones(4), max_value=1.0, pclip=99)
    with pytest.raises(MuteError, match="positive"):
        mutter(np.ones((2, 4)), v=0.0)
    with pytest.raises(DifferenceError, match="shape mismatch"):
        difference_metric(np.ones(3), np.ones(4))


@pytest.mark.original_madagascar
def test_original_sfcausint_comparison_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfcausint"):
        pytest.skip("Original Madagascar sfcausint is not installed")

    input_path = tmp_path / "input.rsf"
    original_path = tmp_path / "original.rsf"
    python_path = tmp_path / "python.rsf"
    write_rsf(input_path, np.arange(5, dtype=np.float32), _header_1d(5))
    run_original_madagascar(
        ["sfcausint", "in=input.rsf", "out=original.rsf"],
        cwd=tmp_path,
        require_program="sfcausint",
    )
    causint_rsf(input_path, python_path)
    np.testing.assert_allclose(read_rsf(original_path).data, read_rsf(python_path).data)


@pytest.mark.original_madagascar
def test_original_sfclip2_comparison_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfclip2"):
        pytest.skip("Original Madagascar sfclip2 is not installed")

    input_path = tmp_path / "input.rsf"
    original_path = tmp_path / "original.rsf"
    python_path = tmp_path / "python.rsf"
    write_rsf(input_path, np.array([-2.0, -0.5, 1.0, 3.0], dtype=np.float32), _header_1d(4))
    run_original_madagascar(
        ["sfclip2", "in=input.rsf", "out=original.rsf", "lower=-1", "upper=2"],
        cwd=tmp_path,
        require_program="sfclip2",
    )
    clip2_rsf(input_path, python_path, min_value=-1.0, max_value=2.0)
    np.testing.assert_allclose(read_rsf(original_path).data, read_rsf(python_path).data)


@pytest.mark.parametrize("program", ["sfderiv", "sfintegral", "sfmutter", "sfdiff"])
@pytest.mark.original_madagascar
def test_original_stage_c4_partial_commands_are_optional(program: str) -> None:
    if not original_madagascar_available(program):
        pytest.skip(f"Original Madagascar {program} is not installed")
    pytest.skip(
        f"Original {program} is not directly compared because the Stage C-4 "
        "implementation intentionally uses a smaller Pythonic parameter surface"
    )
