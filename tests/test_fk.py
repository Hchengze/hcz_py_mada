from pathlib import Path

import numpy as np
import pytest

from pymadagascar.cli.fk import main as fk_main
from pymadagascar.cli.fkfilter import main as fkfilter_main
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf
from pymadagascar.seismic.fk import (
    FKError,
    centered_frequency_axis,
    fk_filter,
    fk_spectrum,
    make_fk_mask,
)
from pymadagascar.testing.runner import original_madagascar_available, run_original_madagascar


def _header(nt: int = 128, nx: int = 64, dt: float = 0.004, dx: float = 10.0) -> RSFHeader:
    return RSFHeader(
        {
            "n1": nt,
            "o1": 0.0,
            "d1": dt,
            "label1": "Time",
            "unit1": "s",
            "n2": nx,
            "o2": 0.0,
            "d2": dx,
            "label2": "Offset",
            "unit2": "m",
        }
    )


def _plane_wave(
    *,
    nt: int = 128,
    nx: int = 64,
    dt: float = 0.004,
    dx: float = 10.0,
    frequency: float = 19.53125,
    velocity: float = 1250.0,
) -> np.ndarray:
    time = np.arange(nt, dtype=np.float64) * dt
    offset = np.arange(nx, dtype=np.float64) * dx
    phase = 2.0 * np.pi * frequency * (time.reshape(1, nt) - offset.reshape(nx, 1) / velocity)
    return np.cos(phase).astype(np.float32)


def _rms(data: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(np.asarray(data, dtype=np.float64)))))


def test_single_dipping_event_fk_peak_location(tmp_path: Path) -> None:
    input_path = tmp_path / "dip.rsf"
    output_path = tmp_path / "fk.rsf"
    frequency = 19.53125
    velocity = 1250.0
    data = _plane_wave(frequency=frequency, velocity=velocity)
    write_rsf(input_path, data, _header())

    fk_spectrum(input_path, output_path)
    loaded = read_rsf(output_path)

    freqs = centered_frequency_axis(128, 0.004)
    waves = centered_frequency_axis(64, 10.0)
    positive = freqs > 0.0
    spectrum = loaded.data[:, positive]
    peak = np.unravel_index(int(np.argmax(spectrum)), spectrum.shape)
    peak_wave = waves[peak[0]]
    peak_freq = freqs[positive][peak[1]]

    assert loaded.data.dtype == np.float32
    assert abs(peak_freq - frequency) < 1e-9
    assert abs(abs(peak_wave) - frequency / velocity) < 1e-9


