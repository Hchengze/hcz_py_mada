from pathlib import Path
import os
import subprocess
import sys

import numpy as np
import pytest

from pymadagascar.cli.bandpass import main as bandpass_main
from pymadagascar.cli.highpass import main as highpass_main
from pymadagascar.cli.lowpass import main as lowpass_main
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf
from pymadagascar.signal.filter import (
    FilterError,
    bandpass_rsf,
    highpass_rsf,
    lowpass_rsf,
    make_filter_taper,
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


def _header(n1: int = 1000, d1: float = 0.001) -> RSFHeader:
    return RSFHeader(
        {
            "n1": n1,
            "o1": 0.0,
            "d1": d1,
            "label1": "Time",
            "unit1": "s",
            "o2": 0.0,
            "d2": 1.0,
            "label2": "Trace",
        }
    )


def _sine(freq: float, n: int = 1000, d: float = 0.001) -> np.ndarray:
    t = np.arange(n, dtype=np.float64) * d
    return np.sin(2.0 * np.pi * freq * t).astype(np.float32)


def _rms(data: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(np.asarray(data, dtype=np.float64)))))


def test_make_filter_taper_bandpass_with_cosine_edges() -> None:
    freqs = np.array([0.0, 5.0, 10.0, 20.0, 30.0, 35.0], dtype=np.float64)

    taper = make_filter_taper(freqs, kind="bandpass", flo=10.0, fhi=30.0, taper=5.0)

    np.testing.assert_allclose(taper, np.array([0.0, 0.0, 1.0, 1.0, 1.0, 0.0], dtype=np.float32))


def test_make_filter_taper_bandpass_transition_midpoints() -> None:
    freqs = np.array([7.5, 10.0, 20.0, 30.0, 32.5], dtype=np.float64)

    taper = make_filter_taper(freqs, kind="bandpass", flo=10.0, fhi=30.0, taper=5.0)

    np.testing.assert_allclose(taper, np.array([0.5, 1.0, 1.0, 1.0, 0.5], dtype=np.float32))


