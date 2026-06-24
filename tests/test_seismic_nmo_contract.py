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

from pymadagascar.cli.nmo import main as nmo_main
from pymadagascar.io.rsf import read_rsf, write_rsf
from pymadagascar.seismic.nmo import NMOError, nmo_correct
from pymadagascar.testing.seismic_fixtures import make_hyperbolic_gather_fixture
from pymadagascar.testing.seismic_metrics import compute_trace_metrics


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
WORKFLOWS = EXAMPLES / "my_workflows"
WORKFLOW = WORKFLOWS / "seismic_nmo_contract_workflow.py"
TRUE_VELOCITY = 2200.0
WRONG_VELOCITY = 1700.0
SIGNAL_WINDOW = (95, 135)
PICK_WINDOW = (95, 145)
NOISE_WINDOW = (300, 450)


def test_nmo_accepts_s1_fixture_and_flattens_known_event(tmp_path: Path) -> None:
    raw_path = tmp_path / "raw.rsf"
    output_path = tmp_path / "nmo.rsf"
    raw = make_hyperbolic_gather_fixture(path=raw_path)

    nmo_correct(
        raw_path,
        TRUE_VELOCITY,
        output_path,
        half=False,
        stretch=None,
    )
    corrected = read_rsf(output_path)

    assert corrected.data.shape == raw.data.shape == (21, 512)
    assert _event_pick_std(corrected.data) <= 0.003
    assert _event_pick_std(corrected.data) < 0.35 * _event_pick_std(raw.data)
    assert np.all(np.isfinite(corrected.data))


def test_correct_velocity_improves_stack_and_beats_wrong_velocity(
    tmp_path: Path,
) -> None:
    raw_path = tmp_path / "raw.rsf"
    correct_path = tmp_path / "correct.rsf"
    wrong_path = tmp_path / "wrong.rsf"
    raw = make_hyperbolic_gather_fixture(path=raw_path)
    nmo_correct(raw_path, TRUE_VELOCITY, correct_path, half=False, stretch=None)
    nmo_correct(raw_path, WRONG_VELOCITY, wrong_path, half=False, stretch=None)
    corrected = read_rsf(correct_path)
    wrong = read_rsf(wrong_path)

    pre_stack = np.mean(raw.data, axis=0)
    post_stack = np.mean(corrected.data, axis=0)
    wrong_stack = np.mean(wrong.data, axis=0)
    pre_peak = _stack_peak(pre_stack)
    post_peak = _stack_peak(post_stack)
    wrong_peak = _stack_peak(wrong_stack)
    post_metrics = compute_trace_metrics(
        post_stack,
        dt=0.004,
        signal_window=SIGNAL_WINDOW,
        noise_window=NOISE_WINDOW,
    )

    assert post_peak[1] >= 2.0 * pre_peak[1]
    assert post_peak[1] >= 1.8 * wrong_peak[1]
    assert _event_pick_std(wrong.data) >= 2.0 * _event_pick_std(corrected.data)
    assert post_peak[0] * 0.004 == pytest.approx(0.45, abs=0.006)
    assert post_metrics["finite_fraction"] == 1.0


def test_nmo_preserves_s1_axes_dtype_and_records_prototype_metadata(
    tmp_path: Path,
) -> None:
    raw_path = tmp_path / "raw.rsf"
    output_path = tmp_path / "nmo.rsf"
    raw = make_hyperbolic_gather_fixture(dtype=np.float64, path=raw_path)
    nmo_correct(raw_path, TRUE_VELOCITY, output_path, half=False, stretch=None)
    corrected = read_rsf(output_path)

    for key in (
        "n1",
        "o1",
        "d1",
        "label1",
        "unit1",
        "n2",
        "o2",
        "d2",
        "label2",
        "unit2",
        "axis2_role",
        "coordinate_sampling",
        "offset_sign_convention",
    ):
        assert corrected.header.get(key) == raw.header.get(key)
    assert corrected.data.dtype == np.float64
    assert corrected.header["nmo_half"] == "n"
    assert corrected.header["nmo_stretch"] == "0"
    assert corrected.header["nmo_direction"] == "forward"
    assert corrected.header["nmo_interpolation"] == "linear"
    assert corrected.header["nmo_offset_source"] == "axis"


