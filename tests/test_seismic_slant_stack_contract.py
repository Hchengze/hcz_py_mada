"""S6-2 small slant-stack contract tests."""

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

from pymadagascar.cli.iradon import main as iradon_main
from pymadagascar.cli.radon import main as radon_main
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf
from pymadagascar.seismic.radon import (
    RadonError,
    inverse_linear_radon,
    linear_radon,
    radon_adjoint_array,
    radon_model_array,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT.parent / "src-master"
WORKFLOWS_DIR = ROOT / "examples" / "my_workflows"
WORKFLOW = WORKFLOWS_DIR / "seismic_slant_stack_contract_workflow.py"

NT = 256
NX = 31
DT = 0.004
DX = 10.0
OX = -150.0
TAU0 = 0.448
P_TRUE = 0.0004
P_WRONG = -0.0004
PMIN = -0.0008
PMAX = 0.0008
DP = 0.0002
FPEAK = 24.0


def test_madagascar_slant_source_paths_are_audited() -> None:
    mslant = SOURCE_ROOT / "system" / "seismic" / "Mslant.c"
    slant = SOURCE_ROOT / "system" / "seismic" / "slant.c"
    user_slant = SOURCE_ROOT / "user" / "yliu" / "slant.c"

    assert mslant.is_file()
    assert slant.is_file()
    assert user_slant.is_file()

    mslant_source = mslant.read_text(encoding="utf-8", errors="replace")
    slant_source = slant.read_text(encoding="utf-8", errors="replace")
    assert 'sf_getbool ( "adj",&adj )' in mslant_source
    assert 'sf_getint("np",&np)' in mslant_source
    assert 'sf_getfloat("dp",&dp)' in mslant_source
    assert 'sf_getfloat("p0",&p0)' in mslant_source
    assert 'slant_init (rho, x0, dx, nx, p0, dp, np, o1, d1, nt, p1, anti)' in mslant_source
    assert "slant_lop(adj,false,ntp,ntx,vscan,cmp)" in mslant_source
    assert "sf_aastretch_init" in slant_source
    assert "sf_halfint_init" in slant_source
    assert "t = z + sxx" in slant_source


def test_array_dot_test_adjoint_consistency() -> None:
    rng = np.random.default_rng(6202)
    tau = _tau()
    offsets = _offsets()
    p_values = _p_values()
    model = rng.normal(size=(p_values.size, tau.size)).astype(np.float32)
    data = rng.normal(size=(offsets.size, tau.size)).astype(np.float32)

    modeled = radon_model_array(model, tau, offsets, p_values)
    adjoint = radon_adjoint_array(data, tau, offsets, p_values)

    lhs = float(np.vdot(modeled, data))
    rhs = float(np.vdot(model, adjoint))
    assert lhs == pytest.approx(rhs, rel=1e-6, abs=1e-5)


def test_analytic_slant_event_focuses_at_true_slope(tmp_path: Path) -> None:
    gather_path = tmp_path / "gather.rsf"
    panel_path = tmp_path / "panel.rsf"
    write_rsf(gather_path, _linear_event(P_TRUE), _gather_header())

    linear_radon(gather_path, panel_path, pmin=PMIN, pmax=PMAX, dp=DP)
    panel = read_rsf(panel_path)
    p_values = _axis_values(panel, 2)
    tau = _axis_values(panel, 1)
    true_index = int(np.argmin(np.abs(p_values - P_TRUE)))
    wrong_index = int(np.argmin(np.abs(p_values - P_WRONG)))
    tau_index = int(round(TAU0 / DT))

    true_peak = float(np.max(np.abs(panel.data[true_index, tau_index - 2 : tau_index + 3])))
    wrong_peak = float(np.max(np.abs(panel.data[wrong_index, tau_index - 2 : tau_index + 3])))
    peak = np.unravel_index(int(np.argmax(np.abs(panel.data))), panel.data.shape)

    assert p_values[peak[0]] == pytest.approx(P_TRUE, abs=0.5 * DP)
    assert tau[peak[1]] == pytest.approx(TAU0, abs=DT)
    assert true_peak / wrong_peak >= 3.0


def test_iradon_modeling_generates_predictable_linear_event(tmp_path: Path) -> None:
    model_path = tmp_path / "model.rsf"
    gather_path = tmp_path / "modeled.rsf"
    p_values = _p_values()
    write_rsf(model_path, _model_event(p_values), _model_header(p_values))

    inverse_linear_radon(model_path, gather_path)
    gather = read_rsf(gather_path)

    assert gather.data.shape == (NX, NT)
    assert gather.header["radon_direction"] == "modeling"
    assert _modeled_peak_error(gather.data, _offsets()) <= 2.0 * DT
    assert np.isfinite(gather.data).all()


def test_radon_then_iradon_shape_header_and_finiteness(tmp_path: Path) -> None:
    gather_path = tmp_path / "gather.rsf"
    panel_path = tmp_path / "panel.rsf"
    restored_path = tmp_path / "restored.rsf"
    write_rsf(gather_path, _linear_event(P_TRUE), _gather_header())

    linear_radon(gather_path, panel_path, pmin=PMIN, pmax=PMAX, dp=DP)
    inverse_linear_radon(panel_path, restored_path)
    panel = read_rsf(panel_path)
    restored = read_rsf(restored_path)

    assert panel.data.shape == (_p_values().size, NT)
    assert panel.header["label1"] == "Tau"
    assert panel.header["label2"] == "Slowness"
    assert panel.header["axis2_role"] == "slowness"
    assert panel.header["radon_direction"] == "adjoint_slant_stack"
    assert panel.header["radon_operator_form"] == "m=A^T d"
    assert panel.header["radon_sfradon_equivalence"] == "not_sfradon"
    assert restored.data.shape == (NX, NT)
    assert restored.header["label2"] == "Signed Offset"
    assert restored.header["axis2_role"] == "signed_offset"
    assert restored.header["radon_operator_form"] == "d=A m"
    assert np.isfinite(panel.data).all()
    assert np.isfinite(restored.data).all()


def test_regular_and_explicit_offset_vector_are_equivalent(tmp_path: Path) -> None:
    gather_path = tmp_path / "gather.rsf"
    regular_panel_path = tmp_path / "regular_panel.rsf"
    explicit_panel_path = tmp_path / "explicit_panel.rsf"
    offset_path = tmp_path / "offset.rsf"
    offsets = _offsets().astype(np.float32)
    write_rsf(gather_path, _linear_event(P_TRUE), _gather_header())
    write_rsf(offset_path, offsets, RSFHeader({"n1": offsets.size, "label1": "Offset", "unit1": "m"}))

    linear_radon(gather_path, regular_panel_path, pmin=PMIN, pmax=PMAX, dp=DP)
    linear_radon(gather_path, explicit_panel_path, pmin=PMIN, pmax=PMAX, dp=DP, offset=offset_path)

    assert np.allclose(read_rsf(regular_panel_path).data, read_rsf(explicit_panel_path).data)


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
def test_invalid_time_or_offset_axis_raises(
    tmp_path: Path,
    header_updates: dict[str, float],
    message: str,
) -> None:
    gather_path = tmp_path / "bad_axis.rsf"
    output_path = tmp_path / "bad_panel.rsf"
    header = _gather_header()
    for key, value in header_updates.items():
        header[key] = value
    write_rsf(gather_path, _linear_event(P_TRUE), header)

    with pytest.raises(RadonError, match=message):
        linear_radon(gather_path, output_path, pmin=PMIN, pmax=PMAX, dp=DP)
    assert not output_path.exists()


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"pmin": np.nan, "pmax": PMAX, "dp": DP}, "pmin="),
        ({"pmin": PMIN, "pmax": np.inf, "dp": DP}, "pmax="),
        ({"pmin": PMIN, "pmax": PMAX, "dp": np.nan}, "dp="),
        ({"pmin": PMIN, "pmax": PMAX, "dp": 0.0}, "dp="),
        ({"pmin": PMAX, "pmax": PMIN, "dp": DP}, "pmax="),
    ],
)
def test_invalid_slope_range_raises(
    tmp_path: Path,
    kwargs: dict[str, float],
    message: str,
) -> None:
    gather_path = tmp_path / "gather.rsf"
    output_path = tmp_path / "bad_panel.rsf"
    write_rsf(gather_path, _linear_event(P_TRUE), _gather_header())

    with pytest.raises(RadonError, match=message):
        linear_radon(gather_path, output_path, **kwargs)
    assert not output_path.exists()


