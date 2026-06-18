"""S4-2 small-gather geometry adapter contract tests."""

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
from pymadagascar.io.rsf import read_rsf
from pymadagascar.testing.seismic_fixtures import make_hyperbolic_gather_fixture
from pymadagascar.testing.seismic_geometry import (
    SOURCE_RECEIVER_FIELDS,
    SeismicGeometryError,
    make_explicit_offset_vector,
    make_regular_offset_geometry,
    make_source_receiver_table,
    table_column,
    validate_offset_unit_consistency,
    validate_source_receiver_table,
    write_offset_vector_rsf,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT.parent / "src-master"
WORKFLOWS_DIR = ROOT / "examples" / "my_workflows"
WORKFLOW = WORKFLOWS_DIR / "seismic_geometry_contract_workflow.py"
PUBLIC_NAMES = {
    "SOURCE_RECEIVER_FIELDS",
    "SeismicGeometryError",
    "make_explicit_offset_vector",
    "make_regular_offset_geometry",
    "make_source_receiver_table",
    "table_column",
    "validate_offset_unit_consistency",
    "validate_source_receiver_table",
    "write_offset_vector_rsf",
}


def test_madagascar_geometry_source_paths_are_audited() -> None:
    expected = [
        SOURCE_ROOT / "system" / "seismic" / "Mnmo.c",
        SOURCE_ROOT / "system" / "seismic" / "Mvscan.c",
        SOURCE_ROOT / "system" / "seismic" / "Mslant.c",
        SOURCE_ROOT / "system" / "seismic" / "Mradon.c",
        SOURCE_ROOT / "system" / "seismic" / "Mheaderattr.c",
        SOURCE_ROOT / "system" / "seismic" / "Mheadermath.c",
        SOURCE_ROOT / "system" / "main" / "headersort.c",
        SOURCE_ROOT / "system" / "seismic" / "Msegyheader.c",
    ]
    for path in expected:
        assert path.is_file(), path

    nmo_source = expected[0].read_text(encoding="utf-8", errors="replace")
    vscan_source = expected[1].read_text(encoding="utf-8", errors="replace")
    headersort_source = expected[6].read_text(encoding="utf-8", errors="replace")
    assert 'sf_getstring("offset")' in nmo_source
    assert 'sf_histfloat(cmp,"d2"' in nmo_source
    assert 'sf_getstring("offset")' in vscan_source
    assert 'sf_getstring("head")' in headersort_source


def test_regular_offset_gather_contract_matches_s1_fixture() -> None:
    gather = make_hyperbolic_gather_fixture()
    geometry = make_regular_offset_geometry(gather, expected_ntrace=21)

    expected = -500.0 + 50.0 * np.arange(21, dtype=np.float64)
    np.testing.assert_allclose(geometry.offsets, expected)
    assert geometry.source == "ordinary_rsf_axis"
    assert geometry.axis == 2
    assert geometry.unit == "m"
    assert geometry.time_unit == "s"
    assert geometry.velocity_unit == "m/s"
    assert geometry.sign_convention == "receiver_minus_source"
    assert geometry.coordinate_sampling == "regular"


@pytest.mark.parametrize(
    ("header_key", "value", "message"),
    [
        ("label1", "Sample", "label1=Time"),
        ("unit1", "ms", "unit1=s"),
        ("d1", 0.0, "d1="),
        ("label2", "Trace", "label2=Offset"),
        ("unit2", "", "unit2="),
        ("d2", 0.0, "d2="),
        ("axis2_role", "trace", "axis2_role=signed_offset"),
        ("coordinate_sampling", "irregular", "coordinate_sampling=regular"),
        ("offset_sign_convention", "source_minus_receiver", "receiver_minus_source"),
    ],
)
def test_regular_offset_contract_rejects_invalid_axis_metadata(
    header_key: str,
    value: object,
    message: str,
) -> None:
    gather = make_hyperbolic_gather_fixture()
    header = gather.header.copy()
    header[header_key] = value

    with pytest.raises(SeismicGeometryError, match=message):
        make_regular_offset_geometry(type(gather)(gather.data, header))


def test_explicit_offset_vector_contract_and_rsf_round_trip(tmp_path: Path) -> None:
    offsets = np.array([-120.0, -30.0, 5.0, 95.0], dtype=np.float64)
    vector = make_explicit_offset_vector(
        offsets,
        expected_ntrace=4,
        unit="m",
        time_unit="s",
        velocity_unit="m/s",
    )
    path = tmp_path / "offset.rsf"
    write_offset_vector_rsf(path, vector)
    loaded = read_rsf(path)
    loaded_vector = make_explicit_offset_vector(loaded, expected_ntrace=4)

    np.testing.assert_array_equal(loaded_vector.values, offsets)
    assert loaded.header["geometry_model"] == "explicit_offset_vector"
    assert loaded.header["coordinate_role"] == "explicit_offset"
    assert loaded.header["trace_header_model"] == "explicit_offset_vector_only"
    assert loaded.header["segy_trace_header_model"] == "not_supported"


@pytest.mark.parametrize(
    ("values", "expected_ntrace", "message"),
    [
        (np.zeros(3), 4, "3 samples, expected 4"),
        (np.array([0.0, np.nan]), 2, "finite"),
        (np.zeros((2, 2)), 4, "1D"),
    ],
)
def test_explicit_offset_vector_rejects_invalid_values(
    values: np.ndarray,
    expected_ntrace: int,
    message: str,
) -> None:
    with pytest.raises(SeismicGeometryError, match=message):
        make_explicit_offset_vector(values, expected_ntrace=expected_ntrace)


def test_offset_unit_consistency_contract() -> None:
    assert (
        validate_offset_unit_consistency("m", time_unit="s", velocity_unit="m/s")
        == "m"
    )
    with pytest.raises(SeismicGeometryError, match="incompatible"):
        validate_offset_unit_consistency("ft", time_unit="s", velocity_unit="m/s")


def test_source_receiver_table_is_deterministic_and_formula_checked() -> None:
    offsets = make_explicit_offset_vector(
        -200.0 + 50.0 * np.arange(9, dtype=np.float64),
        expected_ntrace=9,
    )
    first = make_source_receiver_table(offsets=offsets)
    second = make_source_receiver_table(offsets=offsets)

    np.testing.assert_array_equal(first.data, second.data)
    assert first.header.dimensions == (len(SOURCE_RECEIVER_FIELDS), 9)
    assert first.header["field_names"] == ",".join(SOURCE_RECEIVER_FIELDS)
    assert first.header["trace_header_model"] == "minimal_numeric_header_table"
    assert first.header["segy_trace_header_model"] == "not_supported"

    source_x = table_column(first, "source_x")
    receiver_x = table_column(first, "receiver_x")
    offset = table_column(first, "offset")
    midpoint = table_column(first, "midpoint")
    np.testing.assert_allclose(offset, receiver_x - source_x)
    np.testing.assert_allclose(midpoint, 0.5 * (source_x + receiver_x))
    metrics = validate_source_receiver_table(first)
    assert metrics["overall_pass"] is True
    assert metrics["offset_relation_ok"] is True
    assert metrics["midpoint_relation_ok"] is True


def test_source_receiver_table_rejects_missing_fields() -> None:
    table = make_source_receiver_table(ntrace=5)
    header = table.header.copy()
    header["field_names"] = "trace,source_x,receiver_x,offset"

    with pytest.raises(SeismicGeometryError, match="missing required fields"):
        validate_source_receiver_table(type(table)(table.data[:, :4], header))


def test_ordinary_rsf_header_table_and_segy_boundaries_are_separate() -> None:
    gather = make_hyperbolic_gather_fixture()
    table = make_source_receiver_table(offsets=make_regular_offset_geometry(gather).offsets)

    assert gather.header["trace_header_model"] == "ordinary_rsf_only"
    assert gather.header["source_receiver_geometry"] == "not_encoded"
    assert table.header["trace_header_model"] == "minimal_numeric_header_table"
    assert table.header["ordinary_rsf_header_boundary"] == "regular_axes_only"
    assert table.header["explicit_offset_boundary"] == "1d_trace_compatible_coordinate"
    assert table.header["segy_header_boundary"] == "not_supported"
    assert table.header["segy_trace_header_model"] == "not_supported"


def test_geometry_helper_is_not_exported_as_public_api() -> None:
    for namespace in (pymadagascar, public_api, testing_api):
        assert PUBLIC_NAMES.isdisjoint(vars(namespace))
    assert "seismic_geometry" not in testing_api.__all__


def test_s4_2_workflow_report_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.syspath_prepend(str(WORKFLOWS_DIR))
    namespace = runpy.run_path(str(WORKFLOW), run_name="s4_geometry_contract_test")
    report = namespace["run_pipeline"](tmp_path)

    assert report["workflow"] == "seismic_geometry_contract"
    assert report["stage"] == "S4-2"
    assert report["status"] == "internal_geometry_contract_design"
    assert report["fixture"] == "hyperbolic_gather"
    assert report["checks"]["overall_pass"] is True
    assert report["checks"]["not_segy_trace_header"] is True
    assert report["metrics"]["ntrace"] == 21
    assert report["metrics"]["regular_explicit_max_abs_diff_m"] == pytest.approx(0.0)
    assert report["metrics"]["table_offset_max_abs_diff_m"] == pytest.approx(0.0)
    assert report["contracts"]["ordinary_rsf_header"] == "regular_axes_only"
    assert report["contracts"]["segy_trace_header"] == "out_of_scope"

    report_text = (tmp_path / "s4_geometry_report.json").read_text(encoding="utf-8")
    assert str(tmp_path) not in report_text
    assert json.loads(report_text) == report


def test_s4_2_workflow_subprocess_is_deterministic_and_does_not_pollute_repo(
    tmp_path: Path,
) -> None:
    before = _example_files()
    out1 = tmp_path / "run1"
    out2 = tmp_path / "run2"

    _run_workflow_subprocess(out1)
    _run_workflow_subprocess(out2)

    assert (out1 / "s4_geometry_report.json").read_bytes() == (
        out2 / "s4_geometry_report.json"
    ).read_bytes()
    assert {
        "s4_geometry_gather.rsf",
        "s4_geometry_offset_vector.rsf",
        "s4_geometry_source_receiver_table.rsf",
        "s4_geometry_report.json",
    } <= {path.name for path in out1.iterdir()}
    assert _example_files() == before


def test_s4_2_workflow_default_output_is_system_temporary() -> None:
    completed = _run_workflow_subprocess(None)
    output_dir = _parse_output_dir(completed.stdout)
    try:
        assert output_dir.parent == Path(tempfile.gettempdir())
        assert (output_dir / "s4_geometry_report.json").is_file()
    finally:
        if output_dir.parent == Path(tempfile.gettempdir()) and output_dir.exists():
            shutil.rmtree(output_dir)


def test_s4_2_adds_no_cli_or_console_script() -> None:
    assert not (ROOT / "pymadagascar" / "cli" / "geometry.py").exists()
    assert not (ROOT / "pymadagascar" / "cli" / "seismic_geometry.py").exists()
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "seismic-geometry" not in pyproject
    assert "seismic_geometry" not in pyproject


def test_s4_2_has_no_original_madagascar_or_cpp_dependency() -> None:
    sources = [
        ROOT / "pymadagascar" / "testing" / "seismic_geometry.py",
        WORKFLOW,
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in sources)
    assert "pymadagascar.testing.runner" not in combined
    assert "run_original_madagascar" not in combined
    assert "original_madagascar_available" not in combined
    assert "pymadagascar.hybrid" not in combined
    assert "_core" not in combined


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
