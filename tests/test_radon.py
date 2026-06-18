from pathlib import Path

import numpy as np
import pytest

from pymadagascar.cli.iradon import main as iradon_main
from pymadagascar.cli.radon import main as radon_main
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf
from pymadagascar.seismic.radon import (
    RadonError,
    inverse_linear_radon,
    inverse_parabolic_radon,
    linear_radon,
    parabolic_radon,
    radon_adjoint_array,
    radon_model_array,
)
from pymadagascar.testing.runner import original_madagascar_available, run_original_madagascar


NT = 128
NX = 12
DT = 0.004
DX = 10.0
PMIN = -0.001
PMAX = 0.001
DP = 0.0005


def _gather_header(nt: int = NT, nx: int = NX) -> RSFHeader:
    return RSFHeader(
        {
            "n1": nt,
            "o1": 0.0,
            "d1": DT,
            "label1": "Time",
            "unit1": "s",
            "n2": nx,
            "o2": 0.0,
            "d2": DX,
            "label2": "Offset",
            "unit2": "m",
        }
    )


def _radon_header(
    *,
    nt: int = NT,
    np_: int = 5,
    pmin: float = PMIN,
    dp: float = DP,
    nx: int = NX,
    kind: str = "linear",
    x0: float = 1.0,
) -> RSFHeader:
    unit = "s/m" if kind == "linear" else "s/m^2"
    return RSFHeader(
        {
            "n1": nt,
            "o1": 0.0,
            "d1": DT,
            "label1": "Tau",
            "unit1": "s",
            "n2": np_,
            "o2": pmin,
            "d2": dp,
            "label2": "Slowness" if kind == "linear" else "Parabolic Moveout",
            "unit2": unit,
            "radon_kind": kind,
            "radon_nx": nx,
            "radon_ox": 0.0,
            "radon_dx": DX,
            "radon_x0": x0,
            "radon_time_label": "Time",
            "radon_time_unit": "s",
            "radon_offset_label": "Offset",
            "radon_offset_unit": "m",
        }
    )


def _linear_model() -> np.ndarray:
    model = np.zeros((5, NT), dtype=np.float32)
    model[3, 30] = 1.0
    return model


def _parabolic_model() -> np.ndarray:
    model = np.zeros((3, NT), dtype=np.float32)
    model[2, 25] = 1.0
    return model


def test_synthetic_linear_event_radon_peak(tmp_path: Path) -> None:
    model_path = tmp_path / "model.rsf"
    gather_path = tmp_path / "gather.rsf"
    panel_path = tmp_path / "panel.rsf"
    write_rsf(model_path, _linear_model(), _radon_header())

    inverse_linear_radon(model_path, gather_path)
    linear_radon(gather_path, panel_path, pmin=PMIN, pmax=PMAX, dp=DP)
    panel = read_rsf(panel_path)

    peak = np.unravel_index(int(np.argmax(panel.data)), panel.data.shape)
    assert peak[0] == 3
    assert abs(peak[1] - 30) <= 1
    assert panel.data[peak] > 1.0


def test_radon_header_updates_tau_and_p_axes(tmp_path: Path) -> None:
    input_path = tmp_path / "gather.rsf"
    output_path = tmp_path / "panel.rsf"
    write_rsf(input_path, np.ones((NX, NT), dtype=np.float32), _gather_header())

    linear_radon(input_path, output_path, pmin=PMIN, pmax=PMAX, dp=DP)
    panel = read_rsf(output_path)

    assert panel.header.dimensions == (NT, 5)
    assert panel.header["label1"] == "Tau"
    assert panel.header["unit1"] == "s"
    assert panel.header["label2"] == "Slowness"
    assert panel.header["unit2"] == "s/m"
    assert panel.header["o2"] == "-0.001"
    assert panel.header["d2"] == "0.0005"
    assert panel.header["radon_nx"] == str(NX)
    assert panel.header["radon_offset_label"] == "Offset"


def test_linear_radon_adjoint_dot_product() -> None:
    rng = np.random.default_rng(2026)
    tau = DT * np.arange(NT, dtype=np.float64)
    offsets = DX * np.arange(NX, dtype=np.float64)
    p_values = PMIN + DP * np.arange(5, dtype=np.float64)
    model = rng.normal(size=(5, NT)).astype(np.float32)
    data = rng.normal(size=(NX, NT)).astype(np.float32)

    modeled = radon_model_array(model, tau, offsets, p_values)
    adjoint = radon_adjoint_array(data, tau, offsets, p_values)

    lhs = float(np.vdot(modeled, data))
    rhs = float(np.vdot(model, adjoint))
    assert lhs == pytest.approx(rhs, rel=1e-6, abs=1e-5)


def test_inverse_linear_radon_shape_and_header(tmp_path: Path) -> None:
    input_path = tmp_path / "model.rsf"
    output_path = tmp_path / "gather.rsf"
    write_rsf(input_path, _linear_model(), _radon_header())

    inverse_linear_radon(input_path, output_path)
    gather = read_rsf(output_path)

    assert gather.data.shape == (NX, NT)
    assert gather.header.dimensions == (NT, NX)
    assert gather.header["label1"] == "Time"
    assert gather.header["label2"] == "Offset"
    assert gather.header["radon_adjoint"] == "n"


