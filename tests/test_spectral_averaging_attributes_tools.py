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
    freqattr_rsf,
    frequency_attributes,
    spectral_normalize,
    spectral_whiten,
    transfer_function,
    transfer_rsf,
    welch_csd,
    welch_psd,
    welch_rsf,
    welchcsd_rsf,
)


ROOT = Path(__file__).resolve().parents[1]


def _header(n1: int, n2: int | None = None, *, d1: float = 0.002) -> RSFHeader:
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
                "o2": 0.0,
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


def _signals(
    n: int = 512,
    dt: float = 0.002,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    time = np.arange(n, dtype=np.float64) * dt
    source = np.sin(2.0 * np.pi * 20.0 * time)
    response = 2.0 * source
    secondary = 0.2 * np.sin(2.0 * np.pi * 60.0 * time)
    return (
        time,
        (source + secondary).astype(np.float32),
        (response + 0.4 * secondary).astype(np.float32),
    )


def test_welch_psd_peak_average_and_dtype() -> None:
    n = 512
    dt = 0.002
    _, source, _ = _signals(n, dt)
    panel = np.vstack([source, 0.5 * source]).astype(np.float32)

    per_trace = welch_psd(
        panel,
        dt,
        axis=1,
        nperseg=128,
        noverlap=64,
        average=False,
    )
    averaged = welch_psd(
        panel,
        dt,
        axis=1,
        nperseg=128,
        noverlap=64,
        average=True,
    )

    assert per_trace.shape == (2, 65)
    assert averaged.shape == (65,)
    assert averaged.dtype == np.float32
    df = 1.0 / (128 * dt)
    assert int(np.argmax(averaged)) == pytest.approx(20.0 / df, abs=1)


def test_welch_csd_complex_phase_and_average() -> None:
    n = 512
    dt = 0.002
    time = np.arange(n) * dt
    left = np.sin(2.0 * np.pi * 20.0 * time).astype(np.float32)
    right = np.cos(2.0 * np.pi * 20.0 * time).astype(np.float32)
    panel_left = np.vstack([left, left])
    panel_right = np.vstack([right, right])

    result = welch_csd(
        panel_left,
        panel_right,
        dt,
        axis=1,
        nperseg=128,
        noverlap=64,
        average=True,
    )

    peak = int(np.argmax(np.abs(result)))
    assert result.shape == (65,)
    assert result.dtype == np.complex64
    assert abs(np.imag(result[peak])) > abs(np.real(result[peak]))


def test_transfer_h1_h2_known_gain() -> None:
    n = 512
    dt = 0.002
    time = np.arange(n) * dt
    source = np.sin(2.0 * np.pi * 20.0 * time).astype(np.float32)
    response = (2.5 * source).astype(np.float32)
    peak = int(round(20.0 / (1.0 / (128 * dt))))

    h1 = transfer_function(
        source,
        response,
        dt,
        nperseg=128,
        noverlap=64,
        method="H1",
    )
    h2 = transfer_function(
        source,
        response,
        dt,
        nperseg=128,
        noverlap=64,
        method="H2",
    )

    assert h1[peak] == pytest.approx(2.5 + 0.0j, abs=1e-5)
    assert h2[peak] == pytest.approx(2.5 + 0.0j, abs=1e-5)


def test_whiten_reduces_spectral_dynamic_range() -> None:
    n = 512
    dt = 1.0 / n
    time = np.arange(n) * dt
    signal = (
        10.0 * np.sin(2.0 * np.pi * 20.0 * time)
        + np.sin(2.0 * np.pi * 60.0 * time)
    ).astype(np.float32)
    whitened = spectral_whiten(signal, dt, smooth=0)
    original_amplitude = np.abs(np.fft.rfft(signal))
    whitened_amplitude = np.abs(np.fft.rfft(whitened))
    original_ratio = original_amplitude[20] / original_amplitude[60]
    whitened_ratio = whitened_amplitude[20] / whitened_amplitude[60]

    assert whitened.shape == signal.shape
    assert whitened.dtype == np.float32
    assert original_ratio > 9.0
    assert whitened_ratio == pytest.approx(1.0, abs=1e-4)


@pytest.mark.parametrize("mode", ["unit_rms", "unit_max"])
def test_specnorm_band_contract(mode: str) -> None:
    n = 256
    dt = 0.004
    _, source, _ = _signals(n, dt)
    normalized = spectral_normalize(
        source,
        dt,
        mode=mode,
        band=(5.0, 80.0),
    )
    spectrum = np.abs(np.fft.rfft(normalized))
    frequencies = np.fft.rfftfreq(n, d=dt)
    selected = spectrum[(frequencies >= 5.0) & (frequencies <= 80.0)]
    statistic = (
        np.sqrt(np.mean(selected * selected))
        if mode == "unit_rms"
        else np.max(selected)
    )

    assert normalized.shape == source.shape
    assert statistic == pytest.approx(1.0, abs=1e-5)


def test_frequency_attributes_known_tone_and_psd_input() -> None:
    n = 512
    dt = 1.0 / n
    time = np.arange(n) * dt
    signal = np.sin(2.0 * np.pi * 32.0 * time).astype(np.float32)
    signal_attrs = frequency_attributes(
        signal,
        dt,
        attrs=("dominant", "centroid", "bandwidth"),
        fmin=10.0,
        fmax=80.0,
    )
    synthetic_psd = np.zeros(129, dtype=np.float32)
    synthetic_psd[24] = 1.0
    psd_attrs = frequency_attributes(
        synthetic_psd,
        1.0,
        input_kind="psd",
        attrs=("dominant", "centroid", "bandwidth"),
    )

    assert signal_attrs.shape == (3,)
    assert signal_attrs[0] == pytest.approx(32.0, abs=1.0)
    assert signal_attrs[1] == pytest.approx(32.0, abs=1.0)
    assert psd_attrs[0] == pytest.approx(24.0)
    assert psd_attrs[1] == pytest.approx(24.0)
    assert psd_attrs[2] == pytest.approx(0.0)


def test_rsf_wrappers_frequency_headers_and_attribute_table(tmp_path: Path) -> None:
    n = 512
    dt = 0.002
    _, source, response = _signals(n, dt)
    panel = np.vstack([source, source]).astype(np.float32)
    source_path = tmp_path / "source.rsf"
    response_path = tmp_path / "response.rsf"
    welch_path = tmp_path / "welch.rsf"
    csd_path = tmp_path / "welchcsd.rsf"
    transfer_path = tmp_path / "transfer.rsf"
    attr_path = tmp_path / "attributes.rsf"
    write_rsf(source_path, panel, _header(n, 2, d1=dt))
    write_rsf(
        response_path,
        np.vstack([response, response]).astype(np.float32),
        _header(n, 2, d1=dt),
    )

    welch_rsf(
        source_path,
        welch_path,
        nperseg=128,
        noverlap=64,
        average=False,
    )
    welchcsd_rsf(
        source_path,
        response_path,
        csd_path,
        nperseg=128,
        noverlap=64,
        average=False,
    )
    transfer_rsf(
        source_path,
        response_path,
        transfer_path,
        nperseg=128,
        noverlap=64,
    )
    freqattr_rsf(source_path, attr_path, fmin=5.0, fmax=80.0)

    welch_loaded = read_rsf(welch_path)
    csd_loaded = read_rsf(csd_path)
    transfer_loaded = read_rsf(transfer_path)
    attr_loaded = read_rsf(attr_path)
    assert welch_loaded.data.shape == (2, 65)
    assert welch_loaded.header["label1"] == "Frequency"
    assert welch_loaded.header["unit1"] == "Hz"
    assert csd_loaded.data.dtype == np.complex64
    assert transfer_loaded.data.dtype == np.complex64
    assert transfer_loaded.header["transfer_method"] == "H1"
    assert attr_loaded.data.shape == (2, 3)
    assert attr_loaded.header.dimensions == (3, 2)
    assert attr_loaded.header["frequency_attributes"] == "dominant,centroid,bandwidth"


@pytest.mark.parametrize(
    ("module", "parameters", "two_inputs"),
    [
        (
            "welch",
            ["nperseg=128", "noverlap=64", "average=y"],
            False,
        ),
        (
            "welchcsd",
            ["nperseg=128", "noverlap=64", "average=y"],
            True,
        ),
        (
            "transfer",
            ["nperseg=128", "noverlap=64", "method=H1"],
            True,
        ),
        ("whiten", ["floor=1e-6", "smooth=5"], False),
        ("specnorm", ["mode=unit_rms", "fmin=5", "fmax=80"], False),
        (
            "freqattr",
            ["attrs=dominant,centroid,bandwidth", "fmin=5", "fmax=80"],
            False,
        ),
    ],
)
def test_c9_cli_subprocess(
    module: str,
    parameters: list[str],
    two_inputs: bool,
    tmp_path: Path,
) -> None:
    n = 512
    dt = 0.002
    _, source, response = _signals(n, dt)
    first = tmp_path / f"{module}_source.rsf"
    second = tmp_path / f"{module}_response.rsf"
    output = tmp_path / f"{module}_out.rsf"
    write_rsf(first, source, _header(n, d1=dt))
    write_rsf(second, response, _header(n, d1=dt))
    args = [str(first)]
    if two_inputs:
        args.append(str(second))
    args.extend(["out=" + str(output), *parameters])

    result = _run_cli(module, args, tmp_path)

    assert result.returncode == 0, result.stderr
    assert output.exists()


def test_rsfdata_c9_chain_binary_operands_and_inplace(tmp_path: Path) -> None:
    n = 512
    dt = 0.002
    _, source_data, response_data = _signals(n, dt)
    source = RSFData(source_data, _header(n, d1=dt))
    response = RSFData(response_data, _header(n, d1=dt))

    density = source.welch(nperseg=128, noverlap=64)
    cross = source.welchcsd(response_data.tolist(), nperseg=128, noverlap=64)
    transfer = source.transfer(response, nperseg=128, noverlap=64)
    whitened = source.whiten(smooth=5)
    normalized = source.specnorm(fmin=5.0, fmax=80.0)
    attributes = source.freqattr(fmin=5.0, fmax=80.0)

    assert density.shape == (65,)
    assert cross.dtype == np.dtype("complex64")
    assert transfer.shape == (65,)
    assert whitened.shape == source.shape
    assert normalized.shape == source.shape
    assert attributes.shape == (3,)

    response_path = tmp_path / "response.rsf"
    write_rsf(response_path, response_data, _header(n, d1=dt))
    from_path = source.transfer(response_path, nperseg=128, noverlap=64)
    np.testing.assert_allclose(from_path.numpy(), transfer.numpy(), atol=1e-6)

    returned = source.whiten(inplace=True)
    assert returned is source
    assert source.shape == (n,)


def test_invalid_c9_parameters_and_nonfinite_contract() -> None:
    data = np.ones(16, dtype=np.float32)
    with pytest.raises(SpectralQCError, match="nperseg"):
        welch_psd(data, 0.1, nperseg=17)
    with pytest.raises(SpectralQCError, match="identical shapes"):
        welch_csd(data, np.ones(15), 0.1)
    with pytest.raises(SpectralQCError, match="H1 or H2"):
        transfer_function(data, data, 0.1, nperseg=8, method="H3")
    with pytest.raises(SpectralQCError, match="phase"):
        spectral_whiten(data, 0.1, phase="zero")
    with pytest.raises(SpectralQCError, match="mode"):
        spectral_normalize(data, 0.1, mode="match_mean")
    with pytest.raises(SpectralQCError, match="finite"):
        spectral_whiten(np.array([1.0, np.nan]), 0.1)
    with pytest.raises(SpectralQCError, match="frequency band"):
        frequency_attributes(data, 0.1, fmin=100.0, fmax=120.0)
    with pytest.raises(SpectralQCError, match="attrs"):
        frequency_attributes(data, 0.1, attrs=("dominant", "unknown"))
