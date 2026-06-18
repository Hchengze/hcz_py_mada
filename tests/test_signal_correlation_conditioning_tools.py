from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys

import numpy as np
import pytest

from pymadagascar import RSFData
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf
from pymadagascar.seismic.stack import StackError, stack_along_axis, stacks_rsf
from pymadagascar.signal.conditioning import ConditioningError, shift, shifts_rsf
from pymadagascar.signal.convolution import (
    ConvolutionError,
    autocorr,
    autocorr_rsf,
    cconv_rsf,
    circular_convolve,
    convolve,
    convolve_rsf,
    envcorr_rsf,
    envelope_correlation,
)
from pymadagascar.signal.preprocessing import envelope
from pymadagascar.testing.runner import original_madagascar_available


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


def _header_2d(n1: int, n2: int, *, d1: float = 1.0) -> RSFHeader:
    header = _header_1d(n1, d1=d1)
    header["n2"] = n2
    header["o2"] = 0.0
    header["d2"] = 1.0
    header["label2"] = "Trace"
    return header


def test_autocorr_symmetry_delta_normalize_and_max_lag(tmp_path: Path) -> None:
    data = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    delta = np.array([0.0, 1.0, 0.0], dtype=np.float32)

    full = autocorr(data, mode="full")
    normalized = autocorr(data, mode="full", normalize=True)
    limited = autocorr(data, mode="full", max_lag=1)

    np.testing.assert_allclose(full, np.correlate(data, data, mode="full"))
    np.testing.assert_allclose(full, full[::-1])
    np.testing.assert_allclose(autocorr(delta), np.array([0.0, 0.0, 1.0, 0.0, 0.0], dtype=np.float32))
    np.testing.assert_allclose(normalized[2], 1.0)
    np.testing.assert_allclose(limited, np.array([8.0, 14.0, 8.0], dtype=np.float32))

    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "autocorr.rsf"
    write_rsf(input_path, data, _header_1d(3, d1=0.5))
    autocorr_rsf(input_path, output_path, max_lag=1)
    loaded = read_rsf(output_path)
    assert loaded.header.dimensions == (3,)
    assert loaded.header["o1"] == "-0.5"
    assert loaded.header["label1"] == "Lag"


def test_autocorr_2d_axis_and_cli(tmp_path: Path) -> None:
    panel = np.array([[1.0, 0.0, 2.0], [0.0, 1.0, 0.0]], dtype=np.float32)
    input_path = tmp_path / "panel.rsf"
    output_path = tmp_path / "autocorr_cli.rsf"
    write_rsf(input_path, panel, _header_2d(n1=3, n2=2))

    axis1 = autocorr(panel, axis=1)
    axis2 = autocorr(panel, axis=2, mode="same")
    result = _run_cli(
        "autocorr",
        [str(input_path), "out=" + str(output_path), "axis=1", "mode=full", "normalize=n"],
        tmp_path,
    )

    expected_axis1 = np.stack([np.correlate(trace, trace, mode="full") for trace in panel])
    np.testing.assert_allclose(axis1, expected_axis1)
    assert axis2.shape == (2, 3)
    assert result.returncode == 0, result.stderr
    np.testing.assert_allclose(read_rsf(output_path).data, expected_axis1)


def test_convolve_api_and_cli_modes(tmp_path: Path) -> None:
    data = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    kernel = np.array([1.0, 1.0], dtype=np.float32)
    input_path = tmp_path / "input.rsf"
    kernel_path = tmp_path / "kernel.rsf"
    output_path = tmp_path / "convolve_cli.rsf"
    write_rsf(input_path, data, _header_1d(3))
    write_rsf(kernel_path, kernel, _header_1d(2))

    np.testing.assert_allclose(convolve(data, kernel, mode="full"), np.convolve(data, kernel, mode="full"))
    np.testing.assert_allclose(convolve(data, kernel, mode="same"), np.convolve(data, kernel, mode="same"))
    convolve_rsf(input_path, kernel_path, tmp_path / "conv_api.rsf", mode="full")
    result = _run_cli("convolve", [str(input_path), str(kernel_path), "out=" + str(output_path), "mode=full"], tmp_path)

    assert result.returncode == 0, result.stderr
    np.testing.assert_allclose(read_rsf(output_path).data, np.convolve(data, kernel, mode="full"))


