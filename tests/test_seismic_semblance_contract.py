"""S4-1 Semblance prototype contract tests."""

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

from pymadagascar.cli.semblance import main as semblance_main
from pymadagascar.io.rsf import read_rsf, write_rsf
from pymadagascar.seismic.nmo import nmo_correct
from pymadagascar.seismic.semblance import SemblanceError, semblance_scan
from pymadagascar.seismic.stack import stack_rsf
from pymadagascar.testing.seismic_fixtures import make_hyperbolic_gather_fixture


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT.parent / "src-master"
MVSCAN_SOURCE = SOURCE_ROOT / "system" / "seismic" / "Mvscan.c"
WORKFLOWS_DIR = ROOT / "examples" / "my_workflows"
WORKFLOW = WORKFLOWS_DIR / "seismic_semblance_contract_workflow.py"
TRUE_VELOCITY = 2200.0
WRONG_VELOCITY = 1700.0
VMIN = 1700.0
VMAX = 2700.0
DV = 100.0


def test_mvscan_source_path_audit_record_is_present() -> None:
    assert MVSCAN_SOURCE.is_file()
    text = MVSCAN_SOURCE.read_text(encoding="utf-8", errors="replace")
    for pattern in (
        'sf_getfloat("v0"',
        'sf_getfloat("dv"',
        'sf_getint("nv"',
        'sf_getbool("semblance"',
        'sf_getbool("diffsemblance"',
        'sf_getbool("avosemblance"',
        "stretch(nmo,nmofunc",
        'sf_putstring(scan,"label2"',
    ):
        assert pattern in text


def test_semblance_accepts_s1_fixture_and_peaks_near_true_velocity(tmp_path: Path) -> None:
    raw_path = tmp_path / "gather.rsf"
    panel_path = tmp_path / "semblance.rsf"
    raw = make_hyperbolic_gather_fixture(path=raw_path)

    semblance_scan(
        raw_path,
        panel_path,
        vmin=VMIN,
        vmax=VMAX,
        dv=DV,
        half=False,
        stretch=None,
        smooth=2,
    )
    panel = read_rsf(panel_path)
    velocities = _velocity_axis(panel)
    event_index = _event_index(raw)
    event_scores = np.asarray(panel.data[:, event_index], dtype=np.float64)

    assert panel.data.shape == (11, 512)
    assert np.all(np.isfinite(panel.data))
    assert float(velocities[int(np.argmax(event_scores))]) == pytest.approx(
        TRUE_VELOCITY,
        abs=DV,
    )
    assert float(np.max(event_scores)) > 0.85
    global_index = np.unravel_index(int(np.argmax(panel.data)), panel.data.shape)
    assert float(velocities[global_index[0]]) == pytest.approx(TRUE_VELOCITY, abs=DV)
    assert _time_axis(panel)[global_index[1]] == pytest.approx(
        float(raw.header["event_t0_s"]),
        abs=0.006,
    )


def test_true_velocity_semblance_and_stack_beats_wrong_velocity(tmp_path: Path) -> None:
    raw_path = tmp_path / "gather.rsf"
    panel_path = tmp_path / "semblance.rsf"
    true_nmo = tmp_path / "true_nmo.rsf"
    wrong_nmo = tmp_path / "wrong_nmo.rsf"
    true_stack = tmp_path / "true_stack.rsf"
    wrong_stack = tmp_path / "wrong_stack.rsf"
    raw = make_hyperbolic_gather_fixture(path=raw_path)

    semblance_scan(
        raw_path,
        panel_path,
        vmin=VMIN,
        vmax=VMAX,
        dv=DV,
        half=False,
        stretch=None,
        smooth=2,
    )
    nmo_correct(raw_path, TRUE_VELOCITY, true_nmo, half=False, stretch=None)
    nmo_correct(raw_path, WRONG_VELOCITY, wrong_nmo, half=False, stretch=None)
    stack_rsf(true_nmo, true_stack, axis=2, mode="mean", nonzero=False)
    stack_rsf(wrong_nmo, wrong_stack, axis=2, mode="mean", nonzero=False)

    panel = read_rsf(panel_path)
    event_scores = np.asarray(panel.data[:, _event_index(raw)], dtype=np.float64)
    velocities = _velocity_axis(panel)
    true_score = event_scores[int(np.argmin(np.abs(velocities - TRUE_VELOCITY)))]
    wrong_score = event_scores[int(np.argmin(np.abs(velocities - WRONG_VELOCITY)))]
    true_peak = _window_peak(read_rsf(true_stack).data)
    wrong_peak = _window_peak(read_rsf(wrong_stack).data)

    assert true_score / wrong_score >= 2.0
    assert true_peak / wrong_peak >= 1.8


