from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys

import numpy as np
import pytest

import pymadagascar
from pymadagascar.api import RSFData
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf
from pymadagascar.seismic.gather import (
    GatherError,
    cmp2shot,
    cmp2shot_rsf,
    intbin,
    intbin3,
    intbin3_rsf,
    intbin_rsf,
    shot2cmp,
    shot2cmp_rsf,
)


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
        timeout=30,
    )


def _cmp_header(nt: int, nh: int, ny: int) -> RSFHeader:
    return RSFHeader(
        {
            "n1": nt,
            "o1": 0.0,
            "d1": 0.004,
            "label1": "Time",
            "unit1": "s",
            "n2": nh,
            "o2": 0.0,
            "d2": 2.0,
            "label2": "Offset",
            "n3": ny,
            "o3": 10.0,
            "d3": 1.0,
            "label3": "CMP",
        }
    )


def _shot_header(nt: int, nh: int, ns: int) -> RSFHeader:
    return RSFHeader(
        {
            "n1": nt,
            "o1": 0.0,
            "d1": 0.004,
            "label1": "Time",
            "unit1": "s",
            "n2": nh,
            "o2": 0.0,
            "d2": 1.0,
            "label2": "Offset",
            "n3": ns,
            "o3": 8.0,
            "d3": 2.0,
            "label3": "Shot",
        }
    )


def _trace_header(nt: int, ntr: int) -> RSFHeader:
    return RSFHeader(
        {
            "n1": nt,
            "o1": 0.0,
            "d1": 0.004,
            "label1": "Time",
            "unit1": "s",
            "n2": ntr,
            "o2": 0,
            "d2": 1,
            "label2": "Trace",
        }
    )


def _header_table_header(nkey: int, ntr: int) -> RSFHeader:
    return RSFHeader(
        {
            "n1": nkey,
            "o1": 0,
            "d1": 1,
            "label1": "Key",
            "n2": ntr,
            "o2": 0,
            "d2": 1,
            "label2": "Trace",
        }
    )


def test_cmp2shot_values_header_chain_cli_and_invalid_params(tmp_path: Path) -> None:
    # CMP gather fixture: RSF axes n1=time,n2=offset,n3=CMP；
    # NumPy shape=(n_cmp,n_offset,n_time)。dh/dy=2 对应 upstream 的 integer type。
    data = np.arange(4 * 2 * 3, dtype=np.float32).reshape(4, 2, 3)
    input_path = tmp_path / "cmp.rsf"
    output_path = tmp_path / "shot.rsf"
    cli_path = tmp_path / "shot_cli.rsf"
    write_rsf(input_path, data, _cmp_header(nt=3, nh=2, ny=4))

    direct = cmp2shot(data, dh=2.0, dy=1.0, oh=0.0, oy=10.0, positive=True)
    original = RSFData(data, _cmp_header(nt=3, nh=2, ny=4))
    chained = original.cmp2shot()
    cmp2shot_rsf(input_path, output_path)
    result = _run_cli("cmp2shot", [str(input_path), "out=" + str(cli_path)], tmp_path)

    expected = np.zeros((3, 4, 3), dtype=np.float32)
    # expected 逐项复现 Mcmp2shot.c 的规则 geometry 索引关系；
    # 没有对应 shot/offset 的位置保持零填充。
    for ishot in range(3):
        for ioffset in range(2):
            for itype in range(2):
                icmp = itype + 2 * (ishot + ioffset - 1)
                if 0 <= icmp < 4:
                    expected[ishot, ioffset * 2 + itype] = data[icmp, ioffset]
    assert result.returncode == 0, result.stderr
    np.testing.assert_array_equal(direct, expected)
    np.testing.assert_array_equal(read_rsf(output_path).data, expected)
    np.testing.assert_array_equal(read_rsf(cli_path).data, expected)
    np.testing.assert_array_equal(chained.numpy(), expected)
    np.testing.assert_array_equal(original.numpy(), data)
    header = read_rsf(output_path).header
    assert header.dimensions == (3, 4, 3)
    assert header["label3"] == "Shot"
    assert header["cmp2shot_source"] == "../src-master/system/seismic/Mcmp2shot.c"
    assert not hasattr(pymadagascar, "cmp2shot_rsf")
    with pytest.raises(GatherError, match="shape"):
        cmp2shot(data[0], dh=2.0, dy=1.0, oh=0.0, oy=10.0)
    with pytest.raises(GatherError, match="dh/dy"):
        cmp2shot(data, dh=1.5, dy=1.0, oh=0.0, oy=10.0)