def test_bandpass_preserves_single_frequency_in_passband(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "bandpass.rsf"
    data = _sine(20.0)
    write_rsf(input_path, data, _header())

    bandpass_rsf(input_path, output_path, flo=10.0, fhi=30.0)
    loaded = read_rsf(output_path)

    np.testing.assert_allclose(loaded.data, data, atol=1e-5)
    assert loaded.data.dtype == np.float32


def test_bandpass_keeps_flo_and_fhi_boundary_frequencies(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "bandpass.rsf"
    data = (_sine(10.0) + 0.5 * _sine(30.0)).astype(np.float32)
    write_rsf(input_path, data, _header())

    bandpass_rsf(input_path, output_path, flo=10.0, fhi=30.0)
    loaded = read_rsf(output_path)

    np.testing.assert_allclose(loaded.data, data, atol=1e-5)


def test_bandpass_suppresses_high_frequency(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "bandpass.rsf"
    data = (_sine(20.0) + _sine(120.0)).astype(np.float32)
    write_rsf(input_path, data, _header())

    bandpass_rsf(input_path, output_path, flo=10.0, fhi=30.0)
    loaded = read_rsf(output_path)

    np.testing.assert_allclose(loaded.data, _sine(20.0), atol=1e-5)
    assert _rms(loaded.data - _sine(20.0)) < 1e-5


def test_bandpass_suppresses_low_frequency(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "bandpass.rsf"
    data = (_sine(3.0) + _sine(20.0)).astype(np.float32)
    write_rsf(input_path, data, _header())

    bandpass_rsf(input_path, output_path, flo=10.0, fhi=30.0)
    loaded = read_rsf(output_path)

    np.testing.assert_allclose(loaded.data, _sine(20.0), atol=1e-5)


def test_bandpass_zero_phase_preserves_passband_phase(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "bandpass.rsf"
    n = 1000
    d = 0.001
    t = np.arange(n, dtype=np.float64) * d
    data = np.sin(2.0 * np.pi * 20.0 * t + 0.7).astype(np.float32)
    write_rsf(input_path, data, _header(n1=n, d1=d))

    bandpass_rsf(input_path, output_path, flo=10.0, fhi=30.0)
    loaded = read_rsf(output_path)

    np.testing.assert_allclose(loaded.data, data, atol=1e-5)


def test_lowpass_suppresses_high_frequency(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "lowpass.rsf"
    low = _sine(15.0)
    high = _sine(120.0)
    write_rsf(input_path, (low + high).astype(np.float32), _header())

    lowpass_rsf(input_path, output_path, fcut=30.0)
    loaded = read_rsf(output_path)

    np.testing.assert_allclose(loaded.data, low, atol=1e-5)


def test_highpass_suppresses_low_frequency(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "highpass.rsf"
    low = _sine(15.0)
    high = _sine(120.0)
    write_rsf(input_path, (low + high).astype(np.float32), _header())

    highpass_rsf(input_path, output_path, fcut=60.0)
    loaded = read_rsf(output_path)

    np.testing.assert_allclose(loaded.data, high, atol=1e-5)


def test_multitrace_filter_along_axis1(tmp_path: Path) -> None:
    input_path = tmp_path / "gather.rsf"
    output_path = tmp_path / "filtered.rsf"
    low = _sine(10.0)
    high = _sine(100.0)
    data = np.stack([low + high, 2.0 * low + high, low - high], axis=0).astype(np.float32)
    write_rsf(input_path, data, _header())

    lowpass_rsf(input_path, output_path, fcut=30.0, axis=1)
    loaded = read_rsf(output_path)

    expected = np.stack([low, 2.0 * low, low], axis=0).astype(np.float32)
    np.testing.assert_allclose(loaded.data, expected, atol=1e-5)
    assert loaded.header.dimensions == (1000, 3)
    assert loaded.header["label1"] == "Time"
    assert loaded.header["label2"] == "Trace"


def test_3d_filter_along_axis1(tmp_path: Path) -> None:
    input_path = tmp_path / "cube.rsf"
    output_path = tmp_path / "filtered.rsf"
    low = _sine(12.0)
    high = _sine(110.0)
    trace = (low + high).astype(np.float32)
    data = np.broadcast_to(trace, (2, 3, trace.size)).copy()
    header = _header()
    header["o3"] = 1.0
    header["d3"] = 1.0
    header["label3"] = "Shot"
    write_rsf(input_path, data, header)

    lowpass_rsf(input_path, output_path, fcut=30.0, axis=1)
    loaded = read_rsf(output_path)

    expected = np.broadcast_to(low, data.shape)
    np.testing.assert_allclose(loaded.data, expected, atol=1e-5)
    assert loaded.header.dimensions == (1000, 3, 2)
    assert loaded.header["label3"] == "Shot"


def test_filter_preserves_float64_dtype_and_header(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "filtered.rsf"
    data = _sine(20.0).astype(np.float64)
    write_rsf(input_path, data, _header())

    bandpass_rsf(input_path, output_path, flo=10.0, fhi=30.0)
    loaded = read_rsf(output_path)

    assert loaded.data.dtype == np.float64
    assert loaded.header["data_format"] == "native_double"
    assert loaded.header["o1"] == "0"
    assert loaded.header["d1"] == "0.001"


def test_filter_rejects_cutoff_above_nyquist(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "bad.rsf"
    write_rsf(input_path, _sine(20.0), _header())

    with pytest.raises(FilterError, match="Nyquist"):
        lowpass_rsf(input_path, output_path, fcut=600.0)

    assert not output_path.exists()


def test_bandpass_rejects_equal_flo_fhi(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "bad.rsf"
    write_rsf(input_path, _sine(20.0), _header())

    with pytest.raises(FilterError, match="flo= must be smaller than fhi="):
        bandpass_rsf(input_path, output_path, flo=30.0, fhi=30.0)

    assert not output_path.exists()


def test_filter_rejects_complex_input(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "bad.rsf"
    write_rsf(input_path, _sine(20.0).astype(np.complex64), _header())

    with pytest.raises(FilterError, match="real-valued input"):
        lowpass_rsf(input_path, output_path, fcut=30.0)

    assert not output_path.exists()


def test_bandpass_cli(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "bandpass.rsf"
    data = (_sine(20.0) + _sine(120.0)).astype(np.float32)
    write_rsf(input_path, data, _header())

    code = bandpass_main(
        [str(input_path), "out=" + str(output_path), "flo=10", "fhi=30", "taper=0"]
    )
    loaded = read_rsf(output_path)

    assert code == 0
    np.testing.assert_allclose(loaded.data, _sine(20.0), atol=1e-5)


def test_lowpass_cli(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "lowpass.rsf"
    data = (_sine(20.0) + _sine(120.0)).astype(np.float32)
    write_rsf(input_path, data, _header())

    code = lowpass_main([str(input_path), "out=" + str(output_path), "fcut=30"])
    loaded = read_rsf(output_path)

    assert code == 0
    np.testing.assert_allclose(loaded.data, _sine(20.0), atol=1e-5)


def test_highpass_cli(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "highpass.rsf"
    data = (_sine(20.0) + _sine(120.0)).astype(np.float32)
    write_rsf(input_path, data, _header())

    code = highpass_main([str(input_path), "out=" + str(output_path), "fcut=60"])
    loaded = read_rsf(output_path)

    assert code == 0
    np.testing.assert_allclose(loaded.data, _sine(120.0), atol=1e-5)


def test_bandpass_cli_subprocess(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "bandpass.rsf"
    data = (_sine(20.0) + _sine(120.0)).astype(np.float32)
    write_rsf(input_path, data, _header())

    proc = _run_module(
        "pymadagascar.cli.bandpass",
        input_path,
        "out=" + str(output_path),
        "flo=10",
        "fhi=30",
        "taper=0",
    )

    assert proc.returncode == 0, proc.stderr
    loaded = read_rsf(output_path)
    np.testing.assert_allclose(loaded.data, _sine(20.0), atol=1e-5)


def test_cli_reports_missing_frequency(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "bad.rsf"
    write_rsf(input_path, _sine(20.0), _header())

    code = bandpass_main([str(input_path), "out=" + str(output_path), "flo=10"])

    assert code == 2
    assert "Missing required parameter: fhi=" in capsys.readouterr().err
    assert not output_path.exists()


def test_original_sfbandpass_shape_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfbandpass"):
        pytest.skip("Original Madagascar sfbandpass is not installed")

    input_path = tmp_path / "input.rsf"
    original = tmp_path / "original.rsf"
    data = (_sine(20.0) + _sine(120.0)).astype(np.float32)
    write_rsf(input_path, data, _header())

    run_original_madagascar(
        ["sfbandpass", "in=input.rsf", "out=original.rsf", "flo=10", "fhi=30"],
        cwd=tmp_path,
        require_program="sfbandpass",
    )
    original_rsf = read_rsf(original)

    assert original_rsf.data.shape == data.shape
    assert original_rsf.header.dimensions == (1000,)