def test_fk_spectrum_updates_frequency_and_wavenumber_header(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "fk.rsf"
    write_rsf(input_path, _plane_wave(), _header())

    fk_spectrum(input_path, output_path)
    loaded = read_rsf(output_path)

    assert loaded.header.dimensions == (128, 64)
    assert loaded.header["label1"] == "Frequency"
    assert loaded.header["unit1"] == "Hz"
    assert loaded.header["o1"] == "-125"
    assert loaded.header["d1"] == "1.95312"
    assert loaded.header["label2"] == "Wavenumber"
    assert loaded.header["unit2"] == "1/m"
    assert loaded.header["fk_label1"] == "Time"
    assert loaded.header["fk_label2"] == "Offset"


def test_fk_spectrum_can_write_complex_spectrum(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "fk_complex.rsf"
    data = _plane_wave()
    write_rsf(input_path, data, _header())

    fk_spectrum(input_path, output_path, amplitude=False)
    loaded = read_rsf(output_path)

    expected = np.fft.fftshift(np.fft.fft2(data.astype(np.complex64), axes=(0, 1)), axes=(0, 1))
    assert loaded.data.dtype == np.complex64
    np.testing.assert_allclose(loaded.data, expected.astype(np.complex64), atol=1e-5)


def test_make_fk_mask_velocity_gate() -> None:
    freqs = np.array([-20.0, 0.0, 20.0], dtype=np.float64)
    waves = np.array([-0.04, -0.016, 0.0, 0.016, 0.04], dtype=np.float64)

    mask = make_fk_mask(freqs, waves, vmin=1000.0, vmax=1500.0)

    assert mask[waves.tolist().index(-0.016), freqs.tolist().index(20.0)] == 1.0
    assert mask[waves.tolist().index(0.04), freqs.tolist().index(20.0)] == 0.0
    assert mask[waves.tolist().index(0.0), freqs.tolist().index(20.0)] == 0.0


def test_fk_filter_passes_selected_velocity_fan(tmp_path: Path) -> None:
    input_path = tmp_path / "mixed.rsf"
    output_path = tmp_path / "filtered.rsf"
    target = _plane_wave(velocity=1250.0)
    reject = _plane_wave(velocity=500.0)
    mixed = (target + 0.5 * reject).astype(np.float32)
    write_rsf(input_path, mixed, _header())

    fk_filter(input_path, output_path, vmin=1000.0, vmax=1500.0)
    loaded = read_rsf(output_path)

    assert loaded.data.shape == mixed.shape
    assert _rms(loaded.data - target) < _rms(mixed - target)
    assert loaded.header["fkfilter_vmin"] == "1000"
    assert loaded.header["fkfilter_vmax"] == "1500"


def test_fk_filter_inverse_keeps_dimensions_and_header(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "filtered.rsf"
    data = _plane_wave()
    write_rsf(input_path, data, _header())

    fk_filter(input_path, output_path, vmin=1000.0, vmax=1500.0)
    loaded = read_rsf(output_path)

    assert loaded.data.shape == data.shape
    assert loaded.header.dimensions == (128, 64)
    assert loaded.header["label1"] == "Time"
    assert loaded.header["label2"] == "Offset"


def test_fk_rejects_non_2d_input(tmp_path: Path) -> None:
    input_path = tmp_path / "trace.rsf"
    output_path = tmp_path / "bad.rsf"
    write_rsf(input_path, np.ones(8, dtype=np.float32), RSFHeader({"n1": 8, "d1": 0.004}))

    with pytest.raises(FKError, match="2D input"):
        fk_spectrum(input_path, output_path)

    assert not output_path.exists()


def test_fk_mask_rejects_bad_velocity_range() -> None:
    with pytest.raises(FKError, match="vmin="):
        make_fk_mask(np.array([1.0]), np.array([0.1]), vmin=2000.0, vmax=1000.0)


def test_fk_cli(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "fk.rsf"
    write_rsf(input_path, _plane_wave(), _header())

    code = fk_main([str(input_path), "out=" + str(output_path), "amplitude=y"])
    loaded = read_rsf(output_path)

    assert code == 0
    assert loaded.data.dtype == np.float32
    assert loaded.header["label1"] == "Frequency"


def test_fk_cli_complex_alias(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "fk_complex.rsf"
    write_rsf(input_path, _plane_wave(), _header())

    code = fk_main([str(input_path), "out=" + str(output_path), "complex=y"])
    loaded = read_rsf(output_path)

    assert code == 0
    assert loaded.data.dtype == np.complex64


def test_fkfilter_cli(tmp_path: Path) -> None:
    input_path = tmp_path / "mixed.rsf"
    output_path = tmp_path / "filtered.rsf"
    target = _plane_wave(velocity=1250.0)
    reject = _plane_wave(velocity=500.0)
    write_rsf(input_path, (target + reject).astype(np.float32), _header())

    code = fkfilter_main([str(input_path), "out=" + str(output_path), "vmin=1000", "vmax=1500"])
    loaded = read_rsf(output_path)

    assert code == 0
    assert loaded.data.shape == target.shape
    assert _rms(loaded.data - target) < _rms(reject)


def test_fkfilter_cli_reports_missing_velocity(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "bad.rsf"
    write_rsf(input_path, _plane_wave(), _header())

    code = fkfilter_main([str(input_path), "out=" + str(output_path)])

    assert code == 2
    assert "vmin= or vmax=" in capsys.readouterr().err
    assert not output_path.exists()


def test_original_sfdipfilter_shape_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfdipfilter"):
        pytest.skip("Original Madagascar sfdipfilter is not installed")

    input_path = tmp_path / "input.rsf"
    fk_path = tmp_path / "fk.rsf"
    original_path = tmp_path / "original.rsf"
    write_rsf(input_path, _plane_wave(), _header())
    fk_spectrum(input_path, fk_path, amplitude=False)

    run_original_madagascar(
        [
            "sfdipfilter",
            "in=fk.rsf",
            "out=original.rsf",
            "v1=1000",
            "v2=1100",
            "v3=1500",
            "v4=1600",
            "pass=y",
        ],
        cwd=tmp_path,
        require_program="sfdipfilter",
    )
    loaded = read_rsf(original_path)

    assert loaded.data.shape == (64, 128)
