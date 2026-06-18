from pathlib import Path

import numpy as np
import pytest

from pymadagascar.cli.kirchhoff import main as kirchhoff_main
from pymadagascar.imaging.kirchhoff import (
    ImagingError,
    kirchhoff_time_migration,
    kirchhoff_time_migration_array,
)
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf
from pymadagascar.testing.runner import original_madagascar_available, run_original_madagascar


VELOCITY = 2000.0


def _header(nt: int = 121, nx: int = 41, dt: float = 0.004, dx: float = 25.0) -> RSFHeader:
    x0 = -0.5 * (nx - 1) * dx
    return RSFHeader(
        {
            "n1": nt,
            "o1": 0.0,
            "d1": dt,
            "label1": "Time",
            "unit1": "s",
            "n2": nx,
            "o2": x0,
            "d2": dx,
            "label2": "Midpoint",
            "unit2": "m",
        }
    )


def _diffraction(
    *,
    nt: int = 121,
    nx: int = 41,
    dt: float = 0.004,
    dx: float = 25.0,
    x0: float = 0.0,
    tau0: float = 0.24,
    velocity: float = VELOCITY,
    sigma: float = 0.006,
) -> np.ndarray:
    time = dt * np.arange(nt, dtype=np.float64)
    x = -0.5 * (nx - 1) * dx + dx * np.arange(nx, dtype=np.float64)
    data = np.zeros((nx, nt), dtype=np.float32)
    for ix, xpos in enumerate(x):
        travel = np.sqrt(tau0 * tau0 + (2.0 * (xpos - x0) / velocity) ** 2)
        data[ix] = np.exp(-0.5 * ((time - travel) / sigma) ** 2).astype(np.float32)
    return data


def test_small_model_runs_without_nan(tmp_path: Path) -> None:
    input_path = tmp_path / "small.rsf"
    output_path = tmp_path / "image.rsf"
    data = np.zeros((9, 31), dtype=np.float32)
    data[4, 10] = 1.0
    write_rsf(input_path, data, _header(nt=31, nx=9, dx=20.0))

    kirchhoff_time_migration(input_path, output_path, velocity=VELOCITY, normalize=True)
    image = read_rsf(output_path)

    assert image.data.shape == data.shape
    assert np.all(np.isfinite(image.data))


def test_single_diffraction_images_near_true_point(tmp_path: Path) -> None:
    input_path = tmp_path / "diffraction.rsf"
    output_path = tmp_path / "image.rsf"
    data = _diffraction(x0=0.0, tau0=0.24)
    write_rsf(input_path, data, _header())

    kirchhoff_time_migration(input_path, output_path, velocity=VELOCITY, normalize=True)
    image = read_rsf(output_path)
    peak = np.unravel_index(int(np.argmax(image.data)), image.data.shape)

    assert abs(peak[0] - 20) <= 1
    assert abs(peak[1] - 60) <= 2
    assert image.data[peak] > 0.5


def test_output_shape_matches_input(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "image.rsf"
    data = _diffraction(nt=81, nx=17, tau0=0.16)
    write_rsf(input_path, data, _header(nt=81, nx=17))

    kirchhoff_time_migration(input_path, output_path, velocity=VELOCITY)
    image = read_rsf(output_path)

    assert image.data.shape == (17, 81)
    assert image.header.dimensions == (81, 17)


def test_header_updates_axis_labels_and_metadata(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "image.rsf"
    write_rsf(input_path, _diffraction(), _header())

    kirchhoff_time_migration(input_path, output_path, velocity=VELOCITY, aperture=250.0, normalize=True)
    image = read_rsf(output_path)

    assert image.header["label1"] == "Migrated Time"
    assert image.header["label2"] == "Image X"
    assert image.header["kirchhoff_algorithm"] == "poststack_time"
    assert image.header["kirchhoff_velocity"] == "2000"
    assert image.header["kirchhoff_aperture"] == "250"
    assert image.header["kirchhoff_normalize"] == "y"


def test_velocity_file_is_supported(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    velocity_path = tmp_path / "velocity.rsf"
    output_path = tmp_path / "image.rsf"
    data = _diffraction()
    header = _header()
    write_rsf(input_path, data, header)
    write_rsf(velocity_path, np.full(121, VELOCITY, dtype=np.float32), RSFHeader({"n1": 121, "d1": 0.004}))

    kirchhoff_time_migration(input_path, output_path, velocity=velocity_path, normalize=True)
    image = read_rsf(output_path)

    peak = np.unravel_index(int(np.argmax(image.data)), image.data.shape)
    assert abs(peak[0] - 20) <= 1
    assert image.header["kirchhoff_velocity"].endswith("velocity.rsf")


def test_array_api_rejects_bad_velocity() -> None:
    data = np.ones((3, 5), dtype=np.float32)
    time = np.arange(5, dtype=np.float64)
    x = np.arange(3, dtype=np.float64)

    with pytest.raises(ImagingError, match="positive"):
        kirchhoff_time_migration_array(data, time, x, 0.0)


def test_kirchhoff_rejects_3d_input(tmp_path: Path) -> None:
    input_path = tmp_path / "cube.rsf"
    output_path = tmp_path / "bad.rsf"
    header = _header(nt=11, nx=5)
    header["n3"] = 2
    write_rsf(input_path, np.ones((2, 5, 11), dtype=np.float32), header)

    with pytest.raises(ImagingError, match="2D input"):
        kirchhoff_time_migration(input_path, output_path, velocity=VELOCITY)

    assert not output_path.exists()


def test_kirchhoff_cli(tmp_path: Path) -> None:
    input_path = tmp_path / "diffraction.rsf"
    output_path = tmp_path / "image.rsf"
    write_rsf(input_path, _diffraction(), _header())

    code = kirchhoff_main(
        [str(input_path), "out=" + str(output_path), "velocity=2000", "normalize=y"]
    )
    image = read_rsf(output_path)

    assert code == 0
    assert image.header["label1"] == "Migrated Time"
    peak = np.unravel_index(int(np.argmax(image.data)), image.data.shape)
    assert abs(peak[0] - 20) <= 1


def test_kirchhoff_cli_reports_missing_velocity(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "bad.rsf"
    write_rsf(input_path, _diffraction(), _header())

    code = kirchhoff_main([str(input_path), "out=" + str(output_path)])

    assert code == 2
    assert "Missing required parameter: velocity=" in capsys.readouterr().err
    assert not output_path.exists()


def test_original_sfkirchnew_shape_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfkirchnew"):
        pytest.skip("Original Madagascar sfkirchnew is not installed")

    input_path = tmp_path / "input.rsf"
    original_path = tmp_path / "original.rsf"
    data = _diffraction()
    write_rsf(input_path, data, _header())

    run_original_madagascar(
        ["sfkirchnew", "in=input.rsf", "out=original.rsf", "adj=y", "hd=n", "v0=2000"],
        cwd=tmp_path,
        require_program="sfkirchnew",
    )
    original = read_rsf(original_path)

    assert original.header.dimensions == (121, 41)
