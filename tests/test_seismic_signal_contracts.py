from __future__ import annotations

import json
import os
from pathlib import Path
import runpy
import subprocess
import sys

import numpy as np
import pytest

from pymadagascar.io.rsf import read_rsf
from pymadagascar.seismic.mute import MuteError, mutter
from pymadagascar.signal.qc import SignalQCError, demean
from pymadagascar.testing.seismic_fixtures import (
    SeismicFixtureError,
    make_hyperbolic_gather_fixture,
    make_panel_fixture,
    make_plane_wave_panel_fixture,
    make_ricker_event_fixture,
    make_trace_fixture,
)


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
WORKFLOWS = EXAMPLES / "my_workflows"
WORKFLOW = WORKFLOWS / "seismic_signal_contract_workflow.py"


def test_trace_fixture_contract() -> None:
    fixture = make_trace_fixture()

    assert fixture.data.shape == (512,)
    assert fixture.data.dtype == np.float32
    assert np.all(np.isfinite(fixture.data))
    assert fixture.header.dimensions == (512,)
    assert fixture.header["o1"] == "0"
    assert fixture.header["d1"] == "0.004"
    assert fixture.header["label1"] == "Time"
    assert fixture.header["unit1"] == "s"
    assert fixture.header["amplitude_unit"] == "relative"
    assert fixture.header["finite_value_policy"] == "required"
    assert fixture.header["fixture_scope"] == "internal_testing"


def test_panel_fixture_contract_and_regular_channel_axis() -> None:
    fixture = make_panel_fixture(nchannel=7, nt=200, channel_o=10.0, channel_d=2.5)

    assert fixture.data.shape == (7, 200)
    assert fixture.header.shape == fixture.data.shape
    assert fixture.header.dimensions == (200, 7)
    assert fixture.header["label1"] == "Time"
    assert fixture.header["label2"] == "Channel"
    assert fixture.header["unit2"] == "m"
    assert fixture.header["o2"] == "10"
    assert fixture.header["d2"] == "2.5"
    assert fixture.header["coordinate_sampling"] == "regular"
    assert fixture.header["axis2_role"] == "channel_coordinate"


def test_hyperbolic_gather_contract_and_known_arrivals() -> None:
    fixture = make_hyperbolic_gather_fixture(
        ntrace=9,
        nt=400,
        offset_o=-200.0,
        offset_d=50.0,
        t0=0.5,
        velocity=2000.0,
        interference_amplitude=0.0,
        noise_std=0.0,
        trend=0.0,
    )

    offsets = -200.0 + 50.0 * np.arange(9)
    expected = np.sqrt(0.5**2 + np.square(offsets / 2000.0))
    picked = np.argmax(fixture.data, axis=1) * 0.004
    np.testing.assert_allclose(picked, expected, atol=0.004)
    assert fixture.data.shape == (9, 400)
    assert fixture.header["label2"] == "Offset"
    assert fixture.header["unit2"] == "m"
    assert fixture.header["offset_sign_convention"] == "receiver_minus_source"
    assert fixture.header["source_receiver_geometry"] == "not_encoded"
    assert fixture.header["trace_header_model"] == "ordinary_rsf_only"


def test_plane_wave_fixture_has_known_signed_slope() -> None:
    fixture = make_plane_wave_panel_fixture(
        nchannel=11,
        nt=400,
        channel_o=-50.0,
        channel_d=10.0,
        intercept_time=0.4,
        apparent_velocity=1000.0,
        noise_std=0.0,
    )

    channel = -50.0 + 10.0 * np.arange(11)
    picked = np.argmax(fixture.data, axis=1) * 0.002
    expected = 0.4 + channel / 1000.0
    np.testing.assert_allclose(picked, expected, atol=0.002)
    slope = np.polyfit(channel, picked, 1)[0]
    assert slope == pytest.approx(1.0 / 1000.0, abs=2.0e-5)
    assert fixture.header["plane_wave_slowness_s_per_m"] == "0.001"


def test_ricker_event_fixture_has_known_peak() -> None:
    fixture = make_ricker_event_fixture(nt=300, dt=0.002, peak_time=0.24, fpeak=30.0)

    peak_index = int(np.argmax(fixture.data))
    assert peak_index == 120
    assert fixture.data[peak_index] == pytest.approx(1.0, abs=1.0e-7)
    assert fixture.header["event_peak_time_s"] == "0.24"
    assert fixture.header["event_peak_frequency_hz"] == "30"


def test_fixtures_are_deterministic_and_file_round_trip(tmp_path: Path) -> None:
    first = make_hyperbolic_gather_fixture(seed=31)
    second = make_hyperbolic_gather_fixture(seed=31)
    different = make_hyperbolic_gather_fixture(seed=32)
    np.testing.assert_array_equal(first.data, second.data)
    assert not np.array_equal(first.data, different.data)

    path = tmp_path / "gather.rsf"
    written = make_hyperbolic_gather_fixture(seed=31, path=path)
    loaded = read_rsf(path)
    np.testing.assert_array_equal(written.data, loaded.data)
    assert loaded.header["fixture_kind"] == "hyperbolic_cmp_gather"


