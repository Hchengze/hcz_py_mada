from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys

import numpy as np
import pytest

from pymadagascar import RSFData
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf
from pymadagascar.signal.preprocessing import (
    PreprocessingError,
    cosine_taper,
    costaper_rsf,
    envelope,
    envelope_rsf,
    spectra,
    spectra_rsf,
    threshold,
    threshold_rsf,
)
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


def _header_1d(n1: int, d1: float = 0.01) -> RSFHeader:
    return RSFHeader({"n1": n1, "o1": 0.0, "d1": d1, "label1": "Time", "unit1": "s"})


def _header_2d(n1: int, n2: int, d1: float = 0.01) -> RSFHeader:
    header = _header_1d(n1, d1=d1)
    header["n2"] = n2
    header["o2"] = 0.0
    header["d2"] = 1.0
    header["label2"] = "Trace"
    return header


def test_cosine_taper_1d_center_and_edges() -> None:
    result = cosine_taper(np.ones(8, dtype=np.float32), widths=2)

    np.testing.assert_allclose(result, np.array([0.25, 0.75, 1.0, 1.0, 1.0, 1.0, 0.75, 0.25], dtype=np.float32))
    assert result.dtype == np.float32


def test_cosine_taper_2d_axis_width_zero_and_header(tmp_path: Path) -> None:
    data = np.ones((4, 6), dtype=np.float32)
    tapered = cosine_taper(data, widths={1: 0, 2: 1})

    np.testing.assert_allclose(tapered[0, :], 0.5)
    np.testing.assert_allclose(tapered[-1, :], 0.5)
    np.testing.assert_allclose(tapered[1:-1, :], 1.0)

    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "taper.rsf"
    write_rsf(input_path, data, _header_2d(n1=6, n2=4))
    costaper_rsf(input_path, output_path, widths={1: 2})
    loaded = read_rsf(output_path)

    assert loaded.header["label1"] == "Time"
    assert loaded.header["label2"] == "Trace"
    assert loaded.data.shape == data.shape
    assert np.all(loaded.data[:, 0] < loaded.data[:, 2])


