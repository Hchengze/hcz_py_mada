from pathlib import Path

import numpy as np
import pytest

from pymadagascar.cli.nmo import main as nmo_main
from pymadagascar.cli.semblance import main as semblance_main
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf
from pymadagascar.seismic.nmo import NMOError, inverse_nmo, nmo_correct
from pymadagascar.seismic.semblance import semblance_scan
from pymadagascar.testing.runner import original_madagascar_available, run_original_madagascar


TRUE_VELOCITY = 2000.0


def _header(nt: int = 251, nh: int = 5, dt: float = 0.004) -> RSFHeader:
    return RSFHeader(
        {
            "n1": nt,
            "o1": 0.0,
            "d1": dt,
            "label1": "Time",
            "unit1": "s",
            "n2": nh,
            "o2": 0.0,
            "d2": 150.0,
            "label2": "Offset",
            "unit2": "m",
        }
    )


def _velocity_header(nt: int = 251, dt: float = 0.004) -> RSFHeader:
    return RSFHeader({"n1": nt, "o1": 0.0, "d1": dt, "label1": "Time", "unit1": "s"})


def _hyperbolic_gather(
    *,
    nt: int = 251,
    nh: int = 5,
    dt: float = 0.004,
    event_time: float = 0.4,
    velocity: float = TRUE_VELOCITY,
    half: bool = False,
) -> np.ndarray:
    times = dt * np.arange(nt, dtype=np.float64)
    offsets = 150.0 * np.arange(nh, dtype=np.float64)
    data = np.zeros((nh, nt), dtype=np.float32)
    width = 0.012
    for ih, offset in enumerate(offsets):
        h = offset * (2.0 if half else 1.0)
        arrival = np.sqrt(event_time * event_time + (h / velocity) ** 2)
        data[ih] = np.exp(-0.5 * ((times - arrival) / width) ** 2).astype(np.float32)
    return data


def _velocity_file(path: Path, nt: int = 251, velocity: float = TRUE_VELOCITY) -> Path:
    write_rsf(path, np.full(nt, velocity, dtype=np.float32), _velocity_header(nt=nt))
    return path


def test_constant_velocity_nmo_flattens_hyperbolic_event(tmp_path: Path) -> None:
    input_path = tmp_path / "cmp.rsf"
    vel_path = _velocity_file(tmp_path / "vel.rsf")
    output_path = tmp_path / "nmo.rsf"
    data = _hyperbolic_gather()
    write_rsf(input_path, data, _header())

    nmo_correct(input_path, vel_path, output_path, half=False, stretch=None)
    loaded = read_rsf(output_path)

    peak_times = np.argmax(loaded.data, axis=1) * 0.004
    np.testing.assert_allclose(peak_times, np.full(5, 0.4), atol=0.008)
    assert loaded.header.dimensions == (251, 5)
    assert loaded.header["nmo_half"] == "n"


def test_velocity_function_nmo_accepts_time_variant_velocity(tmp_path: Path) -> None:
    input_path = tmp_path / "cmp.rsf"
    vel_path = tmp_path / "vel.rsf"
    output_path = tmp_path / "nmo.rsf"
    data = _hyperbolic_gather()
    velocity = np.linspace(1900.0, 2100.0, 251, dtype=np.float32)
    write_rsf(input_path, data, _header())
    write_rsf(vel_path, velocity, _velocity_header())

    nmo_correct(input_path, vel_path, output_path, half=False, stretch=None)
    loaded = read_rsf(output_path)

    assert loaded.data.shape == data.shape
    assert np.max(loaded.data) > 0.9