@pytest.mark.parametrize(
    ("factory", "kwargs", "message"),
    [
        (make_trace_fixture, {"dt": 0.0}, "dt"),
        (make_panel_fixture, {"channel_d": 0.0}, "channel_d"),
        (make_hyperbolic_gather_fixture, {"velocity": 0.0}, "velocity"),
        (make_hyperbolic_gather_fixture, {"offset_d": -1.0}, "offset_d"),
        (make_ricker_event_fixture, {"peak_time": 99.0}, "sampled time range"),
        (make_trace_fixture, {"dtype": np.int32}, "dtype"),
        (make_trace_fixture, {"noise_std": np.inf}, "noise_std"),
    ],
)
def test_fixture_invalid_geometry_and_finite_policy(
    factory: object,
    kwargs: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(SeismicFixtureError, match=message):
        factory(**kwargs)  # type: ignore[operator]


def test_existing_operations_reject_invalid_axis_geometry_and_nonfinite() -> None:
    gather = make_hyperbolic_gather_fixture()
    with pytest.raises(SignalQCError, match="axis"):
        demean(gather.data, axis=3)
    with pytest.raises(MuteError, match="different"):
        mutter(gather.data, time_axis=1, offset_axis=1, v=2000.0)
    with pytest.raises(SignalQCError, match="NaN"):
        demean(np.array([1.0, np.nan], dtype=np.float32), nan_policy="raise")


def test_pipeline_regression_contract(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.syspath_prepend(str(WORKFLOWS))
    namespace = runpy.run_path(str(WORKFLOW))
    payload = namespace["run_pipeline"](tmp_path / "pipeline")
    metrics = payload["metrics"]

    assert payload["status"] == "internal_testing_contract"
    assert payload["shapes"]["raw"] == [21, 512]
    assert payload["shapes"]["processed"] == [21, 512]
    assert payload["shapes"]["stack"] == [512]
    assert metrics["all_finite"] is True
    assert metrics["shape_preserved_before_stack"] is True
    assert 0.75 <= metrics["passband_amplitude_ratio"] <= 1.05
    assert metrics["stopband_amplitude_ratio"] < 0.02
    assert metrics["mute_preboundary_max_abs"] == pytest.approx(0.0, abs=1.0e-8)
    assert metrics["stack_noise_ratio"] < 0.45

    processed = read_rsf(tmp_path / "pipeline" / "s1_processed_gather.rsf")
    stack = read_rsf(tmp_path / "pipeline" / "s1_stack.rsf")
    psd = read_rsf(tmp_path / "pipeline" / "s1_stack_psd.rsf")
    assert processed.header["label1"] == "Time"
    assert processed.header["label2"] == "Offset"
    assert stack.header.dimensions == (512,)
    assert stack.header["label1"] == "Time"
    assert psd.header["label1"] == "Frequency"
    assert psd.header["unit1"] == "Hz"


def test_pipeline_is_deterministic_and_does_not_pollute_repository(
    tmp_path: Path,
) -> None:
    before = _example_files()
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    env = os.environ.copy()
    env["PYTHONPATH"] = (
        str(ROOT)
        if not env.get("PYTHONPATH")
        else str(ROOT) + os.pathsep + env["PYTHONPATH"]
    )

    for output_dir in (first_dir, second_dir):
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
        assert "acceptance:" in result.stdout

    first = json.loads((first_dir / "s1_metrics.json").read_text(encoding="utf-8"))
    second = json.loads((second_dir / "s1_metrics.json").read_text(encoding="utf-8"))
    assert first == second
    assert _example_files() == before
    expected = {
        "s1_synthetic_gather.rsf",
        "s1_processed_gather.rsf",
        "s1_stack.rsf",
        "s1_stack_psd.rsf",
        "s1_processed_quicklook.png",
        "s1_metrics.json",
    }
    assert expected <= {path.name for path in first_dir.iterdir()}


def test_s1_contract_has_no_original_madagascar_or_cpp_dependency() -> None:
    fixture_source = (
        ROOT / "pymadagascar" / "testing" / "seismic_fixtures.py"
    ).read_text(encoding="utf-8")
    workflow_source = WORKFLOW.read_text(encoding="utf-8")
    combined = fixture_source + workflow_source
    assert "testing.runner" not in combined
    assert "run_original_madagascar" not in combined
    assert "pymadagascar.hybrid" not in combined
    assert "pymadagascar._core" not in combined


def _example_files() -> set[Path]:
    return {
        path.relative_to(EXAMPLES)
        for path in EXAMPLES.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    }
