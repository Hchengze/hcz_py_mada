from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from pymadagascar import RSFData
from pymadagascar.generic.edge import EdgeError, grad2, grad2_rsf, grad3, grad3_rsf
from pymadagascar.generic.lpad import LPadError, lpad, lpad_rsf
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf


ROOT = Path(__file__).resolve().parents[1]


def _header_2d(n1: int, n2: int) -> RSFHeader:
    return RSFHeader({"n1": n1, "n2": n2, "o1": 0.0, "d1": 1.0, "o2": 10.0, "d2": 2.0})


def _header_3d(n1: int, n2: int, n3: int) -> RSFHeader:
    header = _header_2d(n1, n2)
    header["n3"] = n3
    header["o3"] = -1.0
    header["d3"] = 0.5
    return header


def test_grad2_numeric_rsf_rsfdata_and_no_inplace(tmp_path: Path) -> None:
    # 2-D RSF plane: NumPy shape=(n2,n1)。线性斜坡让 Sobel stencil 在内部
    # 得到常数 gradient squared，外圈保持 edge.c 的 zero-edge 行为。
    data = np.arange(25, dtype=np.float32).reshape(5, 5)
    expected = np.zeros_like(data)
    expected[1:-1, 1:-1] = 1664.0

    result = grad2(data)
    np.testing.assert_array_equal(result, expected)
    np.testing.assert_array_equal(data, np.arange(25, dtype=np.float32).reshape(5, 5))

    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "grad2.rsf"
    write_rsf(input_path, data, _header_2d(n1=5, n2=5))
    grad2_rsf(input_path, output_path)
    rsf = read_rsf(output_path)
    np.testing.assert_array_equal(rsf.data, expected)
    assert rsf.header["grad2_source"] == "../src-master/system/generic/Mgrad2.c"
    assert rsf.header.dimensions == (5, 5)

    source = RSFData(data, _header_2d(n1=5, n2=5))
    chained = source.grad2()
    assert chained is not source
    np.testing.assert_array_equal(chained.numpy(), expected)
    np.testing.assert_array_equal(source.numpy(), data)


def test_grad3_numeric_rsf_rsfdata_and_cli(tmp_path: Path) -> None:
    # 3-D RSF block: NumPy shape=(n3,n2,n1)。
    # dim=0 验证梯度平方，dim=1/2/3 分别验证 edge.c 的三个 Sobel component。
    data = np.arange(125, dtype=np.float32).reshape(5, 5, 5)
    squared = grad3(data, dim=0)
    component = grad3(data, dim=1)
    assert float(squared[2, 2, 2]) == pytest.approx(41664.0, rel=1e-6)
    assert float(component[2, 2, 2]) == pytest.approx(8.0)
    assert np.count_nonzero(squared[[0, -1], :, :]) == 0

    input_path = tmp_path / "input3.rsf"
    output_path = tmp_path / "grad3.rsf"
    write_rsf(input_path, data, _header_3d(n1=5, n2=5, n3=5))
    grad3_rsf(input_path, output_path, dim=2)
    rsf = read_rsf(output_path)
    assert float(rsf.data[2, 2, 2]) == pytest.approx(40.0)
    assert rsf.header["grad3_source"] == "../src-master/system/generic/Mgrad3.c"
    assert rsf.header["grad3_dim"] == "2"

    source = RSFData(data, _header_3d(n1=5, n2=5, n3=5))
    chained = source.grad3(dim=3)
    assert chained is not source
    assert float(chained.numpy()[2, 2, 2]) == pytest.approx(200.0)
    np.testing.assert_array_equal(source.numpy(), data)

    cli_output = tmp_path / "cli_grad3.rsf"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pymadagascar.cli.grad3",
            str(input_path),
            f"out={cli_output}",
            "dim=1",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=20,
    )
    assert completed.returncode == 0, completed.stderr + completed.stdout
    assert float(read_rsf(cli_output).data[2, 2, 2]) == pytest.approx(8.0)