def test_shot2cmp_values_header_chain_cli_and_invalid_params(tmp_path: Path) -> None:
    # Shot gather fixture: RSF axes n1=time,n2=offset,n3=shot；
    # NumPy shape=(n_shot,n_offset,n_time)。M3-5 subset 只验证 half=y。
    data = np.arange(3 * 4 * 2, dtype=np.float32).reshape(3, 4, 2)
    input_path = tmp_path / "shot.rsf"
    output_path = tmp_path / "cmp.rsf"
    cli_path = tmp_path / "cmp_cli.rsf"
    write_rsf(input_path, data, _shot_header(nt=2, nh=4, ns=3))

    direct = shot2cmp(data, dh=1.0, ds=2.0, oh=0.0, os=8.0, positive=True)
    original = RSFData(data, _shot_header(nt=2, nh=4, ns=3))
    chained = original.shot2cmp()
    shot2cmp_rsf(input_path, output_path)
    result = _run_cli("shot2cmp", [str(input_path), "out=" + str(cli_path)], tmp_path)

    expected = np.zeros((9, 2, 2), dtype=np.float32)
    # expected 对齐 Mshot2cmp.c 的 midpoint/offset 重排；
    # output_offset 是压缩后的 CMP gather offset axis2。
    for icmp in range(9):
        output_offset = 0
        for ioffset in range(icmp % 2, 4 + icmp % 2, 2):
            if ioffset < 4:
                ishot = (icmp - ioffset) // 2
                if 0 <= ishot < 3:
                    expected[icmp, output_offset] = data[ishot, ioffset]
            output_offset += 1
    assert result.returncode == 0, result.stderr
    np.testing.assert_array_equal(direct, expected)
    np.testing.assert_array_equal(read_rsf(output_path).data, expected)
    np.testing.assert_array_equal(read_rsf(cli_path).data, expected)
    np.testing.assert_array_equal(chained.numpy(), expected)
    np.testing.assert_array_equal(original.numpy(), data)
    header = read_rsf(output_path).header
    assert header.dimensions == (2, 2, 9)
    assert header["label3"] == "Midpoint"
    assert header["shot2cmp_source"] == "../src-master/system/seismic/Mshot2cmp.c"
    assert not hasattr(pymadagascar, "shot2cmp_rsf")
    with pytest.raises(GatherError, match="shape"):
        shot2cmp(data[0], dh=1.0, ds=2.0, oh=0.0, os=8.0)
    with pytest.raises(GatherError, match="ds/dh"):
        shot2cmp(data, dh=1.5, ds=2.0, oh=0.0, os=8.0)
    with pytest.raises(GatherError, match="half"):
        shot2cmp(data, dh=1.0, ds=2.0, oh=0.0, os=8.0, half=False)


def test_intbin_values_header_chain_cli_and_bounds(tmp_path: Path) -> None:
    # 数值 header table fixture: headers 的列是整数 x/y key，行数与 trace 数一致。
    # 这不是 SEG-Y trace header；它是 pymadagascar 的普通 RSF numeric table subset。
    traces = np.array(
        [
            [1.0, 1.5],
            [2.0, 2.5],
            [3.0, 3.5],
            [4.0, 4.5],
        ],
        dtype=np.float32,
    )
    headers = np.array([[0, 0], [1, 0], [0, 1], [3, 3]], dtype=np.int32)
    input_path = tmp_path / "traces.rsf"
    header_path = tmp_path / "headers.rsf"
    output_path = tmp_path / "intbin.rsf"
    cli_path = tmp_path / "intbin_cli.rsf"
    write_rsf(input_path, traces, _trace_header(nt=2, ntr=4))
    write_rsf(header_path, headers, _header_table_header(nkey=2, ntr=4))

    direct = intbin(traces, headers, xmin=0, xmax=1, ymin=0, ymax=1)
    original = RSFData(traces, _trace_header(nt=2, ntr=4))
    chained = original.intbin(headers, xmin=0, xmax=1, ymin=0, ymax=1)
    intbin_rsf(input_path, header_path, output_path, xmin=0, xmax=1, ymin=0, ymax=1)
    result = _run_cli(
        "intbin",
        [str(input_path), "head=" + str(header_path), "out=" + str(cli_path), "xmin=0", "xmax=1", "ymin=0", "ymax=1"],
        tmp_path,
    )

    expected = np.zeros((2, 2, 2), dtype=np.float32)
    # bounds 只保留 x/y in [0,1] 的 trace；越界 header [3,3] 被丢弃为零。
    expected[0, 0] = traces[0]
    expected[0, 1] = traces[1]
    expected[1, 0] = traces[2]
    assert result.returncode == 0, result.stderr
    np.testing.assert_array_equal(direct, expected)
    np.testing.assert_array_equal(read_rsf(output_path).data, expected)
    np.testing.assert_array_equal(read_rsf(cli_path).data, expected)
    np.testing.assert_array_equal(chained.numpy(), expected)
    np.testing.assert_array_equal(original.numpy(), traces)
    header = read_rsf(output_path).header
    assert header.dimensions == (2, 2, 2)
    assert header["intbin_source"] == "../src-master/system/seismic/Mintbin.c"
    assert not hasattr(pymadagascar, "intbin_rsf")
    with pytest.raises(GatherError, match="row count"):
        intbin(traces, headers[:2])
    with pytest.raises(GatherError, match="integer-valued"):
        intbin(traces, headers.astype(np.float32) + 0.25)


