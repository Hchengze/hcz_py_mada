from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from pymadagascar import RSFData
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf
from pymadagascar.signal.spectral import (
    SpectralQCError,
    apply_window,
    coherence,
    coherence_rsf,
    csd,
    psd,
    psd_rsf,
    snr,
    spectrogram,
    spectrogram_rsf,
    window_function,
    windowfunc_rsf,
)


ROOT = Path(__file__).resolve().parents[1]


def _header(n1: int, n2: int | None = None, *, d1: float = 0.004) -> RSFHeader:
    values: dict[str, object] = {
        "n1": n1,
        "o1": 0.0,
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


def _signal(n: int = 256, dt: float = 0.004) -> tuple[np.ndarray, np.ndarray]:
    time = np.arange(n, dtype=np.float64) * dt
    signal = np.sin(2.0 * np.pi * 10.0 * time).astype(np.float32)
    return time, signal


def test_window_function_kinds_periodic_and_apply_contract() -> None:
    for kind in ("hann", "hamming", "blackman", "bartlett", "boxcar", "cosine"):
        result = window_function(8, kind=kind)
        assert result.shape == (8,)
        assert result.dtype == np.float32
        assert np.all(np.isfinite(result))

    periodic = window_function(8, kind="hann", periodic=True)
    np.testing.assert_allclose(periodic, np.hanning(9)[:-1].astype(np.float32))
    panel = np.ones((2, 8), dtype=np.float32)
    windowed = apply_window(panel, kind="hann", axis=1)
    assert windowed.shape == panel.shape
    np.testing.assert_allclose(windowed[0], np.hanning(8), atol=1e-7)

    complex_result = apply_window(
        np.ones(8, dtype=np.complex64) * (1.0 + 2.0j),
        kind="hamming",
    )
    assert complex_result.dtype == np.complex64


def test_windowfunc_rsf_generation_application_and_cli(tmp_path: Path) -> None:
    generated = tmp_path / "generated.rsf"
    input_path = tmp_path / "input.rsf"
    applied = tmp_path / "applied.rsf"
    cli_path = tmp_path / "cli.rsf"
    windowfunc_rsf(None, generated, n=16, kind="hann")
    assert read_rsf(generated).data.shape == (16,)

    write_rsf(input_path, np.ones(16, dtype=np.float32), _header(16))
    windowfunc_rsf(input_path, applied, kind="hamming", apply=True)
    loaded = read_rsf(applied)
    assert loaded.header["label1"] == "Time"
    assert loaded.header["window_kind"] == "hamming"

    result = _run_cli(
        "windowfunc",
        ["out=" + str(cli_path), "n1=16", "kind=blackman"],
        tmp_path,
    )
    assert result.returncode == 0, result.stderr
    assert read_rsf(cli_path).header["window_kind"] == "blackman"


def test_psd_peak_scaling_average_and_frequency_header(tmp_path: Path) -> None:
    n = 256
    dt = 0.004
    _, trace = _signal(n, dt)
    panel = np.vstack([trace, 0.5 * trace]).astype(np.float32)
    density = psd(trace, dt, scaling="density")
    spectrum = psd(trace, dt, scaling="spectrum")
    assert int(np.argmax(density)) == pytest.approx(10.0 / (1.0 / (n * dt)), abs=1)
    assert density.dtype == np.float32
    assert spectrum.shape == density.shape

    input_path = tmp_path / "panel.rsf"
    output_path = tmp_path / "psd.rsf"
    write_rsf(input_path, panel, _header(n, 2, d1=dt))
    psd_rsf(input_path, output_path, axis=1, average=True)
    loaded = read_rsf(output_path)
    assert loaded.data.shape == (n // 2 + 1,)
    assert loaded.header["label1"] == "Frequency"
    assert loaded.header["unit1"] == "Hz"
    assert float(loaded.header["d1"]) == pytest.approx(1.0 / (n * dt))


def test_csd_phase_and_complex_dtype() -> None:
    n = 256
    dt = 0.004
    time = np.arange(n) * dt
    left = np.sin(2.0 * np.pi * 10.0 * time).astype(np.float32)
    right = np.cos(2.0 * np.pi * 10.0 * time).astype(np.float32)
    result = csd(left, right, dt, window="boxcar")
    peak = int(np.argmax(np.abs(result)))
    assert result.dtype == np.complex64
    assert abs(np.imag(result[peak])) > abs(np.real(result[peak]))


def test_coherence_identical_signal_and_noise_discrimination() -> None:
    n = 512
    dt = 0.002
    time = np.arange(n) * dt
    rng = np.random.default_rng(12)
    common = np.sin(2.0 * np.pi * 20.0 * time)
    left = (common + 0.15 * rng.standard_normal(n)).astype(np.float32)
    right = (common + 0.15 * rng.standard_normal(n)).astype(np.float32)
    identical = coherence(left, left, dt, nperseg=128, noverlap=64)
    related = coherence(left, right, dt, nperseg=128, noverlap=64)
    peak = int(round(20.0 / (1.0 / (128 * dt))))
    assert identical[peak] == pytest.approx(1.0, abs=1e-6)
    assert related[peak] > 0.8
    assert np.all((related >= 0.0) & (related <= 1.0))


def test_spectrogram_shape_frequency_time_header_and_modes(tmp_path: Path) -> None:
    n = 256
    dt = 0.004
    _, trace = _signal(n, dt)
    panel = np.vstack([trace, trace]).astype(np.float32)
    magnitude = spectrogram(trace, dt, nperseg=64, noverlap=32, mode="magnitude")
    power = spectrogram(trace, dt, nperseg=64, noverlap=32, mode="power")
    assert magnitude.shape == (7, 33)
    assert power.shape == magnitude.shape
    assert np.all(power >= 0.0)

    input_path = tmp_path / "panel.rsf"
    output_path = tmp_path / "spectrogram.rsf"
    write_rsf(input_path, panel, _header(n, 2, d1=dt))
    spectrogram_rsf(
        input_path,
        output_path,
        axis=1,
        nperseg=64,
        noverlap=32,
        mode="power",
    )
    loaded = read_rsf(output_path)
    assert loaded.data.shape == (2, 7, 33)
    assert loaded.header.dimensions == (33, 7, 2)
    assert loaded.header["label1"] == "Frequency"
    assert loaded.header["label2"] == "Window time"
    assert loaded.header["label3"] == "Channel"
    assert float(loaded.header["d1"]) == pytest.approx(1.0 / (64 * dt))
    assert float(loaded.header["d2"]) == pytest.approx(32 * dt)


def test_snr_known_ratio_axis_output_and_complex_support() -> None:
    trace = np.concatenate(
        [np.full(32, 0.1, dtype=np.float32), np.ones(64, dtype=np.float32)]
    )
    panel = np.vstack([trace, 2.0 * trace]).astype(np.float32)
    ratio = snr(
        panel,
        signal_window=(32, 96),
        noise_window=(0, 32),
        axis=1,
        unit="ratio",
    )
    db = snr(
        panel,
        signal_window=(32, 96),
        noise_window=(0, 32),
        axis=1,
        unit="db",
    )
    np.testing.assert_allclose(ratio, [10.0, 10.0])
    np.testing.assert_allclose(db, [20.0, 20.0])
    complex_ratio = snr(
        trace.astype(np.complex64) * (1.0 + 1.0j),
        signal_window=(32, 96),
        noise_window=(0, 32),
        unit="ratio",
    )
    np.testing.assert_allclose(complex_ratio, [10.0])


@pytest.mark.parametrize(
    ("module", "parameters", "two_inputs"),
    [
        ("psd", ["axis=1", "window=hann", "average=n"], False),
        ("csd", ["axis=1", "window=hann"], True),
        (
            "coherence",
            ["axis=1", "window=hann", "nperseg=64", "noverlap=32"],
            True,
        ),
        (
            "spectrogram",
            ["axis=1", "nperseg=64", "noverlap=32", "mode=power"],
            False,
        ),
        ("snr", ["axis=1", "signal=64:192", "noise=0:32", "unit=db"], False),
    ],
)
def test_spectral_cli_subprocess(
    module: str,
    parameters: list[str],
    two_inputs: bool,
    tmp_path: Path,
) -> None:
    n = 256
    dt = 0.004
    _, trace = _signal(n, dt)
    first = tmp_path / f"{module}_a.rsf"
    second = tmp_path / f"{module}_b.rsf"
    output = tmp_path / f"{module}_out.rsf"
    write_rsf(first, trace, _header(n, d1=dt))
    write_rsf(second, (0.8 * trace).astype(np.float32), _header(n, d1=dt))
    args = [str(first)]
    if two_inputs:
        args.append(str(second))
    args.extend(["out=" + str(output), *parameters])
    result = _run_cli(module, args, tmp_path)
    assert result.returncode == 0, result.stderr
    assert output.exists()


def test_rsfdata_spectral_chain_binary_operands_and_inplace(tmp_path: Path) -> None:
    n = 256
    dt = 0.004
    _, trace = _signal(n, dt)
    source = RSFData(trace, _header(n, d1=dt))
    windowed = source.windowfunc(kind="hann")
    density = source.psd()
    cross = source.csd(trace.tolist())
    coherent = source.coherence(
        RSFData(trace.copy(), _header(n, d1=dt)),
        nperseg=64,
        noverlap=32,
    )
    time_frequency = source.spectrogram(nperseg=64, noverlap=32)
    quality = source.snr(signal_window=(64, 192), noise_window=(0, 32))

    assert source.shape == (n,)
    assert windowed.shape == source.shape
    assert density.shape == (n // 2 + 1,)
    assert cross.dtype == np.dtype("complex64")
    assert coherent.shape == (33,)
    assert time_frequency.shape == (7, 33)
    assert quality.shape == (1,)

    other_path = tmp_path / "other.rsf"
    write_rsf(other_path, trace, _header(n, d1=dt))
    from_path = source.csd(other_path)
    np.testing.assert_allclose(from_path.numpy(), cross.numpy())

    returned = source.windowfunc(kind="hamming", inplace=True)
    assert returned is source
    assert source.shape == (n,)


def test_rsf_wrappers_preserve_or_update_shape_header_dtype(tmp_path: Path) -> None:
    n = 128
    dt = 0.002
    _, trace = _signal(n, dt)
    first = tmp_path / "a.rsf"
    second = tmp_path / "b.rsf"
    coherent_path = tmp_path / "coherent.rsf"
    write_rsf(first, trace, _header(n, d1=dt))
    write_rsf(second, trace, _header(n, d1=dt))
    coherence_rsf(
        first,
        second,
        coherent_path,
        nperseg=64,
        noverlap=32,
    )
    loaded = read_rsf(coherent_path)
    assert loaded.data.dtype == np.float32
    assert loaded.data.shape == (33,)
    assert loaded.header["label1"] == "Frequency"
    assert loaded.header["spectral_estimator"] == "segment-averaged coherence"


def test_invalid_parameters_and_nonfinite_contract() -> None:
    with pytest.raises(SpectralQCError, match="window kind"):
        window_function(8, kind="kaiser")  # type: ignore[arg-type]
    with pytest.raises(SpectralQCError, match="real-valued"):
        psd(np.ones(8, dtype=np.complex64), 0.1)
    with pytest.raises(SpectralQCError, match="finite"):
        psd(np.array([1.0, np.nan]), 0.1)
    with pytest.raises(SpectralQCError, match="identical shapes"):
        csd(np.ones(8), np.ones(7), 0.1)
    with pytest.raises(SpectralQCError, match="nperseg"):
        spectrogram(np.ones(8), 0.1, nperseg=9)
    with pytest.raises(SpectralQCError, match="axis 1"):
        spectrogram(np.ones((2, 8)), 0.1, axis=2)
    with pytest.raises(SpectralQCError, match="noise_window"):
        snr(np.ones(8))
