"""S5 integrated small-gather processing workflow tests."""

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

from pymadagascar.io.rsf import read_rsf


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
WORKFLOWS_DIR = EXAMPLES / "my_workflows"
WORKFLOW = WORKFLOWS_DIR / "seismic_small_gather_processing_workflow.py"
TRUE_VELOCITY = 2200.0


def test_s5_integrated_workflow_report_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report = _run_pipeline(tmp_path, monkeypatch)

    assert report["workflow"] == "seismic_small_gather_processing_workflow"
    assert report["stage"] == "S5"
    assert report["status"] == "integrated_workflow_regression_v0"
    assert report["inputs"]["fixture"] == "hyperbolic_gather"
    assert report["inputs"]["output_schema"] == "workflow_internal_regression_only"
    assert set(report) == {
        "workflow",
        "stage",
        "status",
        "inputs",
        "geometry",
        "pipeline",
        "nmo",
        "semblance",
        "fk",
        "stack",
        "checks",
    }
    assert report["checks"]["overall_pass"] is True
    assert all(report["checks"].values())

    assert report["geometry"]["checks"]["overall_pass"] is True
    assert report["geometry"]["metrics"]["ntrace"] == 21
    assert report["geometry"]["contracts"]["source_receiver_table"][
        "segy_trace_header_model"
    ] == "not_supported"

    assert report["pipeline"]["checks"]["overall_pass"] is True
    assert report["pipeline"]["metrics"]["finite_fraction"] == pytest.approx(1.0)
    assert report["pipeline"]["metrics"]["snr_improvement_db"] > 6.0

    nmo = report["nmo"]
    assert nmo["checks"]["overall_pass"] is True
    assert nmo["metrics"]["stack_peak_amplitude_ratio"] >= 2.0
    assert nmo["metrics"]["correct_vs_wrong_stack_peak_ratio"] >= 1.8
    assert nmo["metrics"]["post_stack_peak_time_s"] == pytest.approx(0.45, abs=0.006)

    semblance = report["semblance"]
    assert semblance["checks"]["overall_pass"] is True
    assert semblance["metrics"]["peak_velocity_at_event_m_per_s"] == pytest.approx(
        TRUE_VELOCITY,
        abs=100.0,
    )
    assert semblance["metrics"]["true_to_wrong_semblance_ratio"] >= 2.0

    fk = report["fk"]
    assert fk["checks"]["overall_pass"] is True
    assert 0.05 <= fk["metrics"]["filtered_rms_ratio"] <= 1.05
    assert fk["metrics"]["finite_fraction"] == pytest.approx(1.0)

    stack = report["stack"]
    assert stack["checks"]["overall_pass"] is True
    assert stack["metrics"]["post_to_pre_peak_ratio"] >= 2.0
    assert stack["metrics"]["post_to_wrong_peak_ratio"] >= 1.8

    report_text = (tmp_path / "s5_integrated_qc_report.json").read_text(encoding="utf-8")
    assert str(ROOT) not in report_text
    assert str(tmp_path) not in report_text
    assert json.loads(report_text) == report


def test_s5_outputs_exist_and_are_finite(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _run_pipeline(tmp_path, monkeypatch)

    rsf_outputs = [
        "s5_raw_gather.rsf",
        "s5_offset_vector.rsf",
        "s5_source_receiver_table.rsf",
        "s5_processed_gather.rsf",
        "s5_processed_stack.rsf",
        "s5_true_velocity_nmo.rsf",
        "s5_wrong_velocity_nmo.rsf",
        "s5_true_velocity_stack.rsf",
        "s5_wrong_velocity_stack.rsf",
        "s5_semblance_panel.rsf",
        "s5_fk_spectrum.rsf",
        "s5_fk_filtered_gather.rsf",
    ]
    for name in rsf_outputs:
        path = tmp_path / name
        assert path.is_file()
        assert (tmp_path / f"{name}@").is_file()
        assert np.isfinite(read_rsf(path).data).all()

    for name in (
        "s5_true_nmo_quicklook.png",
        "s5_semblance_quicklook.png",
        "s5_fk_spectrum_quicklook.png",
        "s5_integrated_qc_report.json",
    ):
        assert (tmp_path / name).is_file()


def test_s5_workflow_subprocess_is_deterministic_and_does_not_pollute_repo(
    tmp_path: Path,
) -> None:
    before = _example_files()
    first = tmp_path / "first"
    second = tmp_path / "second"

    for output_dir in (first, second):
        completed = _run_workflow_subprocess(output_dir)
        assert "overall_pass=True" in completed.stdout

    assert (first / "s5_integrated_qc_report.json").read_bytes() == (
        second / "s5_integrated_qc_report.json"
    ).read_bytes()
    assert {
        "s5_raw_gather.rsf",
        "s5_processed_gather.rsf",
        "s5_true_velocity_nmo.rsf",
        "s5_semblance_panel.rsf",
        "s5_fk_spectrum.rsf",
        "s5_fk_filtered_gather.rsf",
        "s5_true_nmo_quicklook.png",
        "s5_integrated_qc_report.json",
    } <= {path.name for path in first.iterdir()}
    assert _example_files() == before


def test_s5_workflow_default_output_is_system_temporary() -> None:
    completed = _run_workflow_subprocess(None)
    output_dir = _parse_output_dir(completed.stdout)
    temp_root = Path(tempfile.gettempdir()).resolve()
    repo_root = ROOT.resolve()
    try:
        assert output_dir.parent == temp_root
        if repo_root not in temp_root.parents and temp_root != repo_root:
            assert repo_root not in (output_dir, *output_dir.parents)
        assert (output_dir / "s5_integrated_qc_report.json").is_file()
    finally:
        if output_dir.parent == temp_root and output_dir.exists():
            shutil.rmtree(output_dir)


def test_s5_json_report_contains_no_local_absolute_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _run_pipeline(tmp_path, monkeypatch)
    text = (tmp_path / "s5_integrated_qc_report.json").read_text(encoding="utf-8")
    assert str(ROOT) not in text
    assert str(tmp_path) not in text
    assert "output_dir" not in text
    assert "C:\\" not in text
    assert "/mnt/" not in text


def test_s5_adds_no_cli_or_console_script() -> None:
    assert not (ROOT / "pymadagascar" / "cli" / "small_gather_processing.py").exists()
    assert not (
        ROOT / "pymadagascar" / "cli" / "seismic_small_gather_processing.py"
    ).exists()
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "seismic-small-gather-processing" not in pyproject
    assert "seismic_small_gather_processing" not in pyproject


def test_s5_has_no_original_madagascar_or_cpp_dependency() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "pymadagascar.testing.runner" not in workflow
    assert "run_original_madagascar" not in workflow
    assert "original_madagascar_available" not in workflow
    assert "pymadagascar.hybrid" not in workflow
    assert "pymadagascar._core" not in workflow


def _run_pipeline(
    output_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> dict[str, object]:
    monkeypatch.syspath_prepend(str(WORKFLOWS_DIR))
    namespace = runpy.run_path(str(WORKFLOW), run_name="s5_integrated_workflow_test")
    return namespace["run_pipeline"](output_dir)


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
        timeout=60,
    )


def _parse_output_dir(stdout: str) -> Path:
    for line in stdout.splitlines():
        if line.startswith("output_dir="):
            return Path(line.removeprefix("output_dir=")).resolve()
    raise AssertionError(f"workflow did not print output_dir=: {stdout}")


def _example_files() -> set[str]:
    return {
        str(path.relative_to(ROOT))
        for path in WORKFLOWS_DIR.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    }