def test_circular_convolution_api_2d_and_cli(tmp_path: Path) -> None:
    data = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float32)
    shift_kernel = np.array([0.0, 1.0, 0.0, 0.0], dtype=np.float32)
    panel = np.vstack([data, data + 10.0]).astype(np.float32)
    input_path = tmp_path / "panel.rsf"
    kernel_path = tmp_path / "kernel.rsf"
    output_path = tmp_path / "cconv_cli.rsf"
    write_rsf(input_path, panel, _header_2d(n1=4, n2=2))
    write_rsf(kernel_path, shift_kernel, _header_1d(4))

    np.testing.assert_allclose(circular_convolve(data, [1.0]), data)
    np.testing.assert_allclose(circular_convolve(data, shift_kernel), np.roll(data, 1))
    np.testing.assert_allclose(circular_convolve(panel, shift_kernel, axis=1), np.roll(panel, 1, axis=1))
    cconv_rsf(input_path, kernel_path, tmp_path / "cconv_api.rsf")
    result = _run_cli("cconv", [str(input_path), str(kernel_path), "out=" + str(output_path), "axis=1"], tmp_path)

    assert result.returncode == 0, result.stderr
    np.testing.assert_allclose(read_rsf(output_path).data, np.roll(panel, 1, axis=1))


def test_envelope_correlation_identical_shifted_2d_and_cli(tmp_path: Path) -> None:
    signal = np.array([0.0, 1.0, 3.0, 1.0, 0.0], dtype=np.float32)
    shifted = np.roll(signal, 1)
    panel = np.vstack([signal, shifted]).astype(np.float32)
    input_path = tmp_path / "a.rsf"
    other_path = tmp_path / "b.rsf"
    output_path = tmp_path / "envcorr_cli.rsf"
    write_rsf(input_path, signal, _header_1d(signal.size))
    write_rsf(other_path, signal, _header_1d(signal.size))

    corr = envelope_correlation(signal, signal, mode="full", normalize=True)
    shifted_corr = envelope_correlation(signal, shifted, mode="full", normalize=True)
    panel_corr = envelope_correlation(panel, signal, axis=1, mode="same", normalize=True)
    result = _run_cli(
        "envcorr",
        [str(input_path), str(other_path), "out=" + str(output_path), "mode=full", "normalize=y"],
        tmp_path,
    )

    assert int(np.argmax(corr)) == signal.size - 1
    np.testing.assert_allclose(np.max(corr), 1.0, atol=1e-6)
    assert int(np.argmax(shifted_corr)) != signal.size - 1
    assert panel_corr.shape == panel.shape
    assert result.returncode == 0, result.stderr
    np.testing.assert_allclose(read_rsf(output_path).data, corr, atol=1e-6)


def test_envcorr_shape_mismatch_raises(tmp_path: Path) -> None:
    a = tmp_path / "a.rsf"
    b = tmp_path / "b.rsf"
    out = tmp_path / "bad.rsf"
    write_rsf(a, np.ones((2, 5), dtype=np.float32), _header_2d(5, 2))
    write_rsf(b, np.ones((3, 5), dtype=np.float32), _header_2d(5, 3))

    with pytest.raises(ConvolutionError, match="not compatible"):
        envcorr_rsf(a, b, out)


def test_shifts_positive_negative_fill_circular_axis_and_cli(tmp_path: Path) -> None:
    data = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float32)
    panel = np.vstack([data, data + 10.0]).astype(np.float32)
    input_path = tmp_path / "panel.rsf"
    output_path = tmp_path / "shift_cli.rsf"
    write_rsf(input_path, panel, _header_2d(4, 2))

    np.testing.assert_allclose(shift(data, 2, fill=-1.0), np.array([-1.0, -1.0, 1.0, 2.0], dtype=np.float32))
    np.testing.assert_allclose(shift(data, -1, fill=0.0), np.array([2.0, 3.0, 4.0, 0.0], dtype=np.float32))
    np.testing.assert_allclose(shift(data, 1, circular=True), np.roll(data, 1))
    np.testing.assert_allclose(shift(panel, 1, axis=2, fill=-1.0), np.vstack([np.full(4, -1.0), data]))
    shifts_rsf(input_path, tmp_path / "shift_api.rsf", shift=1, axis=1, fill=0.0)
    result = _run_cli("shifts", [str(input_path), "out=" + str(output_path), "axis=1", "shift=-1"], tmp_path)

    assert result.returncode == 0, result.stderr
    np.testing.assert_allclose(read_rsf(output_path).data, shift(panel, -1, axis=1))