@pytest.mark.parametrize("bad_value", [np.nan, np.inf, -np.inf])
def test_nan_or_inf_input_raises(tmp_path: Path, bad_value: float) -> None:
    gather_path = tmp_path / "bad_input.rsf"
    output_path = tmp_path / "bad_panel.rsf"
    data = _linear_event(P_TRUE)
    data[0, 0] = bad_value
    write_rsf(gather_path, data, _gather_header())

    with pytest.raises(RadonError, match="non-finite samples"):
        linear_radon(gather_path, output_path, pmin=PMIN, pmax=PMAX, dp=DP)
    assert not output_path.exists()


def test_nonfinite_model_input_raises(tmp_path: Path) -> None:
    model_path = tmp_path / "bad_model.rsf"
    output_path = tmp_path / "bad_gather.rsf"
    model = _model_event(_p_values())
    model[0, 0] = np.inf
    write_rsf(model_path, model, _model_header(_p_values()))

    with pytest.raises(RadonError, match="non-finite samples"):
        inverse_linear_radon(model_path, output_path)
    assert not output_path.exists()


def test_array_helpers_reject_invalid_explicit_offsets_or_p_values() -> None:
    tau = _tau()
    offsets = _offsets()
    p_values = _p_values()
    data = _linear_event(P_TRUE)

    with pytest.raises(RadonError, match="data shape"):
        radon_adjoint_array(data, tau, offsets[:-1], p_values)
    with pytest.raises(RadonError, match="p_values must be strictly increasing"):
        radon_adjoint_array(data, tau, offsets, p_values[::-1])
    with pytest.raises(RadonError, match="p_values contains non-finite"):
        radon_adjoint_array(data, tau, offsets, np.array([PMIN, np.nan, PMAX]))


