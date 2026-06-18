from pathlib import Path
import os
import subprocess
import sys

import numpy as np
import pytest

from pymadagascar.cli.fft import main as fft_main
from pymadagascar.cli.ifft import main as ifft_main
from pymadagascar.cli.rfft import main as rfft_main
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf
from pymadagascar.signal.fft import (
    FFTError,
    fft_axis_header_update,
    fft_rsf,
    ifft_rsf,
    irfft_rsf,
    rfft_rsf,
)
from pymadagascar.testing.runner import original_madagascar_available, run_original_madagascar


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _run_module(module: str, *args: str | Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    pythonpath = str(PROJECT_ROOT)
    if env.get("PYTHONPATH"):
        pythonpath += os.pathsep + env["PYTHONPATH"]
    env["PYTHONPATH"] = pythonpath
    return subprocess.run(
        [sys.executable, "-m", module, *[str(arg) for arg in args]],
        cwd=PROJECT_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def _header_1d(n1: int = 8) -> RSFHeader:
    return RSFHeader({"o1": 0.0, "d1": 0.25, "label1": "Time", "unit1": "s", "n1": n1})


def _header_2d() -> RSFHeader:
    return RSFHeader(
        {
            "o1": 0.0,
            "d1": 0.004,
            "label1": "Time",
            "unit1": "s",
            "o2": 100.0,
            "d2": 25.0,
            "label2": "Trace",
            "unit2": "m",
        }
    )


def _header_3d() -> RSFHeader:
    return RSFHeader(
        {
            "o1": 0.0,
            "d1": 0.004,
            "label1": "Time",
            "unit1": "s",
            "o2": 100.0,
            "d2": 25.0,
            "label2": "Trace",
            "unit2": "m",
            "o3": 1.0,
            "d3": 1.0,
            "label3": "Shot",
        }
    )


def test_delta_fft_matches_numpy_centered_spectrum(tmp_path: Path) -> None:
    input_path = tmp_path / "delta.rsf"
    output_path = tmp_path / "fft.rsf"
    data = np.zeros(8, dtype=np.float32)
    data[0] = 1.0
    write_rsf(input_path, data, _header_1d())

    fft_rsf(input_path, output_path, axis=1)
    loaded = read_rsf(output_path)

    expected = np.fft.fftshift(np.fft.fft(data.astype(np.complex64))).astype(np.complex64)
    assert loaded.data.dtype == np.complex64
    np.testing.assert_allclose(loaded.data, expected, atol=1e-6)
    assert loaded.header["n1"] == "8"
    assert loaded.header["o1"] == "-2"
    assert loaded.header["d1"] == "0.5"
    assert loaded.header["label1"] == "Frequency"
    assert loaded.header["unit1"] == "Hz"
    assert loaded.header["fft_n1"] == "8"
    assert loaded.header["fft_d1"] == "0.25"


def test_sine_wave_rfft_has_expected_peak(tmp_path: Path) -> None:
    input_path = tmp_path / "sine.rsf"
    output_path = tmp_path / "sine_fft.rsf"
    n = 32
    samples = np.arange(n, dtype=np.float32)
    data = np.sin(2.0 * np.pi * 3.0 * samples / n).astype(np.float32)
    write_rsf(input_path, data, RSFHeader({"o1": 0.0, "d1": 1.0, "label1": "Time", "unit1": "s"}))

    rfft_rsf(input_path, output_path, axis=1)
    loaded = read_rsf(output_path)

    magnitude = np.abs(loaded.data)
    assert int(np.argmax(magnitude[1:]) + 1) == 3
    assert loaded.header.dimensions == (17,)
    assert loaded.header["o1"] == "0"
    assert loaded.header["d1"] == "0.03125"


def test_fft_frequency_axis_matches_numpy_fftfreq(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "fft.rsf"
    n = 10
    d = 0.2
    data = np.ones(n, dtype=np.float32)
    write_rsf(input_path, data, RSFHeader({"o1": 2.0, "d1": d, "label1": "Time", "unit1": "s"}))

    fft_rsf(input_path, output_path, axis=1)
    loaded = read_rsf(output_path)

    expected_freqs = np.fft.fftshift(np.fft.fftfreq(n, d=d))
    assert float(loaded.header["o1"]) == pytest.approx(float(expected_freqs[0]))
    assert float(loaded.header["d1"]) == pytest.approx(float(expected_freqs[1] - expected_freqs[0]), rel=1e-5)
    assert loaded.header["fft_o1"] == "2"
    assert loaded.header["fft_d1"] == "0.2"


def test_rfft_frequency_axis_matches_numpy_rfftfreq(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "rfft.rsf"
    n = 12
    d = 0.004
    data = np.ones(n, dtype=np.float32)
    write_rsf(input_path, data, RSFHeader({"o1": 0.0, "d1": d, "label1": "Time", "unit1": "s"}))

    rfft_rsf(input_path, output_path, axis=1)
    loaded = read_rsf(output_path)

    expected_freqs = np.fft.rfftfreq(n, d=d)
    assert loaded.header.dimensions == (expected_freqs.size,)
    assert float(loaded.header["o1"]) == pytest.approx(0.0)
    assert float(loaded.header["d1"]) == pytest.approx(float(expected_freqs[1] - expected_freqs[0]), rel=1e-5)
    assert loaded.header["label1"] == "Frequency"
    assert loaded.header["unit1"] == "Hz"


def test_fft_float64_input_outputs_complex64_by_design(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "fft.rsf"
    data = np.linspace(0.0, 1.0, 8, dtype=np.float64)
    write_rsf(input_path, data, _header_1d())

    fft_rsf(input_path, output_path, axis=1)
    loaded = read_rsf(output_path)

    assert loaded.data.dtype == np.complex64
    assert loaded.header["data_format"] == "native_complex"


def test_fft_then_ifft_restores_complex_data_and_header(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    fft_path = tmp_path / "fft.rsf"
    output_path = tmp_path / "restored.rsf"
    real = np.arange(8, dtype=np.float32)
    imag = np.linspace(0.0, 1.0, 8, dtype=np.float32)
    data = (real + 1j * imag).astype(np.complex64)
    write_rsf(input_path, data, _header_1d())

    fft_rsf(input_path, fft_path, axis=1)
    ifft_rsf(fft_path, output_path, axis=1)
    loaded = read_rsf(output_path)

    np.testing.assert_allclose(loaded.data, data, atol=1e-6)
    assert loaded.header["n1"] == "8"
    assert loaded.header["o1"] == "0"
    assert loaded.header["d1"] == "0.25"
    assert loaded.header["label1"] == "Time"
    assert loaded.header["unit1"] == "s"
    assert "fft_n1" not in loaded.header


def test_rfft_then_irfft_restores_real_data(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    fft_path = tmp_path / "rfft.rsf"
    output_path = tmp_path / "restored.rsf"
    data = np.linspace(-1.0, 1.0, 9, dtype=np.float32)
    write_rsf(input_path, data, RSFHeader({"o1": 1.0, "d1": 0.5, "label1": "Time", "unit1": "s"}))

    rfft_rsf(input_path, fft_path, axis=1)
    irfft_rsf(fft_path, output_path, axis=1)
    loaded = read_rsf(output_path)

    assert loaded.data.dtype == np.float32
    np.testing.assert_allclose(loaded.data, data, atol=1e-6)
    assert loaded.header["n1"] == "9"
    assert loaded.header["o1"] == "1"
    assert loaded.header["d1"] == "0.5"


def test_rfft_irfft_axis2_restores_real_data_and_metadata(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    fft_path = tmp_path / "rfft_axis2.rsf"
    output_path = tmp_path / "restored.rsf"
    data = np.arange(24, dtype=np.float32).reshape(4, 6)
    write_rsf(input_path, data, _header_2d())

    rfft_rsf(input_path, fft_path, axis=2)
    irfft_rsf(fft_path, output_path, axis=2)
    loaded = read_rsf(output_path)

    assert loaded.data.dtype == np.float32
    np.testing.assert_allclose(loaded.data, data, atol=1e-6)
    assert loaded.header.dimensions == (6, 4)
    assert loaded.header["o2"] == "100"
    assert loaded.header["d2"] == "25"
    assert loaded.header["label2"] == "Trace"
    assert loaded.header["unit2"] == "m"
    assert "fft_n2" not in loaded.header


def test_2d_rfft_along_axis2_updates_shape_and_header(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "rfft_axis2.rsf"
    data = np.arange(24, dtype=np.float32).reshape(4, 6)
    write_rsf(input_path, data, _header_2d())

    rfft_rsf(input_path, output_path, axis=2)
    loaded = read_rsf(output_path)

    expected = np.fft.rfft(data, axis=0).astype(np.complex64)
    np.testing.assert_allclose(loaded.data, expected, atol=1e-6)
    assert loaded.header.dimensions == (6, 3)
    assert loaded.header["label2"] == "Frequency"
    assert loaded.header["unit2"] == "1/m"


def test_3d_fft_along_axis3_updates_shape_and_header(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "fft_axis3.rsf"
    data = np.arange(24, dtype=np.float32).reshape(2, 3, 4)
    write_rsf(input_path, data, _header_3d())

    fft_rsf(input_path, output_path, axis=3)
    loaded = read_rsf(output_path)

    expected = np.fft.fftshift(np.fft.fft(data.astype(np.complex64), axis=0), axes=0).astype(np.complex64)
    np.testing.assert_allclose(loaded.data, expected, atol=1e-6)
    assert loaded.header.dimensions == (4, 3, 2)
    assert loaded.header["label3"] == "Frequency"
    assert loaded.header["fft_n3"] == "2"


def test_fft_axis_header_update_for_rfft() -> None:
    header = fft_axis_header_update(_header_1d(), axis=1, transform="rfft")

    assert header["n1"] == "5"
    assert header["o1"] == "0"
    assert header["d1"] == "0.5"
    assert header["label1"] == "Frequency"
    assert header["unit1"] == "Hz"
    assert header["fft_label1"] == "Time"


def test_fft_rejects_bad_axis(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "bad.rsf"
    write_rsf(input_path, np.ones(8, dtype=np.float32), _header_1d())

    with pytest.raises(FFTError, match="axis must be between"):
        fft_rsf(input_path, output_path, axis=2)

    assert not output_path.exists()


def test_fft_rejects_bad_norm(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "bad.rsf"
    write_rsf(input_path, np.ones(8, dtype=np.float32), _header_1d())

    with pytest.raises(FFTError, match="norm="):
        fft_rsf(input_path, output_path, norm="unitary")

    assert not output_path.exists()


def test_fft_cli_and_ifft_cli_round_trip(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    fft_path = tmp_path / "fft.rsf"
    output_path = tmp_path / "restored.rsf"
    data = np.linspace(0.0, 1.0, 8, dtype=np.float32)
    write_rsf(input_path, data, _header_1d())

    assert fft_main([str(input_path), "out=" + str(fft_path), "axis=1"]) == 0
    assert ifft_main([str(fft_path), "out=" + str(output_path), "axis=1"]) == 0
    loaded = read_rsf(output_path)

    np.testing.assert_allclose(loaded.data.real, data, atol=1e-6)
    np.testing.assert_allclose(loaded.data.imag, 0.0, atol=1e-6)


def test_rfft_cli(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "rfft.rsf"
    data = np.ones(8, dtype=np.float32)
    write_rsf(input_path, data, _header_1d())

    code = rfft_main([str(input_path), "out=" + str(output_path), "axis=1", "norm=backward"])
    loaded = read_rsf(output_path)

    assert code == 0
    assert loaded.data.dtype == np.complex64
    assert loaded.header.dimensions == (5,)
    np.testing.assert_allclose(loaded.data[0], 8.0 + 0.0j)


def test_fft_cli_subprocess_round_trip(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    fft_path = tmp_path / "fft.rsf"
    output_path = tmp_path / "restored.rsf"
    data = np.linspace(-1.0, 1.0, 8, dtype=np.float32)
    write_rsf(input_path, data, _header_1d())

    fft_proc = _run_module("pymadagascar.cli.fft", input_path, "out=" + str(fft_path), "axis=1")
    ifft_proc = _run_module("pymadagascar.cli.ifft", fft_path, "out=" + str(output_path), "axis=1")

    assert fft_proc.returncode == 0, fft_proc.stderr
    assert ifft_proc.returncode == 0, ifft_proc.stderr
    loaded = read_rsf(output_path)
    np.testing.assert_allclose(loaded.data.real, data, atol=1e-6)
    np.testing.assert_allclose(loaded.data.imag, 0.0, atol=1e-6)


def test_rfft_cli_subprocess_writes_frequency_axis(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "rfft.rsf"
    data = np.ones(16, dtype=np.float32)
    write_rsf(input_path, data, RSFHeader({"o1": 0.0, "d1": 0.002, "label1": "Time", "unit1": "s"}))

    proc = _run_module("pymadagascar.cli.rfft", input_path, "out=" + str(output_path), "axis=1")
    loaded = read_rsf(output_path)

    assert proc.returncode == 0, proc.stderr
    assert loaded.data.dtype == np.complex64
    assert loaded.header.dimensions == (9,)
    assert float(loaded.header["d1"]) == pytest.approx(31.25)


def test_rfft_cli_reports_complex_input(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "bad.rsf"
    write_rsf(input_path, np.ones(8, dtype=np.complex64), _header_1d())

    code = rfft_main([str(input_path), "out=" + str(output_path)])

    assert code == 2
    assert "requires real-valued input" in capsys.readouterr().err
    assert not output_path.exists()


def test_original_sffft1_comparison_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sffft1"):
        pytest.skip("Original Madagascar sffft1 is not installed")

    input_path = tmp_path / "input.rsf"
    original = tmp_path / "original.rsf"
    python = tmp_path / "python.rsf"
    data = np.arange(8, dtype=np.float32)
    write_rsf(input_path, data, _header_1d())

    run_original_madagascar(
        ["sffft1", "in=input.rsf", "out=original.rsf", "opt=n"],
        cwd=tmp_path,
        require_program="sffft1",
    )
    rfft_rsf(input_path, python, axis=1)

    original_rsf = read_rsf(original)
    python_rsf = read_rsf(python)
    np.testing.assert_allclose(python_rsf.data, original_rsf.data, atol=1e-5)
    assert python_rsf.header["n1"] == original_rsf.header["n1"]
