"""S4-3 FK prototype source-aligned contract tests."""

from __future__ import annotations

import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import tempfile

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
from pymadagascar.testing.seismic_fixtures import make_plane_wave_panel_fixture


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT.parent / "src-master"
WORKFLOWS_DIR = ROOT / "examples" / "my_workflows"
WORKFLOW = WORKFLOWS_DIR / "seismic_fk_contract_workflow.py"

NT = 256
NX = 64
DT = 0.004
DX = 10.0
FREQUENCY_BIN = 20
TARGET_K_BIN = 8
REJECT_K_BIN = 20
FREQUENCY = FREQUENCY_BIN / (NT * DT)
TARGET_K = TARGET_K_BIN / (NX * DX)
REJECT_K = REJECT_K_BIN / (NX * DX)
TARGET_VELOCITY = FREQUENCY / TARGET_K
REJECT_VELOCITY = FREQUENCY / REJECT_K


def test_madagascar_fk_and_dipfilter_source_paths_are_audited() -> None:
    direct_fk = list(SOURCE_ROOT.rglob("Mfk.c"))
    assert direct_fk == []

    dipfilter = SOURCE_ROOT / "system" / "generic" / "Mdipfilter.c"
    assert dipfilter.is_file()
    source = dipfilter.read_text(encoding="utf-8", errors="replace")
    assert 'sf_histint(in,"n1",&nw)' in source
    assert 'sf_histfloat(in,"d1",&dw)' in source
    assert 'sf_getfloat("v1",&v1)' in source
    assert 'sf_getbool("pass",&pass)' in source
    assert "vel = w/x" in source

    related = {
        "Mfkamo.c": SOURCE_ROOT / "system" / "seismic" / "Mfkamo.c",
        "Mfkdmo.c": SOURCE_ROOT / "system" / "seismic" / "Mfkdmo.c",
        "Mfkgdmo.c": SOURCE_ROOT / "system" / "seismic" / "Mfkgdmo.c",
    }
    for path in related.values():
        assert path.is_file(), path
    assert "Azimuth Move-Out" in related["Mfkamo.c"].read_text(
        encoding="utf-8",
        errors="replace",
    )
    assert "Offset continuation" in related["Mfkdmo.c"].read_text(
        encoding="utf-8",
        errors="replace",
    )
    assert "Gardner" in related["Mfkgdmo.c"].read_text(
        encoding="utf-8",
        errors="replace",
    )


def test_current_fk_accepts_s1_plane_wave_fixture(tmp_path: Path) -> None:
    input_path = tmp_path / "s1_plane_wave.rsf"
    output_path = tmp_path / "fk.rsf"
    fixture = make_plane_wave_panel_fixture(path=input_path)

    fk_spectrum(input_path, output_path)
    loaded = read_rsf(output_path)

    assert fixture.header["label1"] == "Time"
    assert fixture.header["coordinate_sampling"] == "regular"
    assert loaded.data.shape == fixture.data.shape
    assert loaded.header["label1"] == "Frequency"
    assert loaded.header["label2"] == "Wavenumber"
    assert loaded.header["fk_reference_source"] == "../src-master/system/generic/Mdipfilter.c"
    assert loaded.header["fk_madagascar_equivalence"] == "no_direct_Mfk_transform_found"
    assert np.isfinite(loaded.data).all()


def test_fk_peak_location_near_analytic_expectation(tmp_path: Path) -> None:
    input_path = tmp_path / "positive_slope.rsf"
    output_path = tmp_path / "fk.rsf"
    write_rsf(input_path, _plane_wave(TARGET_K_BIN, sign=1), _header())

    fk_spectrum(input_path, output_path)
    peak_frequency, peak_wavenumber, _ = _positive_frequency_peak(read_rsf(output_path))

    assert peak_frequency == pytest.approx(FREQUENCY, abs=0.5 / (NT * DT))
    assert peak_wavenumber == pytest.approx(TARGET_K, abs=0.5 / (NX * DX))