def test_inverse_nmo_round_trip_constant_velocity(tmp_path: Path) -> None:
    input_path = tmp_path / "flat.rsf"
    nmo_path = tmp_path / "offset.rsf"
    restored_path = tmp_path / "restored.rsf"
    vel_path = _velocity_file(tmp_path / "vel.rsf")
    flat = np.zeros((5, 251), dtype=np.float32)
    flat[:, 100] = 1.0
    write_rsf(input_path, flat, _header())

    inverse_nmo(input_path, vel_path, nmo_path, half=False, stretch=None)
    nmo_correct(nmo_path, vel_path, restored_path, half=False, stretch=None)
    restored = read_rsf(restored_path)

    assert restored.data.shape == flat.shape
    assert np.argmax(restored.data[0]) == 100
    assert np.max(restored.data[:, 98:103]) > 0.8


def test_offset_file_overrides_offset_axis(tmp_path: Path) -> None:
    input_path = tmp_path / "cmp.rsf"
    vel_path = _velocity_file(tmp_path / "vel.rsf")
    offset_path = tmp_path / "offset.rsf"
    output_path = tmp_path / "nmo.rsf"
    data = _hyperbolic_gather()
    write_rsf(input_path, data, _header())
    write_rsf(offset_path, np.arange(5, dtype=np.float32) * 150.0, RSFHeader({"n1": 5}))

    nmo_correct(input_path, vel_path, output_path, offset=offset_path, half=False, stretch=None)
    loaded = read_rsf(output_path)

    peak_times = np.argmax(loaded.data, axis=1) * 0.004
    np.testing.assert_allclose(peak_times, np.full(5, 0.4), atol=0.008)


def test_stretch_mute_zeros_overstretched_early_samples(tmp_path: Path) -> None:
    input_path = tmp_path / "ones.rsf"
    vel_path = _velocity_file(tmp_path / "vel.rsf")
    output_path = tmp_path / "muted.rsf"
    data = np.ones((5, 251), dtype=np.float32)
    write_rsf(input_path, data, _header())

    nmo_correct(input_path, vel_path, output_path, half=False, stretch=0.5)
    loaded = read_rsf(output_path)

    assert loaded.data[-1, 1] == 0.0
    assert loaded.data[-1, 200] == pytest.approx(1.0)


def test_semblance_peak_is_near_true_velocity(tmp_path: Path) -> None:
    input_path = tmp_path / "cmp.rsf"
    output_path = tmp_path / "semblance.rsf"
    data = _hyperbolic_gather()
    write_rsf(input_path, data, _header())

    semblance_scan(input_path, output_path, vmin=1500.0, vmax=2500.0, dv=100.0, half=False, stretch=None, smooth=2)
    loaded = read_rsf(output_path)

    event_index = int(round(0.4 / 0.004))
    best_velocity_index = int(np.argmax(loaded.data[:, event_index]))
    best_velocity = float(loaded.header["o2"]) + best_velocity_index * float(loaded.header["d2"])
    assert best_velocity == pytest.approx(TRUE_VELOCITY, abs=100.0)
    assert loaded.header.dimensions == (251, 11)
    assert loaded.header["label2"] == "Velocity"


def test_semblance_preserves_extra_gather_axis(tmp_path: Path) -> None:
    input_path = tmp_path / "cube.rsf"
    output_path = tmp_path / "semblance.rsf"
    gather = _hyperbolic_gather(nt=101, nh=4, event_time=0.24)
    data = np.stack([gather, 0.5 * gather], axis=0).astype(np.float32)
    header = _header(nt=101, nh=4)
    header["n3"] = 2
    header["o3"] = 10.0
    header["d3"] = 1.0
    header["label3"] = "CMP"
    write_rsf(input_path, data, header)

    semblance_scan(input_path, output_path, vmin=1800.0, vmax=2200.0, dv=200.0, half=False, stretch=None)
    loaded = read_rsf(output_path)

    assert loaded.data.shape == (2, 3, 101)
    assert loaded.header.dimensions == (101, 3, 2)
    assert loaded.header["label3"] == "CMP"


