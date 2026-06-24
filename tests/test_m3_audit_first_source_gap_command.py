from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

import pymadagascar
from pymadagascar import RSFData
from pymadagascar.generic.polymask import PolyMaskError, polymask, polymask_rsf
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf


ROOT = Path(__file__).resolve().parents[1]


def _grid_header() -> RSFHeader:
    return RSFHeader({"n1": 5, "o1": 0.0, "d1": 1.0, "n2": 4, "o2": 0.0, "d2": 1.0})


def _poly_header(vertices: np.ndarray) -> RSFHeader:
    return RSFHeader({"n1": 2, "n2": vertices.shape[1]})


def test_polymask_values_rsfdata_cli_and_no_inplace(tmp_path: Path) -> None:
    # 2-D grid fixture: RSF n1=5,n2=4 对应 NumPy shape=(4,5)。
    # polygon 顶点表使用 upstream poly= 约定：n1=2 为 x/y，n2=nv 为顶点个数。
    grid = np.arange(20, dtype=np.float32).reshape(4, 5)
    vertices = np.array([[1.0, 4.0, 4.0, 1.0], [1.0, 1.0, 3.0, 3.0]], dtype=np.float32)
    expected = np.zeros((4, 5), dtype=np.int32)
    # Franklin pnpoly crossing rule 不把所有边界点统一算作 inside；
    # 对这个矩形，内部 mask 落在 y index 1..2、x index 1..3。
    expected[1:3, 1:4] = 1

    np.testing.assert_array_equal(polymask(grid.shape, vertices), expected)
    np.testing.assert_array_equal(grid, np.arange(20, dtype=np.float32).reshape(4, 5))

    input_path = tmp_path / "grid.rsf"
    poly_path = tmp_path / "poly.rsf"
    output_path = tmp_path / "mask.rsf"
    cli_path = tmp_path / "mask_cli.rsf"
    write_rsf(input_path, grid, _grid_header())
    write_rsf(poly_path, vertices, _poly_header(vertices))
    polymask_rsf(input_path, poly_path, output_path)
    rsf = read_rsf(output_path)
    np.testing.assert_array_equal(rsf.data, expected)
    assert rsf.header["polymask_source"] == "../src-master/system/generic/Mpolymask.c"
    assert rsf.header.dimensions == (5, 4)

    source = RSFData(grid, _grid_header())
    chained = source.polymask(poly_path)
    # RSFData.polymask 读取 poly= side input 并返回新 mask dataset，不改原 grid。
    assert chained is not source
    np.testing.assert_array_equal(chained.numpy(), expected)
    np.testing.assert_array_equal(source.numpy(), grid)

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pymadagascar.cli.polymask",
            str(input_path),
            f"out={cli_path}",
            f"poly={poly_path}",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=20,
    )
    assert completed.returncode == 0, completed.stderr + completed.stdout
    np.testing.assert_array_equal(read_rsf(cli_path).data, expected)
    assert not hasattr(pymadagascar, "polymask_rsf")


def test_polymask_invalid_params_and_help(tmp_path: Path) -> None:
    # invalid params 覆盖 bounded subset 边界：只支持 2-D RSF grid、
    # 至少三个有限顶点，以及 float RSF vertex table。
    with pytest.raises(PolyMaskError, match="2-D grid"):
        polymask((3, 3, 1), np.zeros((2, 3), dtype=np.float32))
    with pytest.raises(PolyMaskError, match="at least three"):
        polymask((3, 3), np.zeros((2, 2), dtype=np.float32))
    with pytest.raises(PolyMaskError, match="finite"):
        polymask((3, 3), np.array([[0.0, 1.0, np.nan], [0.0, 0.0, 1.0]]))

    input_path = tmp_path / "grid.rsf"
    poly_path = tmp_path / "poly.rsf"
    output_path = tmp_path / "mask.rsf"
    write_rsf(input_path, np.ones((1, 3, 3), dtype=np.float32), RSFHeader({"n1": 3, "n2": 3, "n3": 1}))
    write_rsf(poly_path, np.zeros((2, 3), dtype=np.float32), RSFHeader({"n1": 2, "n2": 3}))
    with pytest.raises(PolyMaskError, match="2-D RSF"):
        polymask_rsf(input_path, poly_path, output_path)

    help_result = subprocess.run(
        [sys.executable, "-m", "pymadagascar.cli.polymask", "--help"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=20,
    )
    assert help_result.returncode == 0, help_result.stderr + help_result.stdout
    assert "Mpolymask.c" in help_result.stdout