def test_positive_and_negative_slopes_are_separated_in_fk(tmp_path: Path) -> None:
    positive_input = tmp_path / "positive.rsf"
    negative_input = tmp_path / "negative.rsf"
    positive_output = tmp_path / "positive_fk.rsf"
    negative_output = tmp_path / "negative_fk.rsf"
    write_rsf(positive_input, _plane_wave(TARGET_K_BIN, sign=1), _header())
    write_rsf(negative_input, _plane_wave(TARGET_K_BIN, sign=-1), _header())

    fk_spectrum(positive_input, positive_output)
    fk_spectrum(negative_input, negative_output)
    positive_peak = _positive_frequency_peak(read_rsf(positive_output))
    negative_peak = _positive_frequency_peak(read_rsf(negative_output))

    assert positive_peak[0] == pytest.approx(FREQUENCY, abs=0.5 / (NT * DT))
    assert negative_peak[0] == pytest.approx(FREQUENCY, abs=0.5 / (NT * DT))
    assert positive_peak[1] == pytest.approx(TARGET_K, abs=0.5 / (NX * DX))
    assert negative_peak[1] == pytest.approx(-TARGET_K, abs=0.5 / (NX * DX))


def test_fk_filter_preserves_target_slope_and_suppresses_reject_slope(tmp_path: Path) -> None:
    input_path = tmp_path / "mixed.rsf"
    output_path = tmp_path / "filtered.rsf"
    target = _plane_wave(TARGET_K_BIN, sign=1, amplitude=1.0)
    reject = _plane_wave(REJECT_K_BIN, sign=-1, amplitude=0.5)
    mixed = (target + reject).astype(np.float32)
    write_rsf(input_path, mixed, _header())

    fk_filter(input_path, output_path, vmin=1200.0, vmax=1800.0)
    loaded = read_rsf(output_path)
    before = _basis_coefficients(mixed, target, reject)
    after = _basis_coefficients(loaded.data, target, reject)

    assert after[0] / before[0] >= 0.90
    assert abs(after[1]) / abs(before[1]) <= 0.20
    assert _rms(loaded.data - target) < _rms(mixed - target)
    assert loaded.header["fkfilter_reference_source"] == "../src-master/system/generic/Mdipfilter.c"
    assert loaded.header["fkfilter_madagascar_equivalence"] == "not_sfdipfilter_clone"
    assert loaded.header["fkfilter_mask_velocity"] == "abs_frequency_over_abs_wavenumber"


def test_fk_filter_reject_only_slope_is_attenuated(tmp_path: Path) -> None:
    input_path = tmp_path / "reject_only.rsf"
    output_path = tmp_path / "filtered.rsf"
    reject = _plane_wave(REJECT_K_BIN, sign=-1)
    write_rsf(input_path, reject, _header())

    fk_filter(input_path, output_path, vmin=1200.0, vmax=1800.0)
    loaded = read_rsf(output_path)

    assert _rms(loaded.data) / _rms(reject) <= 0.20