def test_semblance_output_header_and_velocity_axis_contract(tmp_path: Path) -> None:
    raw_path = tmp_path / "gather.rsf"
    panel_path = tmp_path / "semblance.rsf"
    raw = make_hyperbolic_gather_fixture(path=raw_path)

    semblance_scan(
        raw_path,
        panel_path,
        vmin=VMIN,
        vmax=VMAX,
        dv=DV,
        half=False,
        stretch=None,
        smooth=2,
    )
    panel = read_rsf(panel_path)

    assert panel.header.dimensions == (512, 11)
    assert panel.header["n1"] == raw.header["n1"]
    assert panel.header["o1"] == raw.header["o1"]
    assert panel.header["d1"] == raw.header["d1"]
    assert panel.header["label1"] == "Time"
    assert panel.header["unit1"] == "s"
    assert panel.header["n2"] == "11"
    assert panel.header["o2"] == f"{VMIN:g}"
    assert panel.header["d2"] == f"{DV:g}"
    assert panel.header["label2"] == "Velocity"
    assert panel.header["unit2"] == "m/s"
    assert panel.header["axis2_role"] == "velocity"
    assert panel.header["coordinate_sampling"] == "regular"
    assert panel.header["semblance_reference_source"] == "../src-master/system/seismic/Mvscan.c"
    assert panel.header["semblance_algorithm"] == "simple_nmo_stack_ratio"
    assert panel.header["semblance_madagascar_subset"] == "velocity_panel_semblance_only"
    assert panel.header["semblance_offset_source"] == "axis"
    assert panel.header["semblance_input_offset_n"] == raw.header["n2"]
    assert panel.header["semblance_input_offset_o"] == raw.header["o2"]
    assert panel.header["semblance_input_offset_d"] == raw.header["d2"]
    assert panel.header["semblance_input_axis2_role"] == "signed_offset"
    assert panel.header["semblance_input_offset_sign_convention"] == "receiver_minus_source"
    assert panel.header["semblance_velocity_min"] == f"{VMIN:g}"
    assert panel.header["semblance_velocity_max"] == f"{VMAX:g}"
    assert panel.header["semblance_velocity_count"] == "11"
    assert panel.header["semblance_half"] == "n"
    assert panel.header["semblance_stretch"] == "0"
    assert panel.header["semblance_smooth"] == "2"
    assert panel.header["semblance_interpolation"] == "linear"


def test_explicit_offset_vector_contract_and_shape_mismatch(tmp_path: Path) -> None:
    raw_path = tmp_path / "gather.rsf"
    panel_path = tmp_path / "semblance.rsf"
    bad_path = tmp_path / "bad.rsf"
    raw = make_hyperbolic_gather_fixture(path=raw_path)
    header = raw.header.copy()
    header["d2"] = 0.0
    write_rsf(raw_path, raw.data, header)
    offsets = -500.0 + 50.0 * np.arange(21, dtype=np.float64)

    semblance_scan(
        raw_path,
        panel_path,
        vmin=VMIN,
        vmax=VMAX,
        dv=DV,
        offset=offsets,
        half=False,
        stretch=None,
    )
    assert read_rsf(panel_path).header["semblance_offset_source"] == "explicit"

    with pytest.raises(SemblanceError, match="offset vector length"):
        semblance_scan(
            raw_path,
            bad_path,
            vmin=VMIN,
            vmax=VMAX,
            dv=DV,
            offset=offsets[:-1],
            half=False,
            stretch=None,
        )
    assert not bad_path.exists()


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"vmin": 0.0}, "vmin= must be positive"),
        ({"vmin": np.nan}, "vmin= must be finite"),
        ({"vmax": 1600.0}, "vmax= must be greater"),
        ({"dv": 0.0}, "dv= must be positive"),
        ({"dv": np.inf}, "dv= must be finite"),
    ],
)
def test_invalid_velocity_axis_parameters_raise(
    tmp_path: Path,
    kwargs: dict[str, float],
    message: str,
) -> None:
    raw_path = tmp_path / "gather.rsf"
    out_path = tmp_path / "bad.rsf"
    make_hyperbolic_gather_fixture(path=raw_path)
    params = {"vmin": VMIN, "vmax": VMAX, "dv": DV}
    params.update(kwargs)

    with pytest.raises(SemblanceError, match=message):
        semblance_scan(raw_path, out_path, **params)
    assert not out_path.exists()


