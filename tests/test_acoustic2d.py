from pathlib import Path

import numpy as np
import pytest

from pymadagascar.cli.acoustic2d import main as acoustic2d_main
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf
from pymadagascar.modeling.acoustic2d import (
    Acoustic2DError,
    absorbing_boundary_simple,
    acoustic2d_forward,
    ricker_wavelet,
)


def _velocity_header(nx: int = 41, nz: int = 41, dx: float = 10.0, dz: float = 10.0) -> RSFHeader:
    return RSFHeader(
        {
            "n1": nz,
            "o1": 0.0,
            "d1": dz,
            "label1": "Depth",
            "unit1": "m",
            "n2": nx,
            "o2": 0.0,
            "d2": dx,
            "label2": "X",
            "unit2": "m",
        }
    )


def _write_velocity(path: Path, *, nx: int = 41, nz: int = 41, velocity: float = 1000.0) -> Path:
    write_rsf(path, np.full((nx, nz), velocity, dtype=np.float32), _velocity_header(nx=nx, nz=nz))
    return path


def test_ricker_wavelet_peak_and_shape() -> None:
    wavelet = ricker_wavelet(101, 0.001, 25.0, t0=0.04)

    assert wavelet.shape == (101,)
    assert wavelet.dtype == np.float32
    assert int(np.argmax(wavelet)) == 40
    assert wavelet[40] == pytest.approx(1.0)
    assert np.min(wavelet) < 0.0


def test_absorbing_boundary_simple_damps_edges() -> None:
    field = np.ones((9, 9), dtype=np.float32)

    damped = absorbing_boundary_simple(field, nb=3, strength=0.1)

    assert damped[4, 4] == pytest.approx(1.0)
    assert damped[0, 0] < damped[1, 1] < damped[2, 2] < damped[4, 4]


def test_uniform_velocity_forward_output_dimensions(tmp_path: Path) -> None:
    velocity_path = _write_velocity(tmp_path / "vel.rsf", nx=21, nz=19)
    output_path = tmp_path / "shot.rsf"
    receivers = [(8, 5), (10, 5), (12, 5)]

    acoustic2d_forward(
        velocity_path,
        output_path,
        nt=80,
        dt=0.001,
        sx=10,
        sz=9,
        receivers=receivers,
        fpeak=20.0,
        t0=0.04,
        nb=5,
    )
    shot = read_rsf(output_path)

    assert shot.data.shape == (3, 80)
    assert shot.header.dimensions == (80, 3)
    assert shot.header["label1"] == "Time"
    assert shot.header["label2"] == "Receiver"
    assert shot.header["acoustic2d_fd_time_order"] == "2"
    assert shot.header["acoustic2d_fd_space_order"] == "2"


def test_uniform_velocity_direct_arrival_time_is_reasonable(tmp_path: Path) -> None:
    velocity_path = _write_velocity(tmp_path / "vel.rsf")
    output_path = tmp_path / "shot.rsf"
    sx, sz = 20, 20
    rx, rz = 28, 20
    dt = 0.001
    t0 = 0.05

    acoustic2d_forward(
        velocity_path,
        output_path,
        nt=220,
        dt=dt,
        sx=sx,
        sz=sz,
        receivers=[(rx, rz)],
        fpeak=20.0,
        t0=t0,
        nb=8,
    )
    trace = read_rsf(output_path).data[0]

    peak_time = int(np.argmax(np.abs(trace))) * dt
    expected = t0 + abs(rx - sx) * 10.0 / 1000.0
    assert peak_time == pytest.approx(expected, abs=0.02)
    assert np.max(np.abs(trace)) > 0.01


def test_snapshot_output(tmp_path: Path) -> None:
    velocity_path = _write_velocity(tmp_path / "vel.rsf", nx=15, nz=13)
    output_path = tmp_path / "shot.rsf"
    snapshot_path = tmp_path / "snap.rsf"

    acoustic2d_forward(
        velocity_path,
        output_path,
        nt=30,
        dt=0.001,
        sx=7,
        sz=6,
        receivers=[(7, 6)],
        fpeak=25.0,
        t0=0.02,
        nb=4,
        snapshot_interval=10,
        snapshot_path=snapshot_path,
    )
    snapshots = read_rsf(snapshot_path)

    assert snapshots.data.shape == (3, 15, 13)
    assert snapshots.header.dimensions == (13, 15, 3)
    assert snapshots.header["label3"] == "Snapshot Time"
    assert snapshots.header["d3"] == "0.01"


def test_stability_condition_rejects_large_time_step(tmp_path: Path) -> None:
    velocity_path = _write_velocity(tmp_path / "vel.rsf", velocity=3000.0)
    output_path = tmp_path / "bad.rsf"

    with pytest.raises(Acoustic2DError, match="stability condition"):
        acoustic2d_forward(
            velocity_path,
            output_path,
            nt=20,
            dt=0.01,
            sx=20,
            sz=20,
            receivers=[(21, 20)],
        )

    assert not output_path.exists()


def test_acoustic2d_cli(tmp_path: Path) -> None:
    velocity_path = _write_velocity(tmp_path / "vel.rsf", nx=21, nz=21)
    output_path = tmp_path / "shot.rsf"

    code = acoustic2d_main(
        [
            str(velocity_path),
            "out=" + str(output_path),
            "nt=60",
            "dt=0.001",
            "sx=10",
            "sz=10",
            "rx=8,10,12",
            "rz=10",
            "fpeak=20",
            "t0=0.04",
            "nb=5",
        ]
    )
    shot = read_rsf(output_path)

    assert code == 0
    assert shot.data.shape == (3, 60)
    assert shot.header["acoustic2d_fpeak"] == "20"


def test_acoustic2d_cli_reports_missing_source(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    velocity_path = _write_velocity(tmp_path / "vel.rsf")
    output_path = tmp_path / "bad.rsf"

    code = acoustic2d_main([str(velocity_path), "out=" + str(output_path), "nt=20", "dt=0.001", "sx=10"])

    assert code == 2
    assert "Missing required parameter: sz=" in capsys.readouterr().err
    assert not output_path.exists()