def test_fk_output_shape_header_dtype_and_finiteness(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    amplitude_path = tmp_path / "fk_amp.rsf"
    complex_path = tmp_path / "fk_complex.rsf"
    filtered_path = tmp_path / "filtered.rsf"
    data = _plane_wave(TARGET_K_BIN, sign=1)
    write_rsf(input_path, data, _header())

    fk_spectrum(input_path, amplitude_path, amplitude=True)
    fk_spectrum(input_path, complex_path, amplitude=False)
    fk_filter(input_path, filtered_path, vmin=1200.0, vmax=1800.0)

    amplitude = read_rsf(amplitude_path)
    complex_spectrum = read_rsf(complex_path)
    filtered = read_rsf(filtered_path)
    assert amplitude.data.shape == data.shape
    assert amplitude.data.dtype == np.float32
    assert amplitude.header["unit1"] == "Hz"
    assert amplitude.header["unit2"] == "1/m"
    assert amplitude.header["fk_algorithm"] == "numpy_fft2_centered"
    assert complex_spectrum.data.dtype == np.complex64
    assert complex_spectrum.header["fk_amplitude_output"] == "n"
    assert filtered.data.shape == data.shape
    assert filtered.data.dtype == np.float32
    assert filtered.header["label1"] == "Time"
    assert filtered.header["label2"] == "Channel X"
    assert np.isfinite(amplitude.data).all()
    assert np.isfinite(complex_spectrum.data).all()
    assert np.isfinite(filtered.data).all()


@pytest.mark.parametrize(
    ("header_updates", "message"),
    [
        ({"d1": 0.0}, "d1="),
        ({"d1": np.nan}, "d1="),
        ({"o1": np.inf}, "o1="),
        ({"d2": 0.0}, "d2="),
        ({"d2": np.nan}, "d2="),
        ({"o2": -np.inf}, "o2="),
    ],
)
def test_fk_rejects_invalid_time_or_spatial_axis(
    tmp_path: Path,
    header_updates: dict[str, float],
    message: str,
) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "bad.rsf"
    header = _header()
    for key, value in header_updates.items():
        header[key] = value
    write_rsf(input_path, _plane_wave(TARGET_K_BIN, sign=1), header)

    with pytest.raises(FKError, match=message):
        fk_spectrum(input_path, output_path)
    assert not output_path.exists()


@pytest.mark.parametrize("bad_value", [np.nan, np.inf, -np.inf])
def test_fk_rejects_nan_or_inf_input(tmp_path: Path, bad_value: float) -> None:
    input_path = tmp_path / "input.rsf"
    spectrum_path = tmp_path / "fk.rsf"
    filtered_path = tmp_path / "filtered.rsf"
    data = _plane_wave(TARGET_K_BIN, sign=1)
    data[0, 0] = bad_value
    write_rsf(input_path, data, _header())

    with pytest.raises(FKError, match="finite input samples"):
        fk_spectrum(input_path, spectrum_path)
    with pytest.raises(FKError, match="finite input samples"):
        fk_filter(input_path, filtered_path, vmin=1200.0, vmax=1800.0)
    assert not spectrum_path.exists()
    assert not filtered_path.exists()


def test_fk_rejects_complex_input_with_nonfinite_component(tmp_path: Path) -> None:
    input_path = tmp_path / "complex_bad.rsf"
    output_path = tmp_path / "fk.rsf"
    data = _plane_wave(TARGET_K_BIN, sign=1).astype(np.complex64)
    data[1, 1] = complex(1.0, np.inf)
    write_rsf(input_path, data, _header())

    with pytest.raises(FKError, match="finite input samples"):
        fk_spectrum(input_path, output_path)


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"vmin": np.nan, "vmax": 1800.0}, "vmin= must be finite"),
        ({"vmin": 1200.0, "vmax": np.inf}, "vmax= must be finite"),
        ({"vmin": 1200.0, "vmax": 1800.0, "taper": np.nan}, "taper= must be finite"),
        ({"vmin": -1.0, "vmax": 1800.0}, "vmin= must be non-negative"),
        ({"vmin": 2000.0, "vmax": 1800.0}, "vmin= must be smaller"),
    ],
)
def test_fk_mask_rejects_invalid_parameters(
    kwargs: dict[str, float],
    message: str,
) -> None:
    with pytest.raises(FKError, match=message):
        make_fk_mask(
            centered_frequency_axis(NT, DT),
            centered_frequency_axis(NX, DX),
            **kwargs,
        )


def test_fk_mask_rejects_nonfinite_frequency_or_wavenumber() -> None:
    with pytest.raises(FKError, match="frequencies must be finite"):
        make_fk_mask(np.array([0.0, np.nan]), np.array([0.1]), vmin=1.0)
    with pytest.raises(FKError, match="wavenumbers must be finite"):
        make_fk_mask(np.array([1.0]), np.array([np.inf]), vmin=1.0)