def test_costaper_cli_subprocess(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "taper_cli.rsf"
    write_rsf(input_path, np.ones(8, dtype=np.float32), _header_1d(8))

    result = _run_cli("costaper", [str(input_path), "out=" + str(output_path), "width1=2"], tmp_path)

    assert result.returncode == 0, result.stderr
    np.testing.assert_allclose(read_rsf(output_path).data[[0, -1]], np.array([0.25, 0.25], dtype=np.float32))


def test_threshold_hard_soft_substitute_negative_and_complex() -> None:
    data = np.array([-2.0, -0.5, 0.5, 2.0], dtype=np.float32)
    hard = threshold(data, value=1.0, mode="hard")
    soft = threshold(data, value=1.0, mode="soft")
    sub = threshold(data, value=1.0, mode="hard", substitute=-9.0)
    complex_result = threshold(np.array([0.5 + 0.0j, 3.0 + 4.0j], dtype=np.complex64), value=1.0)

    np.testing.assert_allclose(hard, np.array([-2.0, 0.0, 0.0, 2.0], dtype=np.float32))
    np.testing.assert_allclose(soft, np.array([-1.0, 0.0, 0.0, 1.0], dtype=np.float32))
    np.testing.assert_allclose(sub, np.array([-2.0, -9.0, -9.0, 2.0], dtype=np.float32))
    np.testing.assert_allclose(complex_result, np.array([0.0 + 0.0j, 3.0 + 4.0j], dtype=np.complex64))


def test_threshold_rsf_header_and_cli(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    api_path = tmp_path / "threshold_api.rsf"
    cli_path = tmp_path / "threshold_cli.rsf"
    data = np.array([-2.0, -0.5, 0.5, 2.0], dtype=np.float32)
    write_rsf(input_path, data, _header_1d(4))

    threshold_rsf(input_path, api_path, value=1.0, mode="soft")
    result = _run_cli(
        "threshold",
        [str(input_path), "out=" + str(cli_path), "value=1.0", "mode=hard", "substitute=-1"],
        tmp_path,
    )

    assert result.returncode == 0, result.stderr
    assert read_rsf(api_path).header["label1"] == "Time"
    np.testing.assert_allclose(read_rsf(api_path).data, np.array([-1.0, 0.0, 0.0, 1.0], dtype=np.float32))
    np.testing.assert_allclose(read_rsf(cli_path).data, np.array([-2.0, -1.0, -1.0, 2.0], dtype=np.float32))


def test_spectra_sine_peak_modes_average_and_header(tmp_path: Path) -> None:
    n = 100
    dt = 0.01
    t = np.arange(n) * dt
    trace = np.sin(2.0 * np.pi * 10.0 * t).astype(np.float32)
    panel = np.vstack([trace, 0.5 * trace]).astype(np.float32)
    input_path = tmp_path / "panel.rsf"
    avg_path = tmp_path / "spectra_avg.rsf"
    full_path = tmp_path / "spectra_full.rsf"
    write_rsf(input_path, panel, _header_2d(n1=n, n2=2, d1=dt))

    amp = spectra(trace, axis=1, dt=dt, mode="amplitude")
    power = spectra(trace, axis=1, dt=dt, mode="power")
    spectra_rsf(input_path, avg_path, axis=1, mode="amplitude", average=True)
    spectra_rsf(input_path, full_path, axis=1, mode="power", average=False)

    assert int(np.argmax(amp)) == 10
    np.testing.assert_allclose(power, amp * amp, rtol=1e-6, atol=1e-6)
    avg = read_rsf(avg_path)
    full = read_rsf(full_path)
    assert avg.data.shape == (51,)
    assert avg.header["n1"] == "51"
    assert avg.header["d1"] == "1"
    assert avg.header["label1"] == "Frequency"
    assert avg.header["unit1"] == "Hz"
    assert full.data.shape == (2, 51)
    assert full.header.dimensions == (51, 2)


def test_spectra_cli_subprocess(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "spectra_cli.rsf"
    data = np.sin(2.0 * np.pi * 4.0 * np.arange(64) / 64.0).astype(np.float32)
    write_rsf(input_path, data, _header_1d(64, d1=1.0 / 64.0))

    result = _run_cli("spectra", [str(input_path), "out=" + str(output_path), "axis=1", "mode=amplitude"], tmp_path)

    assert result.returncode == 0, result.stderr
    assert int(np.argmax(read_rsf(output_path).data)) == 4


def test_envelope_sine_2d_shape_header_and_cli(tmp_path: Path) -> None:
    n = 64
    trace = np.sin(2.0 * np.pi * 4.0 * np.arange(n) / n).astype(np.float32)
    panel = np.vstack([trace, 2.0 * trace]).astype(np.float32)
    input_path = tmp_path / "panel.rsf"
    api_path = tmp_path / "envelope_api.rsf"
    cli_path = tmp_path / "envelope_cli.rsf"
    write_rsf(input_path, panel, _header_2d(n1=n, n2=2))

    env = envelope(trace, axis=1)
    envelope_rsf(input_path, api_path, axis=1)
    result = _run_cli("envelope", [str(input_path), "out=" + str(cli_path), "axis=1"], tmp_path)

    assert result.returncode == 0, result.stderr
    np.testing.assert_allclose(env, np.ones(n, dtype=np.float32), atol=1e-6)
    loaded = read_rsf(api_path)
    assert loaded.data.shape == panel.shape
    assert loaded.header["label1"] == "Time"
    np.testing.assert_allclose(loaded.data[0], np.ones(n), atol=1e-6)
    np.testing.assert_allclose(loaded.data[1], np.full(n, 2.0), atol=1e-6)
    np.testing.assert_allclose(read_rsf(cli_path).data, loaded.data)


def test_rsfdata_signal_preprocessing_methods_do_not_modify_original() -> None:
    n = 64
    trace = np.sin(2.0 * np.pi * 4.0 * np.arange(n) / n).astype(np.float32)
    rsf = RSFData(trace, _header_1d(n, d1=1.0 / 64.0))

    tapered = rsf.costaper(widths=2)
    thresholded = rsf.threshold(value=0.5, mode="hard")
    spec = rsf.spectra(axis=1)
    env = rsf.envelope(axis=1)

    np.testing.assert_allclose(rsf.numpy(), trace)
    assert tapered.shape == rsf.shape
    assert thresholded.shape == rsf.shape
    assert spec.shape == (33,)
    assert spec.header["label1"] == "Frequency"
    np.testing.assert_allclose(env.numpy(), np.ones(n), atol=1e-6)


def test_invalid_parameters_raise_clear_errors() -> None:
    with pytest.raises(PreprocessingError, match="half"):
        cosine_taper(np.ones(4), widths=3)
    with pytest.raises(PreprocessingError, match="nonnegative"):
        threshold(np.ones(4), value=-1.0)
    with pytest.raises(PreprocessingError, match="real-valued"):
        spectra(np.ones(4, dtype=np.complex64))
    with pytest.raises(PreprocessingError, match="axis"):
        envelope(np.ones(4), axis=2)


@pytest.mark.original_madagascar
def test_original_sfcostaper_comparison_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfcostaper"):
        pytest.skip("Original Madagascar sfcostaper is not installed")

    input_path = tmp_path / "input.rsf"
    original_path = tmp_path / "original.rsf"
    python_path = tmp_path / "python.rsf"
    data = np.ones(8, dtype=np.float32)
    write_rsf(input_path, data, _header_1d(8))

    run_original_madagascar(
        ["sfcostaper", "in=input.rsf", "out=original.rsf", "nw1=2"],
        cwd=tmp_path,
        require_program="sfcostaper",
    )
    costaper_rsf(input_path, python_path, widths={1: 2})

    np.testing.assert_allclose(read_rsf(original_path).data, read_rsf(python_path).data, rtol=1e-6, atol=1e-6)


@pytest.mark.parametrize("program", ["sfthreshold", "sfspectra", "sfenvelope"])
@pytest.mark.original_madagascar
def test_original_stage_c_remaining_commands_are_optional(program: str) -> None:
    if not original_madagascar_available(program):
        pytest.skip(f"Original Madagascar {program} is not installed")
    pytest.skip(
        f"Original {program} is not directly compared here because the Stage C-1 "
        "subset intentionally uses a smaller Pythonic parameter surface"
    )