def test_lpad_numeric_rsf_mask_rsfdata_and_cli(tmp_path: Path) -> None:
    # sflpad fixture: RSF axes 为 n1=2,n2=3,n3=4，对应 NumPy shape=(4,3,2)。
    # jump=2 后只在 axis2/axis3 的偶数位置保留原 trace/plane，其余补零。
    data = np.arange(2 * 3 * 4, dtype=np.float32).reshape(4, 3, 2)
    result = lpad(data, jump=2)
    expected = np.zeros((8, 6, 2), dtype=np.float32)
    expected[::2, ::2, :] = data
    expected_mask = np.zeros((8, 6, 2), dtype=np.int32)
    expected_mask[::2, ::2, :] = 1
    # mask side output 中 1 表示 upstream Mlpad.c 保留的原始样点位置。
    np.testing.assert_array_equal(result.data, expected)
    np.testing.assert_array_equal(result.mask, expected_mask)
    np.testing.assert_array_equal(data, np.arange(24, dtype=np.float32).reshape(4, 3, 2))

    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "lpad.rsf"
    mask_path = tmp_path / "mask.rsf"
    write_rsf(input_path, data, _header_3d(n1=2, n2=3, n3=4))
    lpad_rsf(input_path, output_path, jump=2, mask=mask_path)
    rsf = read_rsf(output_path)
    mask = read_rsf(mask_path)
    np.testing.assert_array_equal(rsf.data, expected)
    np.testing.assert_array_equal(mask.data, expected_mask)
    assert rsf.header.dimensions == (2, 6, 8)
    assert rsf.header["d2"] == "1"
    assert rsf.header["d3"] == "0.25"
    assert rsf.header["lpad_source"] == "../src-master/system/generic/Mlpad.c"

    source = RSFData(data, _header_3d(n1=2, n2=3, n3=4))
    chained = source.lpad(jump=2)
    assert chained is not source
    np.testing.assert_array_equal(chained.numpy(), expected)
    np.testing.assert_array_equal(source.numpy(), data)

    cli_output = tmp_path / "cli_lpad.rsf"
    cli_mask = tmp_path / "cli_mask.rsf"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pymadagascar.cli.lpad",
            str(input_path),
            f"out={cli_output}",
            f"mask={cli_mask}",
            "jump=2",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=20,
    )
    assert completed.returncode == 0, completed.stderr + completed.stdout
    np.testing.assert_array_equal(read_rsf(cli_output).data, expected)
    np.testing.assert_array_equal(read_rsf(cli_mask).data, expected_mask)


def test_second_gap_invalid_params_and_help(tmp_path: Path) -> None:
    # 参数错误覆盖 source-backed bounded subset 的边界：
    # grad2/grad3 需要足够维度，lpad 需要至少 RSF axis1/axis2 和正 jump。
    with pytest.raises(EdgeError, match="at least two axes"):
        grad2(np.ones(4, dtype=np.float32))
    with pytest.raises(EdgeError, match="dim"):
        grad3(np.ones((3, 3, 3), dtype=np.float32), dim=4)
    with pytest.raises(EdgeError, match="real-valued"):
        grad2(np.ones((3, 3), dtype=np.complex64))
    with pytest.raises(LPadError, match="jump"):
        lpad(np.ones((2, 2), dtype=np.float32), jump=0)
    with pytest.raises(LPadError, match="at least two"):
        lpad(np.ones(4, dtype=np.float32))

    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "output.rsf"
    write_rsf(input_path, np.ones((3, 3), dtype=np.float32), _header_2d(n1=3, n2=3))
    failed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pymadagascar.cli.grad2",
            str(input_path),
            f"out={output_path}",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=20,
    )
    assert failed.returncode == 0, failed.stderr + failed.stdout

    for module in ("grad2", "grad3", "lpad"):
        help_result = subprocess.run(
            [sys.executable, "-m", f"pymadagascar.cli.{module}", "--help"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
            timeout=20,
        )
        assert help_result.returncode == 0, help_result.stderr + help_result.stdout
        assert "src-master" in help_result.stdout.lower()