def test_stacks_statistics_header_and_cli(tmp_path: Path) -> None:
    data = np.array([[1.0, 2.0], [3.0, 4.0], [0.0, 0.0]], dtype=np.float32)
    input_path = tmp_path / "gather.rsf"
    output_path = tmp_path / "stacks_cli.rsf"
    write_rsf(input_path, data, _header_2d(n1=2, n2=3))

    np.testing.assert_allclose(stack_along_axis(data, axis=2, statistic="sum"), np.array([4.0, 6.0], dtype=np.float32))
    np.testing.assert_allclose(stack_along_axis(data, axis=2, statistic="mean"), np.array([4.0 / 3.0, 2.0], dtype=np.float32))
    np.testing.assert_allclose(stack_along_axis(data, axis=2, statistic="rms"), np.sqrt(np.array([10.0 / 3.0, 20.0 / 3.0], dtype=np.float32)))
    np.testing.assert_allclose(stack_along_axis(data, axis=2, statistic="count_nonzero"), np.array([2.0, 2.0], dtype=np.float32))

    stacks_rsf(input_path, tmp_path / "stacks_api.rsf", axis=2, statistic="mean")
    result = _run_cli(
        "stacks",
        [str(input_path), "out=" + str(output_path), "axis=2", "statistic=count_nonzero"],
        tmp_path,
    )

    assert result.returncode == 0, result.stderr
    loaded = read_rsf(output_path)
    assert loaded.header.dimensions == (2,)
    assert loaded.header["stack_statistic"] == "count_nonzero"
    np.testing.assert_allclose(loaded.data, np.array([2.0, 2.0], dtype=np.float32))


def test_rsfdata_signal_correlation_conditioning_methods_do_not_modify_original() -> None:
    trace = np.array([0.0, 1.0, 3.0, 1.0, 0.0], dtype=np.float32)
    panel = np.vstack([trace, trace + 1.0]).astype(np.float32)
    rsf = RSFData(trace, _header_1d(trace.size))
    panel_rsf = RSFData(panel, _header_2d(n1=trace.size, n2=2))

    auto = rsf.autocorr(max_lag=1)
    conv = rsf.convolve(np.array([1.0, 1.0], dtype=np.float32), mode="same")
    cconv = rsf.cconv(np.array([0.0, 1.0, 0.0, 0.0, 0.0], dtype=np.float32))
    env = rsf.envcorr(rsf, mode="same")
    shifted = rsf.shifts(shift=1)
    stacked = panel_rsf.stacks(axis=2, statistic="mean")

    np.testing.assert_allclose(rsf.numpy(), trace)
    assert auto.shape == (3,)
    np.testing.assert_allclose(conv.numpy(), np.convolve(trace, np.array([1.0, 1.0], dtype=np.float32), mode="same"))
    np.testing.assert_allclose(cconv.numpy(), np.roll(trace, 1), atol=1e-6)
    assert env.shape == trace.shape
    np.testing.assert_allclose(shifted.numpy(), shift(trace, 1))
    np.testing.assert_allclose(stacked.numpy(), np.mean(panel, axis=0))


def test_invalid_parameters_raise_clear_errors() -> None:
    with pytest.raises(ConvolutionError, match="max_lag"):
        autocorr(np.ones(3), max_lag=-1)
    with pytest.raises(ConvolutionError, match="kernel length"):
        circular_convolve(np.ones(3), np.ones(4))
    with pytest.raises(ConditioningError, match="axis"):
        shift(np.ones((2, 2)), 1, axis=3)
    with pytest.raises(StackError, match="statistic"):
        stack_along_axis(np.ones((2, 2)), statistic="median")
    with pytest.raises(ConvolutionError, match="real-valued"):
        envelope_correlation(np.ones(3, dtype=np.complex64), np.ones(3, dtype=np.complex64))


@pytest.mark.parametrize(
    "program",
    ["sfautocorr", "sfconvolve", "sfcconv", "sfenvcorr", "sfshifts", "sfstacks"],
)
@pytest.mark.original_madagascar
def test_original_stage_c3_commands_are_optional(program: str) -> None:
    if not original_madagascar_available(program):
        pytest.skip(f"Original Madagascar {program} is not installed")
    pytest.skip(
        f"Original {program} is not directly compared here because the Stage C-3 "
        "subset intentionally uses a smaller Pythonic parameter surface"
    )