def test_iradon_explicit_offset_vector_shape_mismatch_raises(tmp_path: Path) -> None:
    model_path = tmp_path / "model.rsf"
    offset_path = tmp_path / "offset.rsf"
    output_path = tmp_path / "bad_gather.rsf"
    offsets = _offsets()[:-1].astype(np.float32)
    write_rsf(model_path, _model_event(_p_values()), _model_header(_p_values()))
    write_rsf(offset_path, offsets, RSFHeader({"n1": offsets.size, "label1": "Offset", "unit1": "m"}))

    with pytest.raises(RadonError, match="offset data has"):
        inverse_linear_radon(model_path, output_path, offset=offset_path, nx=NX)
    assert not output_path.exists()


def test_existing_radon_and_iradon_cli_still_work(tmp_path: Path) -> None:
    gather_path = tmp_path / "gather.rsf"
    panel_path = tmp_path / "panel.rsf"
    restored_path = tmp_path / "restored.rsf"
    write_rsf(gather_path, _linear_event(P_TRUE), _gather_header())

    radon_code = radon_main(
        [
            str(gather_path),
            "out=" + str(panel_path),
            f"pmin={PMIN}",
            f"pmax={PMAX}",
            f"dp={DP}",
        ]
    )
    iradon_code = iradon_main([str(panel_path), "out=" + str(restored_path)])

    assert radon_code == 0
    assert iradon_code == 0
    assert read_rsf(panel_path).header["radon_direction"] == "adjoint_slant_stack"
    assert read_rsf(restored_path).header["radon_direction"] == "modeling"


def test_s6_2_workflow_report_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.syspath_prepend(str(WORKFLOWS_DIR))
    namespace = runpy.run_path(str(WORKFLOW), run_name="s6_slant_stack_contract_test")
    report = namespace["run_pipeline"](tmp_path)

    assert report["workflow"] == "seismic_slant_stack_contract"
    assert report["stage"] == "S6-2"
    assert report["status"] == "prototype_contract_regression"
    assert report["operator_direction"]["radon"] == "adjoint_slant_stack_m_equals_A_transpose_d"
    assert report["operator_direction"]["iradon"] == "modeling_d_equals_A_m"
    assert report["operator_direction"]["solved_inverse"] is False
    assert report["sfradon_equivalence"] == "not_sfradon"
    assert report["checks"]["overall_pass"] is True
    assert report["checks"]["peak_slope_near_true"] is True
    assert report["checks"]["true_slope_beats_wrong"] is True
    assert report["checks"]["dot_test_consistent"] is True
    assert report["checks"]["modeling_event_predictable"] is True
    assert report["metrics"]["peak_slope_s_per_m"] == pytest.approx(P_TRUE, abs=0.5 * DP)
    assert report["metrics"]["peak_tau_s"] == pytest.approx(TAU0, abs=DT)
    assert report["metrics"]["true_to_wrong_peak_ratio"] >= 3.0
    assert report["metrics"]["finite_fraction"] == pytest.approx(1.0)
    assert report["contracts"]["segy_trace_header"] == "out_of_scope"

    report_text = (tmp_path / "s6_slant_stack_qc_report.json").read_text(encoding="utf-8")
    assert str(tmp_path) not in report_text
    assert json.loads(report_text) == report


def test_s6_2_workflow_subprocess_is_deterministic_and_does_not_pollute_repo(
    tmp_path: Path,
) -> None:
    before = _example_files()
    out1 = tmp_path / "run1"
    out2 = tmp_path / "run2"

    _run_workflow_subprocess(out1)
    _run_workflow_subprocess(out2)

    assert (out1 / "s6_slant_stack_qc_report.json").read_bytes() == (
        out2 / "s6_slant_stack_qc_report.json"
    ).read_bytes()
    assert {
        "s6_slant_raw_gather.rsf",
        "s6_slant_panel.rsf",
        "s6_slant_model.rsf",
        "s6_slant_modeled_gather.rsf",
        "s6_slant_panel_quicklook.png",
        "s6_slant_stack_qc_report.json",
    } <= {path.name for path in out1.iterdir()}
    assert _example_files() == before