def test_centered_frequency_axis_rejects_bad_sampling() -> None:
    with pytest.raises(FKError, match="finite and positive"):
        centered_frequency_axis(8, np.nan)
    with pytest.raises(FKError, match="finite and positive"):
        centered_frequency_axis(8, 0.0)


def test_existing_fk_and_fkfilter_cli_still_work(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    spectrum_path = tmp_path / "fk.rsf"
    filtered_path = tmp_path / "filtered.rsf"
    data = _plane_wave(TARGET_K_BIN, sign=1)
    write_rsf(input_path, data, _header())

    fk_code = fk_main([str(input_path), "out=" + str(spectrum_path), "amplitude=y"])
    filter_code = fkfilter_main(
        [
            str(input_path),
            "out=" + str(filtered_path),
            "vmin=1200",
            "vmax=1800",
        ]
    )

    assert fk_code == 0
    assert filter_code == 0
    assert read_rsf(spectrum_path).header["label1"] == "Frequency"
    assert read_rsf(filtered_path).data.shape == data.shape


def test_s4_3_workflow_report_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.syspath_prepend(str(WORKFLOWS_DIR))
    namespace = runpy.run_path(str(WORKFLOW), run_name="s4_fk_contract_test")
    report = namespace["run_pipeline"](tmp_path)

    assert report["workflow"] == "seismic_fk_contract"
    assert report["stage"] == "S4-3"
    assert report["status"] == "prototype_contract_regression"
    assert report["fixture"] == "regular_plane_wave_panel"
    assert report["madagascar_reference"] == "../src-master/system/generic/Mdipfilter.c"
    assert report["direct_mfk_source_found"] is False
    assert report["checks"]["overall_pass"] is True
    assert report["checks"]["peak_frequency_near_expected"] is True
    assert report["checks"]["peak_wavenumber_near_expected"] is True
    assert report["checks"]["target_slope_preserved"] is True
    assert report["checks"]["reject_slope_suppressed"] is True
    assert report["metrics"]["peak_frequency_hz"] == pytest.approx(
        FREQUENCY,
        abs=0.5 / (NT * DT),
    )
    assert report["metrics"]["peak_wavenumber_1_per_m"] == pytest.approx(
        TARGET_K,
        abs=0.5 / (NX * DX),
    )
    assert report["metrics"]["finite_fraction"] == pytest.approx(1.0)
    assert report["metrics"]["header_axis_ok"] is True
    assert report["contracts"]["segy_trace_header"] == "out_of_scope"

    report_text = (tmp_path / "s4_fk_qc_report.json").read_text(encoding="utf-8")
    assert str(tmp_path) not in report_text
    assert json.loads(report_text) == report


def test_s4_3_workflow_subprocess_is_deterministic_and_does_not_pollute_repo(
    tmp_path: Path,
) -> None:
    before = _example_files()
    out1 = tmp_path / "run1"
    out2 = tmp_path / "run2"

    _run_workflow_subprocess(out1)
    _run_workflow_subprocess(out2)

    assert (out1 / "s4_fk_qc_report.json").read_bytes() == (
        out2 / "s4_fk_qc_report.json"
    ).read_bytes()
    assert {
        "s4_fk_raw_panel.rsf",
        "s4_fk_spectrum.rsf",
        "s4_fk_filtered_panel.rsf",
        "s4_fk_spectrum_quicklook.png",
        "s4_fk_qc_report.json",
    } <= {path.name for path in out1.iterdir()}
    assert _example_files() == before


def test_s4_3_workflow_default_output_is_system_temporary() -> None:
    completed = _run_workflow_subprocess(None)
    output_dir = _parse_output_dir(completed.stdout)
    try:
        assert output_dir.parent == Path(tempfile.gettempdir())
        assert (output_dir / "s4_fk_qc_report.json").is_file()
    finally:
        if output_dir.parent == Path(tempfile.gettempdir()) and output_dir.exists():
            shutil.rmtree(output_dir)


def test_s4_3_adds_no_cli_or_console_script() -> None:
    assert not (ROOT / "pymadagascar" / "cli" / "fk_contract.py").exists()
    assert not (ROOT / "pymadagascar" / "cli" / "seismic_fk_contract.py").exists()
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "seismic-fk-contract" not in pyproject
    assert "seismic_fk_contract" not in pyproject


def test_s4_3_has_no_original_madagascar_or_cpp_dependency() -> None:
    sources = [
        ROOT / "pymadagascar" / "seismic" / "fk.py",
        WORKFLOW,
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in sources)
    assert "pymadagascar.testing.runner" not in combined
    assert "run_original_madagascar" not in combined
    assert "original_madagascar_available" not in combined
    assert "pymadagascar.hybrid" not in combined
    assert "_core" not in combined


def _header() -> RSFHeader:
    return RSFHeader(
        {
            "n1": NT,
            "o1": 0.0,
            "d1": DT,
            "label1": "Time",
            "unit1": "s",
            "n2": NX,
            "o2": 0.0,
            "d2": DX,
            "label2": "Channel X",
            "unit2": "m",
            "axis2_role": "regular_spatial_coordinate",
            "coordinate_sampling": "regular",
        }
    )


def _plane_wave(
    wavenumber_bin: int,
    *,
    sign: int,
    amplitude: float = 1.0,
) -> np.ndarray:
    time = DT * np.arange(NT, dtype=np.float64)
    space = DX * np.arange(NX, dtype=np.float64)
    wavenumber = wavenumber_bin / (NX * DX)
    phase = 2.0 * np.pi * (
        FREQUENCY * time.reshape(1, NT)
        + sign * wavenumber * space.reshape(NX, 1)
    )
    return (amplitude * np.cos(phase)).astype(np.float32)


def _positive_frequency_peak(item) -> tuple[float, float, float]:
    frequencies = _axis_values(item, 1)
    wavenumbers = _axis_values(item, 2)
    positive = frequencies > 0.0
    spectrum = np.asarray(item.data[:, positive], dtype=np.float64)
    peak = np.unravel_index(int(np.argmax(spectrum)), spectrum.shape)
    return (
        float(frequencies[positive][peak[1]]),
        float(wavenumbers[peak[0]]),
        float(spectrum[peak]),
    )


def _axis_values(item, axis: int) -> np.ndarray:
    origin = float(item.header[f"o{axis}"])
    spacing = float(item.header[f"d{axis}"])
    count = int(item.header[f"n{axis}"])
    return origin + spacing * np.arange(count, dtype=np.float64)


def _basis_coefficients(data: np.ndarray, target: np.ndarray, reject: np.ndarray) -> tuple[float, float]:
    design = np.stack([target.ravel(), reject.ravel()], axis=1).astype(np.float64)
    coefficients = np.linalg.lstsq(design, np.asarray(data, dtype=np.float64).ravel(), rcond=None)[0]
    return float(coefficients[0]), float(coefficients[1])


def _rms(data: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(np.asarray(data, dtype=np.float64)))))


def _example_files() -> set[str]:
    return {str(path.relative_to(ROOT)) for path in WORKFLOWS_DIR.rglob("*") if path.is_file()}


def _run_workflow_subprocess(output_dir: Path | None) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(WORKFLOW)]
    if output_dir is not None:
        command.append(str(output_dir))
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        command,
        cwd=WORKFLOWS_DIR,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )


def _parse_output_dir(stdout: str) -> Path:
    for line in stdout.splitlines():
        if line.startswith("output_dir="):
            return Path(line.removeprefix("output_dir=")).resolve()
    raise AssertionError(f"workflow did not print output_dir=: {stdout}")