def test_nmo_uses_offset_magnitude_for_signed_s1_geometry(tmp_path: Path) -> None:
    raw_path = tmp_path / "raw.rsf"
    output_path = tmp_path / "nmo.rsf"
    make_hyperbolic_gather_fixture(
        ntrace=11,
        offset_o=-250.0,
        offset_d=50.0,
        interference_amplitude=0.0,
        noise_std=0.0,
        trend=0.0,
        path=raw_path,
    )
    nmo_correct(raw_path, TRUE_VELOCITY, output_path, half=False, stretch=None)
    corrected = read_rsf(output_path)
    picks = _event_picks(corrected.data)

    np.testing.assert_allclose(picks, np.full(11, 0.45), atol=0.004)
    np.testing.assert_array_equal(picks, picks[::-1])


@pytest.mark.parametrize("velocity", [0.0, -1.0, np.nan, np.inf])
def test_nmo_rejects_nonpositive_or_nonfinite_velocity(
    tmp_path: Path,
    velocity: float,
) -> None:
    raw_path = tmp_path / "raw.rsf"
    output_path = tmp_path / "bad.rsf"
    make_hyperbolic_gather_fixture(path=raw_path)

    with pytest.raises(NMOError, match="velocity values must be (positive|finite)"):
        nmo_correct(raw_path, velocity, output_path, half=False)
    assert not output_path.exists()


@pytest.mark.parametrize("d1", [0.0, -0.004, np.nan])
def test_nmo_rejects_invalid_time_axis(tmp_path: Path, d1: float) -> None:
    raw_path = tmp_path / "raw.rsf"
    output_path = tmp_path / "bad.rsf"
    fixture = make_hyperbolic_gather_fixture()
    header = fixture.header.copy()
    header["d1"] = d1
    write_rsf(raw_path, fixture.data, header)

    with pytest.raises(NMOError, match="d1= must be positive"):
        nmo_correct(raw_path, TRUE_VELOCITY, output_path, half=False)
    assert not output_path.exists()


@pytest.mark.parametrize("d2", [0.0, -50.0, np.nan])
def test_nmo_rejects_invalid_regular_offset_axis(
    tmp_path: Path,
    d2: float,
) -> None:
    raw_path = tmp_path / "raw.rsf"
    output_path = tmp_path / "bad.rsf"
    fixture = make_hyperbolic_gather_fixture()
    header = fixture.header.copy()
    header["d2"] = d2
    write_rsf(raw_path, fixture.data, header)

    with pytest.raises(NMOError, match="d2= must be positive"):
        nmo_correct(raw_path, TRUE_VELOCITY, output_path, half=False)
    assert not output_path.exists()


def test_explicit_finite_offset_vector_overrides_axis_coordinates(
    tmp_path: Path,
) -> None:
    raw_path = tmp_path / "raw.rsf"
    output_path = tmp_path / "nmo.rsf"
    fixture = make_hyperbolic_gather_fixture()
    header = fixture.header.copy()
    header["d2"] = 0.0
    write_rsf(raw_path, fixture.data, header)
    offsets = -500.0 + 50.0 * np.arange(21, dtype=np.float64)

    nmo_correct(
        raw_path,
        TRUE_VELOCITY,
        output_path,
        half=False,
        stretch=None,
        offset=offsets,
    )
    corrected = read_rsf(output_path)

    assert corrected.data.shape == fixture.data.shape
    assert corrected.header["nmo_offset_source"] == "explicit"
    assert _event_pick_std(corrected.data) <= 0.003