def test_parabolic_radon_peak(tmp_path: Path) -> None:
    model_path = tmp_path / "par_model.rsf"
    gather_path = tmp_path / "par_gather.rsf"
    panel_path = tmp_path / "par_panel.rsf"
    qmin = 0.0
    dq = 0.04
    x0 = 100.0
    write_rsf(
        model_path,
        _parabolic_model(),
        _radon_header(np_=3, pmin=qmin, dp=dq, kind="parabolic", x0=x0),
    )

    inverse_parabolic_radon(model_path, gather_path, x0=x0)
    parabolic_radon(gather_path, panel_path, qmin=qmin, qmax=0.08, dq=dq, x0=x0)
    panel = read_rsf(panel_path)

    peak = np.unravel_index(int(np.argmax(panel.data)), panel.data.shape)
    assert peak[0] == 2
    assert abs(peak[1] - 25) <= 1
    assert panel.header["label2"] == "Parabolic Moveout"
    assert panel.header["radon_kind"] == "parabolic"


def test_offset_file_controls_inverse_output_axis(tmp_path: Path) -> None:
    model_path = tmp_path / "model.rsf"
    offset_path = tmp_path / "offset.rsf"
    output_path = tmp_path / "gather.rsf"
    offsets = np.array([0.0, 20.0, 35.0], dtype=np.float32)
    write_rsf(model_path, _linear_model(), _radon_header(nx=3))
    write_rsf(offset_path, offsets, RSFHeader({"n1": offsets.size, "label1": "Offset", "unit1": "m"}))

    inverse_linear_radon(model_path, output_path, offset=offset_path)
    gather = read_rsf(output_path)

    assert gather.data.shape == (3, NT)
    assert gather.header["n2"] == "3"
    assert gather.header["o2"] == "0"


def test_radon_rejects_least_squares_placeholder(tmp_path: Path) -> None:
    input_path = tmp_path / "gather.rsf"
    output_path = tmp_path / "bad.rsf"
    write_rsf(input_path, np.ones((NX, NT), dtype=np.float32), _gather_header())

    with pytest.raises(RadonError, match="least_squares"):
        linear_radon(input_path, output_path, pmin=PMIN, pmax=PMAX, dp=DP, least_squares=True)

    assert not output_path.exists()


def test_radon_rejects_3d_input(tmp_path: Path) -> None:
    input_path = tmp_path / "cube.rsf"
    output_path = tmp_path / "bad.rsf"
    header = _gather_header()
    header["n3"] = 2
    write_rsf(input_path, np.ones((2, NX, NT), dtype=np.float32), header)

    with pytest.raises(RadonError, match="2D input"):
        linear_radon(input_path, output_path, pmin=PMIN, pmax=PMAX, dp=DP)


def test_radon_cli_and_iradon_cli(tmp_path: Path) -> None:
    model_path = tmp_path / "model.rsf"
    gather_path = tmp_path / "gather.rsf"
    panel_path = tmp_path / "panel.rsf"
    restored_path = tmp_path / "restored.rsf"
    write_rsf(model_path, _linear_model(), _radon_header())
    assert iradon_main([str(model_path), "out=" + str(gather_path)]) == 0

    code = radon_main(
        [
            str(gather_path),
            "out=" + str(panel_path),
            "pmin=-0.001",
            "pmax=0.001",
            "dp=0.0005",
        ]
    )
    assert code == 0
    assert read_rsf(panel_path).header["label2"] == "Slowness"

    code = iradon_main([str(panel_path), "out=" + str(restored_path)])
    assert code == 0
    assert read_rsf(restored_path).data.shape == (NX, NT)


def test_radon_cli_reports_missing_p_axis(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    input_path = tmp_path / "gather.rsf"
    output_path = tmp_path / "bad.rsf"
    write_rsf(input_path, np.ones((NX, NT), dtype=np.float32), _gather_header())

    code = radon_main([str(input_path), "out=" + str(output_path), "pmin=-0.001", "pmax=0.001"])

    assert code == 2
    assert "Missing required parameter: dp=" in capsys.readouterr().err
    assert not output_path.exists()


def test_original_sfslant_shape_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfslant"):
        pytest.skip("Original Madagascar sfslant is not installed")

    input_path = tmp_path / "gather.rsf"
    original_path = tmp_path / "original.rsf"
    write_rsf(input_path, np.ones((NX, NT), dtype=np.float32), _gather_header())

    run_original_madagascar(
        [
            "sfslant",
            "in=gather.rsf",
            "out=original.rsf",
            "adj=y",
            "rho=n",
            "np=5",
            "p0=-0.001",
            "dp=0.0005",
        ],
        cwd=tmp_path,
        require_program="sfslant",
    )
    original = read_rsf(original_path)

    assert original.header.dimensions == (NT, 5)
