from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys

import numpy as np
import pytest

from pymadagascar import RSFData
from pymadagascar.generic.sampling import (
    SamplingError,
    bin_2d,
    bin_rsf,
    linear_resample,
    linear_rsf,
    max1,
    max1_rsf,
    slice_array,
    slice_rsf,
)
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf
from pymadagascar.testing.runner import original_madagascar_available


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _run_cli(module: str, args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = (
        str(PROJECT_ROOT)
        if not env.get("PYTHONPATH")
        else str(PROJECT_ROOT) + os.pathsep + env["PYTHONPATH"]
    )
    return subprocess.run(
        [sys.executable, "-m", f"pymadagascar.cli.{module}", *args],
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def _header_1d(n1: int, *, o1: float = 0.0, d1: float = 1.0) -> RSFHeader:
    return RSFHeader({"n1": n1, "o1": o1, "d1": d1, "label1": "Time", "unit1": "s"})


def _header_2d(n1: int, n2: int, *, d1: float = 1.0) -> RSFHeader:
    header = _header_1d(n1, d1=d1)
    header["n2"] = n2
    header["o2"] = 0.0
    header["d2"] = 1.0
    header["label2"] = "Trace"
    return header


def _header_3d(n1: int, n2: int, n3: int) -> RSFHeader:
    header = _header_2d(n1, n2)
    header["n3"] = n3
    header["o3"] = 100.0
    header["d3"] = 10.0
    header["label3"] = "Shot"
    return header


def test_linear_resample_1d_function_and_boundary_fill() -> None:
    data = np.arange(4, dtype=np.float32)

    result = linear_resample(data, n=7, o=0.0, d=0.5)
    outside = linear_resample(data, n=6, o=-1.0, d=1.0, fill=-9.0)

    np.testing.assert_allclose(result, np.arange(7, dtype=np.float32) * 0.5)
    np.testing.assert_allclose(outside, np.array([-9.0, 0.0, 1.0, 2.0, 3.0, -9.0], dtype=np.float32))
    assert result.dtype == np.dtype("float32")


def test_linear_resample_2d_axes_and_header(tmp_path: Path) -> None:
    along_axis1 = np.vstack([np.arange(4), np.arange(4) + 10]).astype(np.float32)
    along_axis2 = np.array([[0.0, 10.0], [1.0, 11.0], [2.0, 12.0]], dtype=np.float32)

    resampled_axis1 = linear_resample(along_axis1, axis=1, n=7, d=0.5)
    resampled_axis2 = linear_resample(along_axis2, axis=2, n=5, d=0.5)

    np.testing.assert_allclose(resampled_axis1[0], np.arange(7) * 0.5)
    np.testing.assert_allclose(resampled_axis2[:, 0], np.arange(5) * 0.5)
    np.testing.assert_allclose(resampled_axis2[:, 1], 10.0 + np.arange(5) * 0.5)

    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "linear.rsf"
    write_rsf(input_path, along_axis1, _header_2d(n1=4, n2=2))
    linear_rsf(input_path, output_path, axis=1, n=7, o=0.0, d=0.5)
    loaded = read_rsf(output_path)

    assert loaded.data.shape == (2, 7)
    assert loaded.header.dimensions == (7, 2)
    assert loaded.header["d1"] == "0.5"
    assert loaded.header["label1"] == "Time"


def test_linear_cli_subprocess(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "linear_cli.rsf"
    write_rsf(input_path, np.arange(4, dtype=np.float32), _header_1d(4))

    result = _run_cli(
        "linear",
        [str(input_path), "out=" + str(output_path), "axis=1", "n=7", "o=0", "d=0.5"],
        tmp_path,
    )

    assert result.returncode == 0, result.stderr
    np.testing.assert_allclose(read_rsf(output_path).data, np.arange(7, dtype=np.float32) * 0.5)


def test_bin_2d_mean_sum_count_empty_and_out_of_bounds() -> None:
    x = np.array([0.2, 0.3, 1.2, 99.0], dtype=np.float32)
    y = np.array([0.2, 0.3, 0.3, 0.2], dtype=np.float32)
    values = np.array([1.0, 3.0, 5.0, 7.0], dtype=np.float32)

    mean = bin_2d(x, y, values, n1=3, o1=0.0, d1=1.0, n2=2, o2=0.0, d2=1.0, fill=-1.0)
    summed = bin_2d(
        x,
        y,
        values,
        n1=3,
        o1=0.0,
        d1=1.0,
        n2=2,
        o2=0.0,
        d2=1.0,
        statistic="sum",
        fill=-1.0,
    )
    count = bin_2d(
        x,
        y,
        values,
        n1=3,
        o1=0.0,
        d1=1.0,
        n2=2,
        o2=0.0,
        d2=1.0,
        statistic="count",
        fill=-1.0,
    )

    np.testing.assert_allclose(mean, np.array([[2.0, 5.0, -1.0], [-1.0, -1.0, -1.0]], dtype=np.float32))
    np.testing.assert_allclose(summed[0], np.array([4.0, 5.0, -1.0], dtype=np.float32))
    np.testing.assert_allclose(count[0], np.array([2.0, 1.0, -1.0], dtype=np.float32))


def test_bin_rsf_and_cli_subprocess(tmp_path: Path) -> None:
    points = np.array([[0.2, 0.2, 1.0], [0.3, 0.3, 3.0], [1.2, 0.3, 5.0]], dtype=np.float32)
    input_path = tmp_path / "points.rsf"
    api_path = tmp_path / "grid_api.rsf"
    cli_path = tmp_path / "grid_cli.rsf"
    write_rsf(input_path, points, RSFHeader({"n1": 3, "n2": 3, "label1": "Column", "label2": "Point"}))

    bin_rsf(input_path, api_path, n1=3, o1=0.0, d1=1.0, n2=2, o2=0.0, d2=1.0, fill=-1.0)
    result = _run_cli(
        "bin",
        [
            str(input_path),
            "out=" + str(cli_path),
            "n1=3",
            "o1=0",
            "d1=1",
            "n2=2",
            "o2=0",
            "d2=1",
            "statistic=count",
        ],
        tmp_path,
    )

    assert result.returncode == 0, result.stderr
    loaded = read_rsf(api_path)
    assert loaded.header.dimensions == (3, 2)
    np.testing.assert_allclose(loaded.data[0], np.array([2.0, 5.0, -1.0], dtype=np.float32))
    np.testing.assert_allclose(read_rsf(cli_path).data[0], np.array([2.0, 1.0, 0.0], dtype=np.float32))


def test_slice_array_2d_3d_header_and_out_of_bounds(tmp_path: Path) -> None:
    data2 = np.arange(12, dtype=np.float32).reshape(3, 4)
    data3 = np.arange(24, dtype=np.float32).reshape(2, 3, 4)
    input_path = tmp_path / "cube.rsf"
    output_path = tmp_path / "slice.rsf"

    np.testing.assert_allclose(slice_array(data2, axis=1, index=2), np.array([2, 6, 10], dtype=np.float32))
    np.testing.assert_allclose(slice_array(data3, axis=2, index=1), data3[:, 1, :])
    write_rsf(input_path, data3, _header_3d(n1=4, n2=3, n3=2))
    slice_rsf(input_path, output_path, axis=2, index=1)
    loaded = read_rsf(output_path)

    assert loaded.data.shape == (2, 4)
    assert loaded.header.dimensions == (4, 2)
    assert loaded.header["label1"] == "Time"
    assert loaded.header["label2"] == "Shot"
    assert "n3" not in loaded.header.params
    with pytest.raises(SamplingError, match="outside"):
        slice_array(data2, axis=1, index=4)


def test_slice_cli_subprocess(tmp_path: Path) -> None:
    input_path = tmp_path / "cube.rsf"
    output_path = tmp_path / "slice_cli.rsf"
    data = np.arange(24, dtype=np.float32).reshape(2, 3, 4)
    write_rsf(input_path, data, _header_3d(n1=4, n2=3, n3=2))

    result = _run_cli("slice", [str(input_path), "out=" + str(output_path), "axis=3", "index=1"], tmp_path)

    assert result.returncode == 0, result.stderr
    np.testing.assert_allclose(read_rsf(output_path).data, data[1])


def test_max1_modes_axes_abs_and_nan_policy() -> None:
    data = np.array([[1.0, 5.0, 2.0], [3.0, 2.0, 4.0]], dtype=np.float32)

    np.testing.assert_allclose(max1(data, axis=1, mode="value"), np.array([5.0, 4.0], dtype=np.float32))
    np.testing.assert_allclose(max1(data, axis=2, mode="value"), np.array([3.0, 5.0, 4.0], dtype=np.float32))
    np.testing.assert_allclose(max1(data, axis=1, mode="index"), np.array([1.0, 2.0], dtype=np.float32))
    np.testing.assert_allclose(
        max1(data, axis=1, mode="coord", input_o=10.0, input_d=0.5),
        np.array([10.5, 11.0], dtype=np.float32),
    )
    np.testing.assert_allclose(
        max1(np.array([-5.0, 4.0, 3.0], dtype=np.float32), abs_search=True),
        np.array(-5.0, dtype=np.float32),
    )

    nan_data = np.array([[1.0, np.nan, 2.0], [np.nan, np.nan, np.nan]], dtype=np.float32)
    assert np.isnan(max1(nan_data, axis=1, nan_policy="propagate")).all()
    omit = max1(nan_data, axis=1, nan_policy="omit")
    np.testing.assert_allclose(omit[0], 2.0)
    assert np.isnan(omit[1])


def test_max1_rsf_header_and_cli(tmp_path: Path) -> None:
    input_path = tmp_path / "panel.rsf"
    api_path = tmp_path / "max_api.rsf"
    cli_path = tmp_path / "max_cli.rsf"
    data = np.array([[1.0, 5.0, 2.0], [3.0, 2.0, 4.0]], dtype=np.float32)
    write_rsf(input_path, data, _header_2d(n1=3, n2=2, d1=0.5))

    max1_rsf(input_path, api_path, axis=1, mode="coord")
    result = _run_cli(
        "max1",
        [str(input_path), "out=" + str(cli_path), "axis=1", "mode=index"],
        tmp_path,
    )

    assert result.returncode == 0, result.stderr
    loaded = read_rsf(api_path)
    assert loaded.data.shape == (2,)
    assert loaded.header.dimensions == (2,)
    assert loaded.header["label1"] == "Trace"
    assert loaded.header["max1_mode"] == "coord"
    np.testing.assert_allclose(loaded.data, np.array([0.5, 1.0], dtype=np.float32))
    np.testing.assert_allclose(read_rsf(cli_path).data, np.array([1.0, 2.0], dtype=np.float32))


def test_rsfdata_generic_sampling_methods_do_not_modify_original() -> None:
    panel = np.vstack([np.arange(4), np.arange(4) + 10]).astype(np.float32)
    cube = np.arange(24, dtype=np.float32).reshape(2, 3, 4)
    rsf = RSFData(panel, _header_2d(n1=4, n2=2))
    cube_rsf = RSFData(cube, _header_3d(n1=4, n2=3, n3=2))

    resampled = rsf.linear(axis=1, n=7, d=0.5)
    picked = rsf.max1(axis=1, mode="index")
    sliced = cube_rsf.slice(axis=3, index=1)

    np.testing.assert_allclose(rsf.numpy(), panel)
    assert resampled.shape == (2, 7)
    assert resampled.header["d1"] == "0.5"
    np.testing.assert_allclose(picked.numpy(), np.array([3.0, 3.0], dtype=np.float32))
    np.testing.assert_allclose(sliced.numpy(), cube[1])


def test_invalid_parameters_raise_clear_errors(tmp_path: Path) -> None:
    with pytest.raises(SamplingError, match="real-valued"):
        linear_resample(np.ones(4, dtype=np.complex64), n=8)
    with pytest.raises(SamplingError, match="positive"):
        bin_2d([0], [0], [1], n1=1, o1=0.0, d1=0.0, n2=1, o2=0.0, d2=1.0)
    with pytest.raises(SamplingError, match="axis"):
        max1(np.ones((2, 2), dtype=np.float32), axis=3)

    points = tmp_path / "points.rsf"
    write_rsf(points, np.ones((2, 2), dtype=np.float32), RSFHeader({"n1": 2, "n2": 2}))
    with pytest.raises(SamplingError, match="column"):
        bin_rsf(points, tmp_path / "bad.rsf", value=3, n1=1, o1=0.0, d1=1.0, n2=1, o2=0.0, d2=1.0)


@pytest.mark.parametrize("program", ["sflinear", "sfbin", "sfslice", "sfmax1"])
@pytest.mark.original_madagascar
def test_original_stage_c2_commands_are_optional(program: str) -> None:
    if not original_madagascar_available(program):
        pytest.skip(f"Original Madagascar {program} is not installed")
    pytest.skip(
        f"Original {program} is not directly compared here because the Stage C-2 "
        "subset intentionally uses a smaller Pythonic parameter surface"
    )
