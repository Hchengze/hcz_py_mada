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

import pymadagascar
import pymadagascar.api as public_api
import pymadagascar.testing as testing_api
from pymadagascar.io.rsf import RSFArray, read_rsf
from pymadagascar.testing.seismic_fixtures import (
    make_hyperbolic_gather_fixture,
    make_trace_fixture,
)
from pymadagascar.testing.seismic_metrics import (
    SeismicMetricsError,
    compare_pipeline_metrics,
    compute_gather_pipeline_metrics,
    compute_panel_metrics,
    compute_trace_metrics,
    write_metrics_json,
)


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
WORKFLOWS = EXAMPLES / "my_workflows"
WORKFLOW = WORKFLOWS / "seismic_signal_metrics_workflow.py"
PUBLIC_NAMES = {
    "compute_trace_metrics",
    "compute_panel_metrics",
    "compute_gather_pipeline_metrics",
    "compare_pipeline_metrics",
    "write_metrics_json",
}


def test_metrics_helper_is_not_exported_as_public_api() -> None:
    for namespace in (pymadagascar, public_api, testing_api):
        assert PUBLIC_NAMES.isdisjoint(vars(namespace))


def test_trace_metrics_contract_uses_explicit_windows_and_bands() -> None:
    trace = make_trace_fixture(noise_std=0.0, trend=0.0)
    metrics = compute_trace_metrics(
        trace.data,
        dt=0.004,
        signal_window=(64, 192),
        noise_window=(300, 450),
        target_band=(15.0, 30.0),
        reject_band=(60.0, 80.0),
    )

    assert set(metrics) == {
        "rms",
        "signal_window_rms",
        "noise_window_rms",
        "snr_db",
        "dominant_frequency",
        "target_band_energy",
        "reject_band_energy",
        "finite_fraction",
    }
    assert metrics["finite_fraction"] == 1.0
    assert metrics["dominant_frequency"] == pytest.approx(20.0, abs=1.0)
    assert metrics["target_band_energy"] > metrics["reject_band_energy"]


def test_panel_metrics_are_deterministic_for_s1_fixture() -> None:
    first = make_hyperbolic_gather_fixture(seed=77)
    second = make_hyperbolic_gather_fixture(seed=77)
    kwargs = {
        "dt": 0.004,
        "signal_window": (100, 163),
        "noise_window": (300, 450),
    }
    assert compute_panel_metrics(first.data, **kwargs) == compute_panel_metrics(
        second.data,
        **kwargs,
    )


