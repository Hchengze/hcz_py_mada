from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / "examples" / "my_workflows" / "acoustic_modeling_validation_workflow.py"


def _assert_no_local_paths(payload: object) -> None:
    text = json.dumps(payload, sort_keys=True)
    local_drive_markers = tuple(f"{drive}:{chr(92)}" for drive in ("E", "D"))
    for marker in (*local_drive_markers, "/home/hcz", "/mnt/"):
        assert marker not in text


def test_acoustic_modeling_validation_workflow_subprocess_outputs_json(tmp_path: Path) -> None:
    before = _workflow_files()
    output_dir = tmp_path / "acoustic_modeling_validation"
    env = os.environ.copy()
    env["PYTHONPATH"] = (
        str(ROOT)
        if not env.get("PYTHONPATH")
        else str(ROOT) + os.pathsep + env["PYTHONPATH"]
    )

    result = subprocess.run(
        [sys.executable, str(WORKFLOW), str(output_dir)],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )

    assert result.returncode == 0, result.stderr + result.stdout
    assert "all_checks_passed: True" in result.stdout
    assert _workflow_files() == before

    report_path = output_dir / "acoustic_modeling_validation_summary.json"
    assert report_path.is_file()
    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert report["workflow"] == "acoustic_modeling_validation_workflow"
    assert report["schema"] == "pymadagascar_workflow_acoustic_modeling_validation_v1"
    assert report["stage"] == "F0-6"
    assert report["status"] == "prototype_validation_workflow"

    velocity = report["velocity_model"]
    assert velocity["model_kind"] == "velocity_model_with_anomalies"
    assert velocity["velocity_shape"] == [24, 20]
    assert velocity["anomaly_count"] == 1
    assert velocity["coordinate_frame"] == "local_2d_x_z"

    survey = report["survey_summary"]
    assert survey["shot_count"] == 2
    assert survey["receiver_count_per_shot"] == [5, 5]
    assert survey["time_count_per_shot"] == [64, 64]
    assert survey["can_stack_to_tensor"] is True
    assert survey["tensor_layout_if_stacked"] == "shot_receiver_time"

    tensor = report["tensor_summary"]
    assert tensor["tensor_layout"] == "shot_receiver_time"
    assert tensor["data_shape"] == [2, 5, 64]
    assert tensor["source_coordinate_shape"] == [2, 2]
    assert tensor["receiver_coordinate_shape"] == [2, 5, 2]

    acceptance = report["acceptance"]
    assert acceptance
    assert all(acceptance.values())
    assert report["prototype"] is True
    assert report["field_ready"] is False
    assert report["wave_equation_solver_added"] is False
    assert report["interpolation"] is False
    assert report["imaging"] is False
    assert report["cli"] is False
    assert report["root_stable_api"] is False

    json.dumps(report, sort_keys=True)
    _assert_no_local_paths(report)


def _workflow_files() -> set[Path]:
    workflow_dir = ROOT / "examples" / "my_workflows"
    return {
        path.relative_to(workflow_dir)
        for path in workflow_dir.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    }
