from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from pymadagascar import RSFData
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf
from pymadagascar.signal.qc import (
    SignalQCError,
    bandstop,
    bandstop_rsf,
    decimate,
    decimate_rsf,
    demean,
    detrend,
    local_rms,
    notch,
)
from pymadagascar.testing.runner import original_madagascar_available


ROOT = Path(__file__).resolve().parents[1]


def _header(n1: int, n2: int | None = None, *, d1: float = 0.001) -> RSFHeader:
    values: dict[str, object] = {
        "n1": n1,
        "o1": 0.25,
        "d1": d1,
        "label1": "Time",
        "unit1": "s",
    }
    if n2 is not None:
        values.update(
            {
                "n2": n2,
                "o2": 10.0,
                "d2": 5.0,
                "label2": "Channel",
                "unit2": "m",
            }
        )
    return RSFHeader(values)


def _run_cli(module: str, args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = (
        str(ROOT)
        if not env.get("PYTHONPATH")
        else str(ROOT) + os.pathsep + env["PYTHONPATH"]
    )
    return subprocess.run(
        [sys.executable, "-m", f"pymadagascar.cli.{module}", *args],
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_demean_global_axis_nan_and_complex_contract() -> None:
    panel = np.array([[1.0, 2.0, np.nan], [4.0, 5.0, 6.0]], dtype=np.float32)
    result = demean(panel, axis=1, nan_policy="omit")
    np.testing.assert_allclose(result[0, :2], [-0.5, 0.5])
    np.testing.assert_allclose(result[1], [-1.0, 0.0, 1.0])
    assert np.isnan(result[0, 2])
    assert result.dtype == np.float32

    complex_result = demean(np.array([1 + 2j, 3 + 4j], dtype=np.complex64))
    np.testing.assert_allclose(complex_result, [-1 - 1j, 1 + 1j])
    assert complex_result.dtype == np.complex64


def test_detrend_constant_linear_and_two_dimensional_axis() -> None:
    x = np.arange(10, dtype=np.float32)
    np.testing.assert_allclose(detrend(2.5 * x + 7.0), 0.0, atol=1e-6)
    panel = np.stack((x + 2.0, 3.0 * x - 4.0))
    np.testing.assert_allclose(detrend(panel, axis=1), 0.0, atol=1e-6)
    np.testing.assert_allclose(
        detrend(panel, axis=1, type="constant"),
        panel - panel.mean(axis=1, keepdims=True),
        atol=1e-6,
    )


def test_detrend_nan_policy_omit_and_raise() -> None:
    trace = np.array([1.0, np.nan, 5.0, 7.0], dtype=np.float32)
    result = detrend(trace, nan_policy="omit")
    assert np.isnan(result[1])
    np.testing.assert_allclose(result[[0, 2, 3]], 0.0, atol=1e-6)
    with pytest.raises(SignalQCError, match="NaN"):
        detrend(trace, nan_policy="raise")


def test_decimate_stride_antialias_and_complex_dtype() -> None:
    data = np.arange(10, dtype=np.float32)
    np.testing.assert_array_equal(decimate(data, 3, anti_alias=False), [0.0, 3.0, 6.0, 9.0])
    filtered = decimate(np.ones(10, dtype=np.float32), 4)
    np.testing.assert_allclose(filtered, 1.0)
    complex_result = decimate(
        np.arange(8, dtype=np.float32).astype(np.complex64) * (1.0 + 1.0j),
        2,
    )
    assert complex_result.dtype == np.complex64


def test_decimate_rsf_updates_only_selected_axis(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "decimated.rsf"
    data = np.arange(30, dtype=np.float32).reshape(3, 10)
    write_rsf(input_path, data, _header(10, 3, d1=0.002))
    decimate_rsf(input_path, output_path, factor=4, axis=1, anti_alias=False)
    result = read_rsf(output_path)
    assert result.data.shape == (3, 3)
    assert result.header["n1"] == "3"
    assert result.header["d1"] == "0.008"
    assert result.header["o1"] == "0.25"
    assert result.header["n2"] == "3"
    assert result.header["label2"] == "Channel"


def test_bandstop_and_notch_remove_target_frequency() -> None:
    n = 1000
    dt = 0.001
    time = np.arange(n) * dt
    signal = np.sin(2.0 * np.pi * 10.0 * time) + np.sin(2.0 * np.pi * 50.0 * time)
    stopped = bandstop(signal, dt, 45.0, 55.0)
    notched = notch(signal, dt, 50.0, width=10.0)
    source_spectrum = np.abs(np.fft.rfft(signal))
    stopped_spectrum = np.abs(np.fft.rfft(stopped))
    notched_spectrum = np.abs(np.fft.rfft(notched))
    assert stopped_spectrum[50] < source_spectrum[50] * 1e-5
    assert notched_spectrum[50] < source_spectrum[50] * 1e-5
    assert stopped_spectrum[10] == pytest.approx(source_spectrum[10], rel=1e-5)


def test_bandstop_rsf_preserves_shape_header_and_float_dtype(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "bandstop.rsf"
    data = np.ones((2, 64), dtype=np.float32)
    write_rsf(input_path, data, _header(64, 2, d1=0.004))
    bandstop_rsf(input_path, output_path, fmin=20.0, fmax=40.0, axis=1)
    result = read_rsf(output_path)
    assert result.data.shape == data.shape
    assert result.data.dtype == np.float32
    assert result.header["label1"] == "Time"
    assert result.header["label2"] == "Channel"


def test_local_rms_constant_edges_axis_and_complex_contract() -> None:
    panel = np.ones((3, 9), dtype=np.float32)
    result = local_rms(panel, rect=5, axis=1)
    np.testing.assert_allclose(result, 1.0)
    assert result.shape == panel.shape
    assert result.dtype == np.float32
    complex_result = local_rms(np.full(7, 3.0 + 4.0j, dtype=np.complex64), rect=3)
    np.testing.assert_allclose(complex_result, 5.0)
    assert complex_result.dtype == np.float32


@pytest.mark.parametrize(
    ("module", "parameters"),
    [
        ("demean", ["axis=1"]),
        ("detrend", ["axis=1", "type=linear"]),
        ("decimate", ["axis=1", "factor=2", "anti_alias=n"]),
        ("bandstop", ["axis=1", "fmin=45", "fmax=55"]),
        ("notch", ["axis=1", "f0=50", "width=10"]),
        ("localrms", ["axis=1", "rect=5"]),
    ],
)
def test_stage_c7_cli_subprocess(
    module: str,
    parameters: list[str],
    tmp_path: Path,
) -> None:
    n = 200
    dt = 0.001
    time = np.arange(n) * dt
    data = (2.0 + time + np.sin(2.0 * np.pi * 50.0 * time)).astype(np.float32)
    input_path = tmp_path / f"{module}_input.rsf"
    output_path = tmp_path / f"{module}_output.rsf"
    write_rsf(input_path, data, _header(n, d1=dt))
    result = _run_cli(
        module,
        [str(input_path), "out=" + str(output_path), *parameters],
        tmp_path,
    )
    assert result.returncode == 0, result.stderr
    assert output_path.exists()


def test_rsfdata_chain_methods_and_inplace_contract() -> None:
    n = 200
    dt = 0.001
    time = np.arange(n) * dt
    data = (2.0 + time + np.sin(2.0 * np.pi * 50.0 * time)).astype(np.float32)
    source = RSFData(data, _header(n, d1=dt))
    result = (
        source.demean()
        .detrend()
        .notch(f0=50.0, width=10.0)
        .decimate(2, anti_alias=True)
        .localrms(rect=5)
    )
    assert source.shape == (n,)
    assert result.shape == (n // 2,)
    assert result.header["d1"] == "0.002"
    returned = source.bandstop(fmin=45.0, fmax=55.0, inplace=True)
    assert returned is source
    assert source.shape == (n,)


def test_invalid_parameters_raise_clear_errors() -> None:
    with pytest.raises(SignalQCError, match="axis"):
        demean(np.ones(4), axis=2)
    with pytest.raises(SignalQCError, match="type"):
        detrend(np.ones(4), type="quadratic")
    with pytest.raises(SignalQCError, match="factor"):
        decimate(np.ones(4), 0)
    with pytest.raises(SignalQCError, match="real-valued"):
        bandstop(np.ones(8, dtype=np.complex64), 0.01, 1.0, 2.0)
    with pytest.raises(SignalQCError, match="width or q"):
        notch(np.ones(8), 0.01, 10.0)
    with pytest.raises(SignalQCError, match="rect"):
        local_rms(np.ones(4), rect=0)


@pytest.mark.parametrize(
    "program",
    ["sfdemean", "sfdetrend", "sfdecimate", "sfbandstop", "sfnotch", "sfrms"],
)
@pytest.mark.original_madagascar
def test_original_stage_c7_commands_are_optional(program: str) -> None:
    if not original_madagascar_available(program):
        pytest.skip(f"Original Madagascar {program} is not installed")
    pytest.skip(
        f"{program} is not directly compared because Stage C-7 uses a smaller "
        "Pythonic parameter and boundary contract"
    )