@pytest.mark.parametrize(
    ("key", "value", "message"),
    [
        ("d1", 0.0, "d1= must be positive"),
        ("d1", -0.004, "d1= must be positive"),
        ("d1", np.nan, "d1= must be positive"),
        ("o1", np.inf, "o1= must be finite"),
    ],
)
def test_invalid_time_axis_raises(
    tmp_path: Path,
    key: str,
    value: float,
    message: str,
) -> None:
    raw_path = tmp_path / "gather.rsf"
    out_path = tmp_path / "bad.rsf"
    raw = make_hyperbolic_gather_fixture()
    header = raw.header.copy()
    header[key] = value
    write_rsf(raw_path, raw.data, header)

    with pytest.raises(SemblanceError, match=message):
        semblance_scan(raw_path, out_path, vmin=VMIN, vmax=VMAX, dv=DV)
    assert not out_path.exists()


@pytest.mark.parametrize(
    ("key", "value", "message"),
    [
        ("d2", 0.0, "d2= must be positive"),
        ("d2", -50.0, "d2= must be positive"),
        ("d2", np.nan, "d2= must be positive"),
        ("o2", np.inf, "o2= must be finite"),
    ],
)
def test_invalid_regular_offset_axis_raises(
    tmp_path: Path,
    key: str,
    value: float,
    message: str,
) -> None:
    raw_path = tmp_path / "gather.rsf"
    out_path = tmp_path / "bad.rsf"
    raw = make_hyperbolic_gather_fixture()
    header = raw.header.copy()
    header[key] = value
    write_rsf(raw_path, raw.data, header)

    with pytest.raises(SemblanceError, match=message):
        semblance_scan(raw_path, out_path, vmin=VMIN, vmax=VMAX, dv=DV)
    assert not out_path.exists()


@pytest.mark.parametrize("bad_value", [np.nan, np.inf])
def test_nonfinite_input_samples_raise(tmp_path: Path, bad_value: float) -> None:
    raw_path = tmp_path / "gather.rsf"
    out_path = tmp_path / "bad.rsf"
    raw = make_hyperbolic_gather_fixture()
    data = raw.data.copy()
    data[0, 0] = bad_value
    write_rsf(raw_path, data, raw.header)

    with pytest.raises(SemblanceError, match="finite samples"):
        semblance_scan(raw_path, out_path, vmin=VMIN, vmax=VMAX, dv=DV)
    assert not out_path.exists()


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"h0": np.nan}, "h0= must be finite"),
        ({"stretch": np.inf}, "stretch= must be finite"),
        ({"stretch": -0.1}, "stretch= must be non-negative"),
        ({"smooth": -1}, "smooth= must be non-negative"),
        ({"smooth": 1.5}, "smooth= must be an integer"),
    ],
)
def test_invalid_auxiliary_parameters_raise(
    tmp_path: Path,
    kwargs: dict[str, float],
    message: str,
) -> None:
    raw_path = tmp_path / "gather.rsf"
    out_path = tmp_path / "bad.rsf"
    make_hyperbolic_gather_fixture(path=raw_path)
    params = {
        "vmin": VMIN,
        "vmax": VMAX,
        "dv": DV,
        "half": False,
        "stretch": None,
        "smooth": 2,
    }
    params.update(kwargs)

    with pytest.raises(SemblanceError, match=message):
        semblance_scan(raw_path, out_path, **params)
    assert not out_path.exists()