def test_nmo_rejects_offset_vector_shape_mismatch(tmp_path: Path) -> None:
    raw_path = tmp_path / "raw.rsf"
    output_path = tmp_path / "bad.rsf"
    make_hyperbolic_gather_fixture(path=raw_path)

    with pytest.raises(NMOError, match="offset data has 20 samples"):
        nmo_correct(
            raw_path,
            TRUE_VELOCITY,
            output_path,
            half=False,
            offset=np.zeros(20),
        )
    assert not output_path.exists()


@pytest.mark.parametrize("bad_value", [np.nan, np.inf])
def test_nmo_rejects_nonfinite_input_samples(
    tmp_path: Path,
    bad_value: float,
) -> None:
    raw_path = tmp_path / "raw.rsf"
    output_path = tmp_path / "bad.rsf"
    fixture = make_hyperbolic_gather_fixture()
    data = fixture.data.copy()
    data[0, 0] = bad_value
    write_rsf(raw_path, data, fixture.header)

    with pytest.raises(NMOError, match="only finite samples"):
        nmo_correct(raw_path, TRUE_VELOCITY, output_path, half=False)
    assert not output_path.exists()


@pytest.mark.parametrize("bad_value", [np.nan, np.inf])
def test_nmo_rejects_nonfinite_explicit_offsets(
    tmp_path: Path,
    bad_value: float,
) -> None:
    raw_path = tmp_path / "raw.rsf"
    output_path = tmp_path / "bad.rsf"
    make_hyperbolic_gather_fixture(path=raw_path)
    offsets = -500.0 + 50.0 * np.arange(21, dtype=np.float64)
    offsets[3] = bad_value

    with pytest.raises(NMOError, match="offset values must be finite"):
        nmo_correct(
            raw_path,
            TRUE_VELOCITY,
            output_path,
            half=False,
            offset=offsets,
        )
    assert not output_path.exists()


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"h0": np.nan}, "h0= must be finite"),
        ({"stretch": np.inf}, "stretch= must be finite"),
        ({"stretch": -0.1}, "stretch= must be non-negative"),
    ],
)
def test_nmo_rejects_invalid_reference_offset_or_stretch(
    tmp_path: Path,
    kwargs: dict[str, float],
    message: str,
) -> None:
    raw_path = tmp_path / "raw.rsf"
    output_path = tmp_path / "bad.rsf"
    make_hyperbolic_gather_fixture(path=raw_path)

    with pytest.raises(NMOError, match=message):
        nmo_correct(raw_path, TRUE_VELOCITY, output_path, half=False, **kwargs)
    assert not output_path.exists()


def test_existing_nmo_cli_accepts_s1_fixture(tmp_path: Path) -> None:
    raw_path = tmp_path / "raw.rsf"
    output_path = tmp_path / "nmo.rsf"
    make_hyperbolic_gather_fixture(path=raw_path)

    code = nmo_main(
        [
            str(raw_path),
            "out=" + str(output_path),
            "velocity=2200",
            "half=n",
            "stretch=0",
        ]
    )
    corrected = read_rsf(output_path)

    assert code == 0
    assert _event_pick_std(corrected.data) <= 0.003
    assert corrected.header["nmo_half"] == "n"


def test_s3_workflow_report_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report = _run_pipeline(tmp_path, monkeypatch)
    metrics = report["metrics"]
    checks = report["checks"]
    assert isinstance(metrics, dict)
    assert isinstance(checks, dict)

    assert report["workflow"] == "seismic_nmo_contract"
    assert report["stage"] == "S3"
    assert report["status"] == "prototype_contract_regression"
    assert report["fixture"] == "hyperbolic_gather"
    assert metrics["event_pick_std_after_s"] <= 0.003
    assert metrics["stack_peak_amplitude_ratio"] >= 2.0
    assert metrics["correct_vs_wrong_stack_peak_ratio"] >= 1.8
    assert metrics["post_stack_peak_time_s"] == pytest.approx(0.45, abs=0.006)
    assert metrics["noise_window_rms_ratio"] <= 1.2
    assert metrics["finite_fraction"] == pytest.approx(1.0)
    assert metrics["header_axis_ok"] is True
    assert checks["overall_pass"] is True
    assert all(checks.values())

    report_text = (tmp_path / "s3_nmo_qc_report.json").read_text(encoding="utf-8")
    assert str(ROOT) not in report_text
    assert str(tmp_path) not in report_text
    assert json.loads(report_text) == report