def test_nmo_rejects_nonpositive_velocity(tmp_path: Path) -> None:
    input_path = tmp_path / "cmp.rsf"
    output_path = tmp_path / "bad.rsf"
    write_rsf(input_path, _hyperbolic_gather(), _header())

    with pytest.raises(NMOError, match="velocity values must be positive"):
        nmo_correct(input_path, 0.0, output_path, half=False)

    assert not output_path.exists()


def test_nmo_cli(tmp_path: Path) -> None:
    input_path = tmp_path / "cmp.rsf"
    vel_path = _velocity_file(tmp_path / "vel.rsf")
    output_path = tmp_path / "nmo.rsf"
    write_rsf(input_path, _hyperbolic_gather(), _header())

    code = nmo_main([str(input_path), str(vel_path), "out=" + str(output_path), "half=n", "stretch=0"])
    loaded = read_rsf(output_path)

    assert code == 0
    peak_times = np.argmax(loaded.data, axis=1) * 0.004
    np.testing.assert_allclose(peak_times, np.full(5, 0.4), atol=0.008)


def test_nmo_cli_accepts_scalar_velocity(tmp_path: Path) -> None:
    input_path = tmp_path / "cmp.rsf"
    output_path = tmp_path / "nmo.rsf"
    write_rsf(input_path, _hyperbolic_gather(), _header())

    code = nmo_main([str(input_path), "out=" + str(output_path), "velocity=2000", "half=n", "stretch=0"])

    assert code == 0
    assert read_rsf(output_path).header.dimensions == (251, 5)


def test_semblance_cli(tmp_path: Path) -> None:
    input_path = tmp_path / "cmp.rsf"
    output_path = tmp_path / "semblance.rsf"
    write_rsf(input_path, _hyperbolic_gather(), _header())

    code = semblance_main(
        [
            str(input_path),
            "out=" + str(output_path),
            "vmin=1800",
            "vmax=2200",
            "dv=100",
            "half=n",
            "stretch=0",
        ]
    )
    loaded = read_rsf(output_path)

    assert code == 0
    assert loaded.header.dimensions == (251, 5)
    assert loaded.header["o2"] == "1800"


def test_cli_reports_missing_velocity(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    input_path = tmp_path / "cmp.rsf"
    output_path = tmp_path / "bad.rsf"
    write_rsf(input_path, _hyperbolic_gather(), _header())

    code = nmo_main([str(input_path), "out=" + str(output_path)])

    assert code == 2
    assert "Missing required parameter: velocity=" in capsys.readouterr().err
    assert not output_path.exists()


def test_original_sfnmo_shape_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfnmo"):
        pytest.skip("Original Madagascar sfnmo is not installed")

    input_path = tmp_path / "cmp.rsf"
    vel_path = tmp_path / "vel.rsf"
    original_path = tmp_path / "original.rsf"
    write_rsf(input_path, np.ones((5, 251), dtype=np.float32), _header())
    _velocity_file(vel_path)

    run_original_madagascar(
        ["sfnmo", "in=cmp.rsf", "velocity=vel.rsf", "out=original.rsf", "half=n", "str=0"],
        cwd=tmp_path,
        require_program="sfnmo",
    )
    original = read_rsf(original_path)

    assert original.header.dimensions == (251, 5)


def test_original_sfvscan_shape_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfvscan"):
        pytest.skip("Original Madagascar sfvscan is not installed")

    input_path = tmp_path / "cmp.rsf"
    original_path = tmp_path / "original.rsf"
    write_rsf(input_path, _hyperbolic_gather(), _header())

    run_original_madagascar(
        [
            "sfvscan",
            "in=cmp.rsf",
            "out=original.rsf",
            "v0=1800",
            "dv=100",
            "nv=5",
            "semblance=y",
            "half=n",
            "str=0",
        ],
        cwd=tmp_path,
        require_program="sfvscan",
    )
    original = read_rsf(original_path)

    assert original.header.dimensions == (251, 5)