def test_s6_2_workflow_default_output_is_system_temporary() -> None:
    completed = _run_workflow_subprocess(None)
    output_dir = _parse_output_dir(completed.stdout)
    try:
        assert output_dir.parent == Path(tempfile.gettempdir())
        assert (output_dir / "s6_slant_stack_qc_report.json").is_file()
    finally:
        if output_dir.parent == Path(tempfile.gettempdir()) and output_dir.exists():
            shutil.rmtree(output_dir)


def test_s6_2_adds_no_cli_or_console_script() -> None:
    assert not (ROOT / "pymadagascar" / "cli" / "slant_stack_contract.py").exists()
    assert not (ROOT / "pymadagascar" / "cli" / "seismic_slant_stack_contract.py").exists()
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "seismic-slant-stack-contract" not in pyproject
    assert "seismic_slant_stack_contract" not in pyproject


def test_s6_2_has_no_original_madagascar_or_cpp_dependency() -> None:
    sources = [
        ROOT / "pymadagascar" / "seismic" / "radon.py",
        WORKFLOW,
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in sources)
    assert "pymadagascar.testing.runner" not in combined
    assert "run_original_madagascar" not in combined
    assert "original_madagascar_available" not in combined
    assert "pymadagascar.hybrid" not in combined
    assert "_core" not in combined


def _gather_header() -> RSFHeader:
    return RSFHeader(
        {
            "n1": NT,
            "o1": 0.0,
            "d1": DT,
            "label1": "Time",
            "unit1": "s",
            "n2": NX,
            "o2": OX,
            "d2": DX,
            "label2": "Signed Offset",
            "unit2": "m",
            "axis2_role": "signed_offset",
            "coordinate_sampling": "regular",
            "offset_sign_convention": "receiver_minus_source",
        }
    )


def _model_header(p_values: np.ndarray) -> RSFHeader:
    return RSFHeader(
        {
            "n1": NT,
            "o1": 0.0,
            "d1": DT,
            "label1": "Tau",
            "unit1": "s",
            "n2": p_values.size,
            "o2": float(p_values[0]),
            "d2": float(p_values[1] - p_values[0]),
            "label2": "Slowness",
            "unit2": "s/m",
            "axis2_role": "slowness",
            "radon_kind": "linear",
            "radon_nx": NX,
            "radon_ox": OX,
            "radon_dx": DX,
            "radon_x0": 1.0,
            "radon_time_label": "Time",
            "radon_time_unit": "s",
            "radon_offset_label": "Signed Offset",
            "radon_offset_unit": "m",
        }
    )


def _tau() -> np.ndarray:
    return DT * np.arange(NT, dtype=np.float64)


def _offsets() -> np.ndarray:
    return OX + DX * np.arange(NX, dtype=np.float64)


def _p_values() -> np.ndarray:
    return PMIN + DP * np.arange(int(round((PMAX - PMIN) / DP)) + 1, dtype=np.float64)


def _axis_values(item, axis: int) -> np.ndarray:
    origin = float(item.header[f"o{axis}"])
    spacing = float(item.header[f"d{axis}"])
    count = int(item.header[f"n{axis}"])
    return origin + spacing * np.arange(count, dtype=np.float64)


def _linear_event(p_value: float) -> np.ndarray:
    tau = _tau()
    offsets = _offsets()
    arrivals = TAU0 + p_value * offsets.reshape(NX, 1)
    return _ricker(tau.reshape(1, NT) - arrivals).astype(np.float32)


def _model_event(p_values: np.ndarray) -> np.ndarray:
    model = np.zeros((p_values.size, NT), dtype=np.float32)
    true_index = int(np.argmin(np.abs(p_values - P_TRUE)))
    model[true_index] = _ricker(_tau() - TAU0)
    return model


def _ricker(time: np.ndarray) -> np.ndarray:
    arg = np.pi * FPEAK * time
    return ((1.0 - 2.0 * arg * arg) * np.exp(-(arg * arg))).astype(np.float32)


def _modeled_peak_error(data: np.ndarray, offsets: np.ndarray) -> float:
    values = np.asarray(data, dtype=np.float64)
    errors = []
    for ix, offset in enumerate(offsets):
        expected = TAU0 + P_TRUE * offset
        peak_time = int(np.argmax(np.abs(values[ix]))) * DT
        errors.append(abs(peak_time - expected))
    return float(np.max(errors))


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