def test_s3_workflow_subprocess_is_deterministic_and_does_not_pollute_repo(
    tmp_path: Path,
) -> None:
    before = _example_files()
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    for output_dir in (first_dir, second_dir):
        result = _run_subprocess([str(output_dir)])
        assert result.returncode == 0, result.stderr + result.stdout
        assert "overall_pass=True" in result.stdout

    assert (first_dir / "s3_nmo_qc_report.json").read_bytes() == (
        second_dir / "s3_nmo_qc_report.json"
    ).read_bytes()
    assert _example_files() == before
    assert {
        "s3_raw_gather.rsf",
        "s3_nmo_corrected_gather.rsf",
        "s3_pre_nmo_stack.rsf",
        "s3_post_nmo_stack.rsf",
        "s3_nmo_corrected_quicklook.png",
        "s3_nmo_qc_report.json",
    } <= {path.name for path in first_dir.iterdir()}


def test_s3_workflow_default_output_is_system_temporary() -> None:
    result = _run_subprocess([])
    assert result.returncode == 0, result.stderr + result.stdout
    output_line = next(
        line for line in result.stdout.splitlines() if line.startswith("output_dir=")
    )
    output_dir = Path(output_line.partition("=")[2]).resolve()
    temp_root = Path(tempfile.gettempdir()).resolve()
    repo_root = ROOT.resolve()
    try:
        assert output_dir.is_dir()
        assert temp_root in output_dir.parents
        if repo_root not in temp_root.parents and temp_root != repo_root:
            assert repo_root not in (output_dir, *output_dir.parents)
        assert (output_dir / "s3_nmo_qc_report.json").is_file()
    finally:
        shutil.rmtree(output_dir)


def test_s3_contract_has_no_original_madagascar_or_cpp_dependency() -> None:
    sources = [
        ROOT / "pymadagascar" / "seismic" / "nmo.py",
        WORKFLOW,
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in sources)
    assert "testing.runner" not in combined
    assert "run_original_madagascar" not in combined
    assert "pymadagascar.hybrid" not in combined
    assert "pymadagascar._core" not in combined


def _event_picks(data: np.ndarray) -> np.ndarray:
    start, stop = PICK_WINDOW
    return (start + np.argmax(data[:, start:stop], axis=1)) * 0.004


def _event_pick_std(data: np.ndarray) -> float:
    return float(np.std(_event_picks(data)))


def _stack_peak(data: np.ndarray) -> tuple[int, float]:
    start, stop = SIGNAL_WINDOW
    window = np.asarray(data)[start:stop]
    local_index = int(np.argmax(np.abs(window)))
    return start + local_index, float(abs(window[local_index]))


def _run_pipeline(
    output_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> dict[str, object]:
    monkeypatch.syspath_prepend(str(WORKFLOWS))
    namespace = runpy.run_path(str(WORKFLOW))
    return namespace["run_pipeline"](output_dir)


def _run_subprocess(args: list[str]) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = (
        str(ROOT)
        if not env.get("PYTHONPATH")
        else str(ROOT) + os.pathsep + env["PYTHONPATH"]
    )
    return subprocess.run(
        [sys.executable, str(WORKFLOW), *args],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )


def _example_files() -> set[Path]:
    return {
        path.relative_to(EXAMPLES)
        for path in EXAMPLES.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    }
