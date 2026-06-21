from __future__ import annotations

import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
from typing import Any

import numpy as np
import pytest

from pymadagascar.io.rsf import read_rsf


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
WORKFLOWS = EXAMPLES / "my_workflows"
WORKFLOW = WORKFLOWS / "das_void_diffraction_workflow.py"


def test_workflow_helpers_recover_noise_free_geometry(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.syspath_prepend(str(WORKFLOWS))
    namespace = runpy.run_path(str(WORKFLOW))
    travel_times = namespace["_diffraction_travel_times"]
    invert = namespace["_invert_diffraction_picks"]
    search_grid = namespace["_search_diffraction_grid"]
    original_grid_search = namespace["grid_search_point_location_velocity_2d"]
    calls: list[dict[str, Any]] = []

    def recording_grid_search(*args: Any, **kwargs: Any) -> Any:
        calls.append({"args": args, "kwargs": kwargs})
        return original_grid_search(*args, **kwargs)

    monkeypatch.setitem(
        search_grid.__globals__,
        "grid_search_point_location_velocity_2d",
        recording_grid_search,
    )

    receiver_x = np.linspace(0.0, 35.5, 24)
    picks = travel_times(
        receiver_x,
        source_x=-6.0,
        void_x=17.5,
        void_depth=2.5,
        vr=240.0,
    )
    result = invert(
        receiver_x,
        picks,
        source_x=-6.0,
        x_bounds=(0.0, 35.5),
        depth_bounds=(0.5, 6.0),
        velocity_bounds=(150.0, 400.0),
    )

    assert result.void_x == pytest.approx(17.5, abs=0.1)
    assert result.void_depth == pytest.approx(2.5, rel=0.03)
    assert result.vr == pytest.approx(240.0, rel=0.01)
    assert result.rmse < 1.0e-5
    assert len(calls) == 3
    assert all(call["kwargs"]["velocity_bounds"] == (150.0, 400.0) for call in calls)


def test_workflow_subprocess_outputs_and_inversion(tmp_path: Path) -> None:
    before = _example_files()
    output_dir = tmp_path / "das_void"
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
    assert "true:" in result.stdout
    assert "inverted:" in result.stdout
    assert _example_files() == before

    expected = {
        "das_void_raw.rsf",
        "das_void_raw.rsf@",
        "das_void_fk_filtered.rsf",
        "das_void_fk_filtered.rsf@",
        "das_void_raw.png",
        "das_void_fk_filtered_with_curves.png",
        "das_void_diffraction_picks.csv",
        "das_void_inversion.json",
    }
    assert expected <= {path.name for path in output_dir.iterdir()}

    raw = read_rsf(output_dir / "das_void_raw.rsf")
    filtered = read_rsf(output_dir / "das_void_fk_filtered.rsf")
    assert raw.data.shape == (72, 480)
    assert filtered.data.shape == raw.data.shape
    assert raw.header["label1"] == "Time"
    assert raw.header["label2"] == "DAS Channel X"
    assert filtered.header["fkfilter_vmin"] == "300"

    payload = json.loads((output_dir / "das_void_inversion.json").read_text(encoding="utf-8"))
    assert payload["pick_count"] >= 20
    assert payload["relative_error"]["void_depth"] < 0.10
    assert payload["relative_error"]["void_x"] < 0.03
    assert payload["relative_error"]["vr"] < 0.03
    assert payload["inverted"]["rmse"] < 0.001

    algorithm = payload["localization_algorithm"]
    assert algorithm["module"] == "pymadagascar.localization.traveltime"
    assert algorithm["method"] == "grid_search_point_location_velocity_2d"
    assert algorithm["travel_time_model"] == "source_diffractor_receiver_kinematic"
    assert algorithm["velocity_mode"] == "closed_form_slowness"
    assert algorithm["residual_convention"] == "observed_minus_predicted"
    assert algorithm["coordinate_frame"] == "local_2d_x_z"
    assert algorithm["depth_positive"] == "down"
    assert algorithm["objective"] == "0.5_sum_weighted_squared_residuals"
    assert algorithm["prototype"] is True
    assert algorithm["field_ready"] is False
    assert algorithm["automatic_picking"] is False
    assert algorithm["das_adapter"] is False
    assert algorithm["gauge_response"] is False
    assert algorithm["stable_root_api"] is False
    assert algorithm["cli"] is False

    geometry = payload["das_geometry"]
    assert geometry["schema"] == "pymadagascar_workflow_das_geometry_v1"
    assert geometry["geometry_kind"] == "regular_linear_das"
    assert geometry["coordinate_frame"] == "local_2d"
    assert geometry["distance_unit"] == "m"
    assert geometry["time_unit"] == "s"
    assert geometry["channel_axis_role"] == "fiber_channel"
    assert geometry["channel_count"] == raw.data.shape[0]
    assert geometry["sample_count"] == raw.data.shape[1]
    assert geometry["channel_spacing"] == pytest.approx(float(raw.header["d2"]))
    assert geometry["channel_start"] == pytest.approx(float(raw.header["o2"]))
    assert geometry["channel_stop"] == pytest.approx(
        geometry["channel_start"]
        + geometry["channel_spacing"] * (geometry["channel_count"] - 1)
    )
    assert geometry["fiber_origin_x"] == pytest.approx(geometry["channel_start"])
    assert geometry["fiber_origin_y"] == pytest.approx(0.0)
    assert geometry["fiber_orientation_degrees"] == pytest.approx(0.0)
    assert geometry["fiber_x_start"] == pytest.approx(geometry["channel_start"])
    assert geometry["fiber_x_stop"] == pytest.approx(geometry["channel_stop"])
    assert geometry["source_x"] == pytest.approx(payload["true"]["source_x"])
    assert geometry["source_y"] == pytest.approx(0.0)
    assert geometry["source_kind"] == "synthetic_impact"
    assert geometry["void_x"] == pytest.approx(payload["true"]["void_x"])
    assert geometry["void_depth"] == pytest.approx(payload["true"]["void_depth"])
    assert geometry["void_depth_positive"] == "down"
    assert geometry["gauge_length"] is None
    assert geometry["gauge_length_status"] == "not_modeled"
    assert (
        geometry["receiver_coordinate_convention"]
        == "channel coordinate increases along fiber orientation"
    )
    assert geometry["sample_interval"] == pytest.approx(float(raw.header["d1"]))
    assert geometry["time_start"] == pytest.approx(float(raw.header["o1"]))
    assert geometry["time_stop"] == pytest.approx(
        geometry["time_start"]
        + geometry["sample_interval"] * (geometry["sample_count"] - 1)
    )

    json.dumps(algorithm)
    json.dumps(geometry)
    assert not _contains_local_absolute_path(payload)


def _example_files() -> set[Path]:
    return {
        path.relative_to(EXAMPLES)
        for path in EXAMPLES.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    }


def _contains_local_absolute_path(value: Any) -> bool:
    if isinstance(value, dict):
        return any(_contains_local_absolute_path(item) for item in value.values())
    if isinstance(value, list | tuple):
        return any(_contains_local_absolute_path(item) for item in value)
    if isinstance(value, str):
        normalized = value.replace("\\\\", "/")
        return any(
            marker in normalized
            for marker in ("E:/", "D:/", "/home/hcz", "/mnt/")
        )
    return False