def test_intbin3_values_header_chain_cli_and_invalid_params(tmp_path: Path) -> None:
    # 3-D integer binning fixture 在 x/y/z key 上生成规则网格；
    # 输出 NumPy shape=(nz,ny,nx,ntime)，RSF header 对应 n1=time,n2=x,n3=y,n4=z。
    traces = np.array(
        [
            [1.0, 1.5],
            [2.0, 2.5],
            [3.0, 3.5],
        ],
        dtype=np.float32,
    )
    headers = np.array([[0, 0, 0], [1, 0, 1], [0, 1, 0]], dtype=np.int32)
    input_path = tmp_path / "traces3.rsf"
    header_path = tmp_path / "headers3.rsf"
    output_path = tmp_path / "intbin3.rsf"
    cli_path = tmp_path / "intbin3_cli.rsf"
    write_rsf(input_path, traces, _trace_header(nt=2, ntr=3))
    write_rsf(header_path, headers, _header_table_header(nkey=3, ntr=3))

    direct = intbin3(traces, headers)
    original = RSFData(traces, _trace_header(nt=2, ntr=3))
    chained = original.intbin3(headers)
    intbin3_rsf(input_path, header_path, output_path)
    result = _run_cli("intbin3", [str(input_path), "head=" + str(header_path), "out=" + str(cli_path)], tmp_path)

    expected = np.zeros((2, 2, 2, 2), dtype=np.float32)
    # expected 的索引顺序刻意按 NumPy (z,y,x,time) 写出，避免误读 RSF axis 顺序。
    expected[0, 0, 0] = traces[0]
    expected[1, 0, 1] = traces[1]
    expected[0, 1, 0] = traces[2]
    assert result.returncode == 0, result.stderr
    np.testing.assert_array_equal(direct, expected)
    np.testing.assert_array_equal(read_rsf(output_path).data, expected)
    np.testing.assert_array_equal(read_rsf(cli_path).data, expected)
    np.testing.assert_array_equal(chained.numpy(), expected)
    np.testing.assert_array_equal(original.numpy(), traces)
    header = read_rsf(output_path).header
    assert header.dimensions == (2, 2, 2, 2)
    assert header["intbin_source"] == "../src-master/system/seismic/Mintbin3.c"
    assert not hasattr(pymadagascar, "intbin3_rsf")
    with pytest.raises(GatherError, match="zkey"):
        intbin3(traces, headers, zkey=3)
    with pytest.raises(GatherError, match="xmax"):
        intbin3(traces, headers, xmin=2, xmax=1)


@pytest.mark.parametrize("module", ["cmp2shot", "shot2cmp", "intbin", "intbin3"])
def test_console_script_help_smoke(module: str) -> None:
    # CLI help smoke 不验证数值，只防止 module entry 和 Madagascar-style 参数说明漂移。
    result = subprocess.run(
        [sys.executable, "-m", f"pymadagascar.cli.{module}", "--help"],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=20,
    )
    assert result.returncode == 0
    assert "Madagascar-style parameters" in result.stdout