def test_existing_semblance_cli_still_accepts_s1_fixture(tmp_path: Path) -> None:
    raw_path = tmp_path / "gather.rsf"
    out_path = tmp_path / "semblance.rsf"
    make_hyperbolic_gather_fixture(path=raw_path)

    code = semblance_main(
        [
            str(raw_path),
            "out=" + str(out_path),
            "vmin=1700",
            "vmax=2700",
            "dv=100",
            "half=n",
            "stretch=0",
            "smooth=2",
        ]
    )

    assert code == 0
    loaded = read_rsf(out_path)
    assert loaded.header.dimensions == (512, 11)
    assert loaded.header["label2"] == "Velocity"
    assert loaded.header["semblance_reference_source"] == "../src-master/system/seismic/Mvscan.c"


def test_s4_workflow_report_contract(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.syspath_prepend(str(WORKFLOWS_DIR))
    namespace = runpy.run_path(str(WORKFLOW), run_name="s4_semblance_contract_test")
    report = namespace["run_pipeline"](tmp_path)

    assert report["workflow"] == "seismic_semblance_contract"
    assert report["stage"] == "S4-1"
    assert report["fixture"] == "hyperbolic_gather"
    assert report["madagascar_reference"] == "../src-master/system/seismic/Mvscan.c"
    assert report["parameters"]["not_sfvscan_clone"] is True
    assert report["checks"]["overall_pass"] is True
    assert report["checks"]["finite"] is True
    assert report["checks"]["header_axis_ok"] is True
    assert report["metrics"]["peak_velocity_at_event_m_per_s"] == pytest.approx(
        TRUE_VELOCITY,
        abs=DV,
    )
    assert report["metrics"]["true_to_wrong_semblance_ratio"] >= 2.0
    assert report["metrics"]["true_to_wrong_stack_peak_ratio"] >= 1.8

    report_path = tmp_path / "s4_semblance_qc_report.json"
    loaded = json.loads(report_path.read_text(encoding="utf-8"))
    assert loaded == report
    assert str(tmp_path) not in report_path.read_text(encoding="utf-8")


def test_s4_workflow_subprocess_is_deterministic_and_does_not_pollute_repo(
    tmp_path: Path,
) -> None:
    before = _example_files()
    out1 = tmp_path / "run1"
    out2 = tmp_path / "run2"

    _run_workflow_subprocess(out1)
    _run_workflow_subprocess(out2)

    assert (out1 / "s4_semblance_qc_report.json").read_bytes() == (
        out2 / "s4_semblance_qc_report.json"
    ).read_bytes()
    assert (out1 / "s4_semblance_panel.rsf").is_file()
    assert (out1 / "s4_semblance_panel.rsf@").is_file()
    assert (out1 / "s4_semblance_panel_quicklook.png").is_file()
    assert _example_files() == before


def test_s4_workflow_default_output_is_system_temporary() -> None:
    completed = _run_workflow_subprocess(None)
    output_dir = _parse_output_dir(completed.stdout)
    try:
        assert output_dir.parent == Path(tempfile.gettempdir())
        assert (output_dir / "s4_semblance_qc_report.json").is_file()
    finally:
        if output_dir.parent == Path(tempfile.gettempdir()) and output_dir.exists():
            shutil.rmtree(output_dir)


def test_s4_contract_has_no_original_madagascar_or_cpp_dependency() -> None:
    implementation = (ROOT / "pymadagascar" / "seismic" / "semblance.py").read_text(
        encoding="utf-8"
    )
    workflow = WORKFLOW.read_text(encoding="utf-8")
    combined = implementation + "\n" + workflow

    assert "pymadagascar.testing.runner" not in combined
    assert "run_original_madagascar" not in combined
    assert "original_madagascar_available" not in combined
    assert "pymadagascar.hybrid" not in combined
    assert "_core" not in combined


def _velocity_axis(item) -> np.ndarray:
    origin = float(item.header["o2"])
    step = float(item.header["d2"])
    count = int(item.header["n2"])
    return origin + step * np.arange(count, dtype=np.float64)


def _time_axis(item) -> np.ndarray:
    origin = float(item.header["o1"])
    step = float(item.header["d1"])
    count = int(item.header["n1"])
    return origin + step * np.arange(count, dtype=np.float64)


def _event_index(raw) -> int:
    return int(round(float(raw.header["event_t0_s"]) / float(raw.header["d1"])))


def _window_peak(data: np.ndarray) -> float:
    window = np.asarray(data)[95:135]
    return float(np.max(np.abs(window)))


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
