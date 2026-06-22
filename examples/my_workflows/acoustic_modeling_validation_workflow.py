"""F0-6 geometry-driven acoustic modeling validation workflow.

This deterministic workflow connects the forward-modeling topic helpers:
geometry, synthetic velocity builders, acquisition-driven survey execution,
survey summary, and explicit tensor conversion. It is a smoke-level validation
workflow, not a production acoustic-modeling accuracy study, and it does not
call original Madagascar.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np

from pymadagascar.modeling import (
    AcousticAcquisition2D,
    AcousticModelGrid2D,
    PointSource2D,
    acoustic_survey_to_tensor,
    add_circular_velocity_anomaly_2d,
    constant_velocity_model_2d,
    receiver_line_2d,
    run_acoustic2d_survey,
    summarize_acoustic_survey,
    velocity_model_summary,
)

from _common import parse_output_dir, print_outputs


WORKFLOW = "acoustic_modeling_validation_workflow"
SCHEMA = "pymadagascar_workflow_acoustic_modeling_validation_v1"
NT = 64
DT = 0.001
FPEAK = 20.0
T0 = 0.03
NB = 5


def run_pipeline(output_dir: Path) -> dict[str, Any]:
    """Run the F0-6 acoustic modeling validation workflow and write JSON."""

    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "acoustic_modeling_validation_summary.json"

    grid = AcousticModelGrid2D(nx=24, nz=20, dx=10.0, dz=10.0)
    base_model = constant_velocity_model_2d(grid, 1500.0)
    model = add_circular_velocity_anomaly_2d(
        base_model,
        center_x=120.0,
        center_z=120.0,
        radius=20.0,
        velocity_delta=-200.0,
    )

    receivers = receiver_line_2d(x_start=60.0, x_stop=140.0, z=80.0, spacing=20.0)
    acquisitions = [
        AcousticAcquisition2D(PointSource2D(80.0, 80.0), receivers),
        AcousticAcquisition2D(PointSource2D(140.0, 80.0), receivers),
    ]

    survey = run_acoustic2d_survey(
        model.velocity,
        grid,
        acquisitions,
        nt=NT,
        dt=DT,
        fpeak=FPEAK,
        t0=T0,
        nb=NB,
    )
    survey_summary = summarize_acoustic_survey(survey)
    tensor = acoustic_survey_to_tensor(survey)

    report: dict[str, Any] = {
        "workflow": WORKFLOW,
        "schema": SCHEMA,
        "stage": "F0-6",
        "status": "prototype_validation_workflow",
        "grid": grid.to_metadata(),
        "velocity_model": velocity_model_summary(model),
        "acquisition": _acquisition_summary(acquisitions),
        "modeling": {
            "nt": NT,
            "dt": DT,
            "fpeak": FPEAK,
            "t0": T0,
            "nb": NB,
            "numerical_core": "acoustic2d_forward",
            "shot_wrapper": "run_acoustic2d_shot",
            "survey_wrapper": "run_acoustic2d_survey",
        },
        "survey_summary": survey_summary,
        "tensor_summary": {
            "tensor_layout": tensor.metadata["tensor_layout"],
            "data_shape": tensor.metadata["data_shape"],
            "time_count": tensor.metadata["time_count"],
            "receiver_count": tensor.metadata["receiver_count"],
            "source_coordinate_shape": list(tensor.source_coordinates.shape),
            "receiver_coordinate_shape": list(tensor.receiver_coordinates.shape),
        },
        "acceptance": _acceptance(
            grid=grid,
            velocity=model.velocity,
            survey=survey,
            survey_summary=survey_summary,
            tensor=tensor,
            expected_shots=len(acquisitions),
            expected_receivers=receivers.receiver_count,
        ),
        "prototype": True,
        "field_ready": False,
        "production_accuracy_study": False,
        "wave_equation_solver_added": False,
        "interpolation": False,
        "imaging": False,
        "cli": False,
        "root_stable_api": False,
    }
    report["acceptance"]["metadata_json_safe"] = _is_json_safe(report)
    report["acceptance"]["output_json_path_free"] = _is_path_free(report)
    report["acceptance"]["all_checks_passed"] = all(bool(value) for value in report["acceptance"].values())

    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def _acquisition_summary(acquisitions: Sequence[AcousticAcquisition2D]) -> dict[str, Any]:
    receiver_counts = [acquisition.receivers.receiver_count for acquisition in acquisitions]
    return {
        "acquisition_count": len(acquisitions),
        "source_coordinates": [
            [acquisition.source.x, acquisition.source.z] for acquisition in acquisitions
        ],
        "receiver_count_per_shot": receiver_counts,
        "receiver_coordinates": acquisitions[0].receivers.coordinates.tolist(),
        "coordinate_frame": "local_2d_x_z",
        "distance_unit": "m",
        "receiver_geometry": "shared_regular_line",
    }


def _acceptance(
    *,
    grid: AcousticModelGrid2D,
    velocity: np.ndarray,
    survey: Any,
    survey_summary: dict[str, Any],
    tensor: Any,
    expected_shots: int,
    expected_receivers: int,
) -> dict[str, bool]:
    time = survey.shots[0].time
    return {
        "velocity_shape_matches_grid": tuple(velocity.shape) == (grid.nx, grid.nz),
        "survey_shot_count_matches_expected": survey_summary["shot_count"] == expected_shots,
        "receiver_count_matches_expected": survey_summary["receiver_count_per_shot"]
        == [expected_receivers] * expected_shots,
        "time_count_matches_nt": survey_summary["time_count_per_shot"] == [NT] * expected_shots,
        "tensor_shape_matches_expected": tuple(tensor.data.shape)
        == (expected_shots, expected_receivers, NT),
        "shot_data_all_finite": all(np.all(np.isfinite(shot.data)) for shot in survey.shots),
        "shot_data_not_all_zero": any(np.any(np.abs(shot.data) > 0.0) for shot in survey.shots),
        "time_axis_starts_at_zero": bool(np.isclose(time[0], 0.0)),
        "time_axis_spacing_matches_dt": bool(np.allclose(np.diff(time), DT)),
        "survey_can_stack_to_tensor": survey_summary["can_stack_to_tensor"] is True,
        "tensor_layout_is_shot_receiver_time": tensor.metadata["tensor_layout"] == "shot_receiver_time",
        "uses_topic_level_builders_and_wrappers": True,
    }


def _is_json_safe(payload: object) -> bool:
    try:
        json.dumps(payload, sort_keys=True)
    except (TypeError, ValueError):
        return False
    return True


def _is_path_free(payload: object) -> bool:
    text = json.dumps(payload, sort_keys=True)
    local_drive_markers = tuple(f"{drive}:{chr(92)}" for drive in ("E", "D"))
    return all(marker not in text for marker in (*local_drive_markers, "/home/hcz", "/mnt/"))


def main(argv: Sequence[str] | None = None) -> int:
    output_dir = parse_output_dir(WORKFLOW, argv)
    report = run_pipeline(output_dir)
    report_path = output_dir / "acoustic_modeling_validation_summary.json"
    print(f"workflow: {report['workflow']}")
    print(f"schema: {report['schema']}")
    print(f"all_checks_passed: {report['acceptance']['all_checks_passed']}")
    print_outputs([report_path])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