@pytest.mark.parametrize(
    ("data", "kwargs", "message"),
    [
        (
            np.array([1.0, np.nan]),
            {"signal_window": (0, 1), "noise_window": (1, 2)},
            "finite",
        ),
        (
            np.ones(8),
            {"signal_window": (0, 0), "noise_window": (4, 8)},
            "signal_window",
        ),
        (
            np.ones(8),
            {"signal_window": (0, 5), "noise_window": (4, 8)},
            "must not overlap",
        ),
        (
            np.ones(8),
            {
                "signal_window": (0, 4),
                "noise_window": (4, 8),
                "target_band": (0.0, 5.0),
            },
            "Nyquist",
        ),
    ],
)
def test_trace_metrics_reject_invalid_data_windows_and_bands(
    data: np.ndarray,
    kwargs: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(SeismicMetricsError, match=message):
        compute_trace_metrics(data, dt=0.1, **kwargs)  # type: ignore[arg-type]


def test_pipeline_report_has_stable_schema_and_meaningful_checks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report = _run_pipeline(tmp_path / "pipeline", monkeypatch)
    metrics = report["metrics"]
    checks = report["checks"]
    assert isinstance(metrics, dict)
    assert isinstance(checks, dict)

    assert report["workflow"] == "seismic_signal_metrics"
    assert report["stage"] == "S2"
    assert report["fixture"] == "hyperbolic_gather"
    assert report["status"] == "internal_testing_contract"
    assert metrics["snr_after_db"] >= metrics["snr_before_db"]
    assert metrics["snr_improvement_db"] > 6.0
    assert 0.75 <= metrics["target_band_energy_ratio"] <= 1.10
    assert metrics["reject_band_energy_ratio"] < 0.02
    assert metrics["stack_noise_reduction_ratio"] < 0.45
    assert 0.4 <= metrics["stack_peak_time"] < 0.652
    assert 0.03 < metrics["muted_fraction"] < 0.15
    assert metrics["mute_zero_fraction"] == pytest.approx(1.0)
    assert metrics["finite_fraction"] == pytest.approx(1.0)
    assert metrics["header_axis_ok"] is True
    assert checks["overall_pass"] is True
    assert all(checks.values())


def test_pipeline_metrics_and_json_are_deterministic(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = _run_pipeline(tmp_path / "first", monkeypatch)
    second = _run_pipeline(tmp_path / "second", monkeypatch)
    assert first == second
    assert (tmp_path / "first" / "s2_qc_report.json").read_bytes() == (
        tmp_path / "second" / "s2_qc_report.json"
    ).read_bytes()


def test_pipeline_outputs_preserve_contract_headers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _run_pipeline(tmp_path, monkeypatch)
    raw = read_rsf(tmp_path / "s2_raw_gather.rsf")
    processed = read_rsf(tmp_path / "s2_processed_gather.rsf")
    stack = read_rsf(tmp_path / "s2_stack.rsf")

    assert raw.data.shape == processed.data.shape == (21, 512)
    assert raw.header["label1"] == processed.header["label1"] == "Time"
    assert raw.header["label2"] == processed.header["label2"] == "Offset"
    assert processed.header["axis2_role"] == "signed_offset"
    assert stack.data.shape == (512,)
    assert stack.header["label1"] == "Time"
    assert stack.header["unit1"] == "s"


def test_pipeline_header_check_detects_corrupt_axis_metadata(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _run_pipeline(tmp_path, monkeypatch)
    raw = read_rsf(tmp_path / "s2_raw_gather.rsf")
    before = read_rsf(tmp_path / "s2_detrended_gather.rsf")
    after = read_rsf(tmp_path / "s2_bandpassed_gather.rsf")
    processed = read_rsf(tmp_path / "s2_processed_gather.rsf")
    stack = read_rsf(tmp_path / "s2_stack.rsf")
    bad_header = processed.header.copy()
    bad_header["label1"] = "Sample"

    metrics = compute_gather_pipeline_metrics(
        raw,
        before,
        after,
        RSFArray(processed.data, bad_header),
        stack,
        signal_window=(100, 163),
        noise_window=(300, 450),
    )
    assert metrics["header_axis_ok"] is False
    assert compare_pipeline_metrics(metrics)["overall_pass"] is False


def test_json_report_contains_no_local_absolute_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _run_pipeline(tmp_path, monkeypatch)
    report_text = (tmp_path / "s2_qc_report.json").read_text(encoding="utf-8")
    report = json.loads(report_text)
    assert str(ROOT) not in report_text
    assert str(tmp_path) not in report_text
    assert "output_dir" not in report


def test_write_metrics_json_rejects_paths_and_nonfinite_values(tmp_path: Path) -> None:
    with pytest.raises(SeismicMetricsError, match="Path objects"):
        write_metrics_json(tmp_path / "path.json", {"path": tmp_path})
    with pytest.raises(SeismicMetricsError, match="finite"):
        write_metrics_json(tmp_path / "nan.json", {"value": np.nan})


def test_s2_workflow_subprocess_runs_without_repository_pollution(
    tmp_path: Path,
) -> None:
    before = _example_files()
    output_dir = tmp_path / "explicit"
    result = _run_subprocess([str(output_dir)])

    assert result.returncode == 0, result.stderr + result.stdout
    assert "overall_pass=True" in result.stdout
    assert _example_files() == before
    assert {
        "s2_raw_gather.rsf",
        "s2_processed_gather.rsf",
        "s2_stack.rsf",
        "s2_processed_quicklook.png",
        "s2_qc_report.json",
    } <= {path.name for path in output_dir.iterdir()}


def test_s2_workflow_default_output_is_system_temporary() -> None:
    result = _run_subprocess([])
    assert result.returncode == 0, result.stderr + result.stdout
    output_line = next(
        line for line in result.stdout.splitlines() if line.startswith("output_dir=")
    )
    output_dir = Path(output_line.partition("=")[2]).resolve()
    try:
        assert output_dir.is_dir()
        assert Path(tempfile.gettempdir()).resolve() in output_dir.parents
        assert ROOT.resolve() not in (output_dir, *output_dir.parents)
        assert (output_dir / "s2_qc_report.json").is_file()
    finally:
        shutil.rmtree(output_dir)


def test_s2_metrics_have_no_original_madagascar_or_cpp_dependency() -> None:
    source = (
        ROOT / "pymadagascar" / "testing" / "seismic_metrics.py"
    ).read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    combined = source + workflow
    assert "testing.runner" not in combined
    assert "run_original_madagascar" not in combined
    assert "pymadagascar.hybrid" not in combined
    assert "pymadagascar._core" not in combined


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
