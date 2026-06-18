from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from pymadagascar import RSFData
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf
from pymadagascar.signal.fir import (
    FIRFilterError,
    band_energy,
    bandenergy_rsf,
    filter_bank,
    filterbank_rsf,
    filtfilt_rsf,
    fir_filter,
    firfilter_rsf,
    firwin,
    firwin_rsf,
    freq_response,
    freqz_rsf,
    zero_phase_fir_filter,
)


ROOT = Path(__file__).resolve().parents[1]


def _header(n1: int, n2: int | None = None, *, dt: float = 0.004) -> RSFHeader:
    values: dict[str, object] = {
        "n1": n1,
        "o1": 0.0,
        "d1": dt,
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


def _signal(n: int = 512, dt: float = 0.004) -> np.ndarray:
    time = np.arange(n, dtype=np.float64) * dt
    return (
        np.sin(2.0 * np.pi * 10.0 * time)
        + 0.7 * np.sin(2.0 * np.pi * 60.0 * time)
    ).astype(np.float32)


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


@pytest.mark.parametrize(
    ("cutoff", "pass_zero", "pass_frequency", "stop_frequency"),
    [
        (20.0, True, 5.0, 80.0),
        (20.0, False, 80.0, 5.0),
        ((15.0, 35.0), False, 25.0, 70.0),
        ((15.0, 35.0), True, 5.0, 25.0),
    ],
)
def test_firwin_filter_kinds(
    cutoff: float | tuple[float, float],
    pass_zero: bool,
    pass_frequency: float,
    stop_frequency: float,
) -> None:
    taps = firwin(
        101,
        cutoff,
        fs=200.0,
        pass_zero=pass_zero,
        window="hamming",
    )
    frequencies, response = freq_response(taps, fs=200.0, nfft=4096)
    pass_gain = abs(response[np.argmin(abs(frequencies - pass_frequency))])
    stop_gain = abs(response[np.argmin(abs(frequencies - stop_frequency))])

    assert taps.shape == (101,)
    assert taps.dtype == np.float64
    assert pass_gain > 0.85
    assert stop_gain < 0.08


def test_firwin_normalized_dtype_and_even_constraints() -> None:
    taps = firwin(32, (0.2, 0.5), pass_zero=False, dtype=np.float32)
    assert taps.dtype == np.float32
    with pytest.raises(FIRFilterError, match="odd numtaps"):
        firwin(32, 0.4, pass_zero=False)
    with pytest.raises(FIRFilterError, match="strictly between"):
        firwin(31, 1.0)


def test_fir_filter_attenuates_high_tone_and_supports_complex() -> None:
    n = 512
    dt = 0.004
    signal = _signal(n, dt)
    taps = firwin(81, 25.0, fs=1.0 / dt, dtype=np.float32)
    filtered = fir_filter(signal, taps)
    before = abs(np.fft.rfft(signal))
    after = abs(np.fft.rfft(filtered))
    frequencies = np.fft.rfftfreq(n, d=dt)
    low = np.argmin(abs(frequencies - 10.0))
    high = np.argmin(abs(frequencies - 60.0))

    assert filtered.shape == signal.shape
    assert filtered.dtype == np.float32
    assert after[low] / before[low] > 0.85
    assert after[high] / before[high] < 0.08

    complex_result = fir_filter(
        signal.astype(np.complex64) * (1.0 + 1.0j),
        taps,
    )
    assert complex_result.dtype == np.complex64


def test_filtfilt_impulse_response_is_centered_and_symmetric() -> None:
    data = np.zeros(401, dtype=np.float32)
    data[200] = 1.0
    taps = firwin(41, 0.35, dtype=np.float32)
    result = zero_phase_fir_filter(data, taps, pad=True)
    neighborhood = result[160:241]

    assert result.shape == data.shape
    assert int(np.argmax(result)) == 200
    np.testing.assert_allclose(neighborhood, neighborhood[::-1], atol=2e-6)


def test_freq_response_and_rsf_header(tmp_path: Path) -> None:
    taps_path = tmp_path / "taps.rsf"
    response_path = tmp_path / "response.rsf"
    firwin_rsf(
        taps_path,
        numtaps=51,
        cutoff=20.0,
        fs=200.0,
        pass_zero=True,
    )
    freqz_rsf(taps_path, response_path, fs=200.0, nfft=512, mode="amplitude")
    loaded = read_rsf(response_path)

    assert loaded.data.shape == (257,)
    assert loaded.header["label1"] == "Frequency"
    assert loaded.header["unit1"] == "Hz"
    assert float(loaded.header["d1"]) == pytest.approx(200.0 / 512)
    assert loaded.data[0] == pytest.approx(1.0, abs=1e-6)


def test_band_energy_and_filter_bank_known_tones() -> None:
    n = 512
    dt = 0.004
    signal = _signal(n, dt)
    panel = np.vstack([signal, 0.5 * signal]).astype(np.float32)
    bands = ((5.0, 15.0), (50.0, 70.0))

    per_trace = band_energy(panel, dt, bands, mode="rms", average=False)
    averaged = band_energy(panel, dt, bands, mode="rms", average=True)
    bank = filter_bank(panel, dt, bands, numtaps=81)

    assert per_trace.shape == (2, 2)
    assert averaged.shape == (2,)
    assert averaged[0] > averaged[1]
    assert bank.shape == (2, 2, n)
    low_bank = abs(np.fft.rfft(bank[0, 0]))
    high_bank = abs(np.fft.rfft(bank[1, 0]))
    frequencies = np.fft.rfftfreq(n, d=dt)
    low_bin = np.argmin(abs(frequencies - 10.0))
    high_bin = np.argmin(abs(frequencies - 60.0))
    assert low_bank[low_bin] > 10.0 * low_bank[high_bin]
    assert high_bank[high_bin] > 10.0 * high_bank[low_bin]


def test_rsf_wrappers_shape_and_band_headers(tmp_path: Path) -> None:
    n = 512
    dt = 0.004
    panel = np.vstack([_signal(n, dt), _signal(n, dt)]).astype(np.float32)
    input_path = tmp_path / "input.rsf"
    taps_path = tmp_path / "taps.rsf"
    filtered_path = tmp_path / "filtered.rsf"
    zero_path = tmp_path / "zero_phase.rsf"
    energy_path = tmp_path / "energy.rsf"
    bank_path = tmp_path / "bank.rsf"
    write_rsf(input_path, panel, _header(n, 2, dt=dt))
    firwin_rsf(taps_path, numtaps=81, cutoff=25.0, fs=1.0 / dt)

    firfilter_rsf(input_path, taps_path, filtered_path)
    filtfilt_rsf(input_path, taps_path, zero_path)
    bandenergy_rsf(
        input_path,
        energy_path,
        bands="5:15,50:70",
        average=False,
    )
    filterbank_rsf(
        input_path,
        bank_path,
        bands="5:15,50:70",
        numtaps=81,
    )

    filtered = read_rsf(filtered_path)
    zero_phase = read_rsf(zero_path)
    energy = read_rsf(energy_path)
    bank = read_rsf(bank_path)
    assert filtered.data.shape == panel.shape
    assert zero_phase.data.shape == panel.shape
    assert filtered.header["label1"] == "Time"
    assert energy.data.shape == (2, 2)
    assert energy.header.dimensions == (2, 2)
    assert energy.header["label1"] == "Frequency band"
    assert bank.data.shape == (2, 2, n)
    assert bank.header.dimensions == (n, 2, 2)
    assert bank.header["label3"] == "Frequency band"


@pytest.mark.parametrize(
    ("module", "kind"),
    [
        ("firwin", "firwin"),
        ("firfilter", "binary"),
        ("filtfilt", "binary"),
        ("freqz", "freqz"),
        ("bandenergy", "unary"),
        ("filterbank", "unary"),
    ],
)
def test_c10_cli_subprocess(module: str, kind: str, tmp_path: Path) -> None:
    n = 512
    dt = 0.004
    input_path = tmp_path / "input.rsf"
    taps_path = tmp_path / "taps.rsf"
    output_path = tmp_path / f"{module}.rsf"
    write_rsf(input_path, _signal(n, dt), _header(n, dt=dt))
    firwin_rsf(taps_path, numtaps=81, cutoff=25.0, fs=1.0 / dt)

    if kind == "firwin":
        args = [
            "out=" + str(output_path),
            "numtaps=81",
            "cutoff=25",
            f"fs={1.0 / dt:g}",
        ]
    elif kind == "binary":
        args = [str(input_path), str(taps_path), "out=" + str(output_path)]
    elif kind == "freqz":
        args = [
            str(taps_path),
            "out=" + str(output_path),
            f"fs={1.0 / dt:g}",
            "mode=amplitude",
        ]
    else:
        args = [
            str(input_path),
            "out=" + str(output_path),
            "bands=5:15,50:70",
        ]
        if module == "filterbank":
            args.append("numtaps=81")

    result = _run_cli(module, args, tmp_path)

    assert result.returncode == 0, result.stderr
    assert output_path.exists()


@pytest.mark.parametrize("operand_kind", ["rsfdata", "ndarray", "list", "path"])
def test_rsfdata_fir_operands_and_chain(
    operand_kind: str,
    tmp_path: Path,
) -> None:
    n = 512
    dt = 0.004
    data = _signal(n, dt)
    taps = firwin(81, 25.0, fs=1.0 / dt, dtype=np.float32)
    source = RSFData(data, _header(n, dt=dt))
    if operand_kind == "rsfdata":
        operand: object = RSFData(
            taps,
            RSFHeader({"n1": taps.size, "d1": dt, "o1": -40 * dt}),
        )
    elif operand_kind == "ndarray":
        operand = taps
    elif operand_kind == "list":
        operand = taps.tolist()
    else:
        path = tmp_path / "operand.rsf"
        write_rsf(path, taps, RSFHeader({"n1": taps.size, "d1": dt}))
        operand = path

    filtered = source.firfilter(operand)
    zero_phase = source.filtfilt(operand)
    energy = source.bandenergy(bands="5:15,50:70")
    bank = source.filterbank(bands="5:15,50:70", numtaps=81)

    assert filtered.shape == source.shape
    assert zero_phase.shape == source.shape
    assert energy.shape == (2,)
    assert bank.shape == (2, n)
    np.testing.assert_array_equal(source.numpy(), data)

    returned = source.firfilter(operand, inplace=True)
    assert returned is source
    assert source.shape == (n,)


def test_invalid_parameters_nonfinite_and_complex_contract() -> None:
    data = np.ones(32, dtype=np.float32)
    with pytest.raises(FIRFilterError, match="one or two"):
        firwin(31, (0.1, 0.2, 0.3))
    with pytest.raises(FIRFilterError, match="tap count"):
        fir_filter(data, np.ones(33))
    with pytest.raises(FIRFilterError, match="mode"):
        fir_filter(data, [1.0], mode="full")  # type: ignore[arg-type]
    with pytest.raises(FIRFilterError, match="finite"):
        zero_phase_fir_filter(np.array([1.0, np.nan]), [1.0])
    with pytest.raises(FIRFilterError, match="real-valued"):
        band_energy(data.astype(np.complex64), 0.1, "1:2")
    with pytest.raises(FIRFilterError, match="Nyquist"):
        filter_bank(data, 0.1, "1:5", numtaps=7)
