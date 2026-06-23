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
from pymadagascar.seismic.halfint import HalfIntError, halfint, halfint_rsf
from pymadagascar.seismic.moveout import MoveoutError, moveout_rsf, moveout_spikes
from pymadagascar.seismic.nmo import NMOError, nmo_correct


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


def _gather_header(nt: int, nh: int) -> RSFHeader:
    return RSFHeader(
        {
            "n1": nt,
            "o1": 0.0,
            "d1": 0.004,
            "label1": "Time",
            "unit1": "s",
            "n2": nh,
            "o2": 0.0,
            "d2": 100.0,
            "label2": "Half-offset",
            "unit2": "m",
        }
    )


def _trace_header(n1: int) -> RSFHeader:
    return RSFHeader({"n1": n1, "o1": 0.0, "d1": 0.004, "label1": "Time", "unit1": "s"})


def test_nmo_source_aligned_chain_cli_and_invalid_inputs(tmp_path: Path) -> None:
    time = np.arange(8, dtype=np.float32) * 0.004
    gather = np.vstack([time, time]).astype(np.float32)
    input_path = tmp_path / "gather.rsf"
    output_path = tmp_path / "nmo.rsf"
    cli_path = tmp_path / "nmo_cli.rsf"
    write_rsf(input_path, gather, _gather_header(nt=8, nh=2))

    nmo_correct(input_path, 2000.0, output_path, stretch=None)
    original = RSFData(gather, _gather_header(nt=8, nh=2))
    chained = original.nmo(2000.0, stretch=None)
    result = _run_cli("nmo", [str(input_path), "out=" + str(cli_path), "velocity=2000", "stretch=0"], tmp_path)

    assert result.returncode == 0, result.stderr
    zero_offset = read_rsf(output_path).data[0]
    np.testing.assert_allclose(zero_offset, gather[0], atol=1e-6)
    np.testing.assert_allclose(read_rsf(cli_path).data, read_rsf(output_path).data, atol=1e-6)
    np.testing.assert_allclose(chained.numpy(), read_rsf(output_path).data, atol=1e-6)
    np.testing.assert_array_equal(original.numpy(), gather)
    header = read_rsf(output_path).header
    assert header["nmo_source"] == "../src-master/system/seismic/Mnmo.c"
    assert header["nmo_subset"] == "bounded-hyperbolic-nmo"
    assert callable(getattr(pymadagascar, "nmo_correct", None))
    with pytest.raises(NMOError, match="positive"):
        original.nmo(-1.0)
    with pytest.raises(NMOError, match="expected"):
        original.nmo(np.ones(3, dtype=np.float32))


def test_halfint_values_header_chain_cli_and_invalid_axis(tmp_path: Path) -> None:
    n = 64
    phase = np.linspace(0.0, 4.0 * np.pi, n, endpoint=False, dtype=np.float64)
    trace = np.sin(phase).astype(np.float32)
    input_path = tmp_path / "trace.rsf"
    output_path = tmp_path / "halfint.rsf"
    cli_path = tmp_path / "halfint_cli.rsf"
    write_rsf(input_path, trace, _trace_header(n))

    direct = halfint(trace, axis=1)
    diffed = halfint(direct, axis=1, inv=True)
    original = RSFData(trace, _trace_header(n))
    chained = original.halfint(axis=1)
    halfint_rsf(input_path, output_path, axis=1)
    result = _run_cli("halfint", [str(input_path), "out=" + str(cli_path), "axis=1"], tmp_path)

    assert result.returncode == 0, result.stderr
    assert np.all(np.isfinite(direct))
    assert np.max(np.abs(direct)) > 0.0
    np.testing.assert_allclose(diffed[1:-1], trace[1:-1], atol=0.55)
    np.testing.assert_allclose(read_rsf(output_path).data, direct, atol=1e-6)
    np.testing.assert_allclose(read_rsf(cli_path).data, direct, atol=1e-6)
    np.testing.assert_allclose(chained.numpy(), direct, atol=1e-6)
    np.testing.assert_array_equal(original.numpy(), trace)
    header = read_rsf(output_path).header
    assert header.dimensions == (n,)
    assert header["halfint_source"] == "../src-master/system/seismic/Mhalfint.c"
    assert not hasattr(pymadagascar, "halfint_rsf")
    with pytest.raises((HalfIntError, ValueError), match="axis"):
        halfint(trace, axis=2)
    with pytest.raises(HalfIntError, match="rho"):
        halfint(trace, rho=0.0)


def test_moveout_values_header_chain_cli_and_invalid_params(tmp_path: Path) -> None:
    times = np.array([0.0, 0.5, 2.25, 4.0], dtype=np.float32)
    input_path = tmp_path / "times.rsf"
    output_path = tmp_path / "moveout.rsf"
    cli_path = tmp_path / "moveout_cli.rsf"
    header = RSFHeader({"n1": 4, "o1": 10.0, "d1": 1.0, "label1": "CMP", "unit1": "index"})
    write_rsf(input_path, times, header)

    direct = moveout_spikes(times, n1=5, o1=0.0, d1=1.0)
    original = RSFData(times, header)
    chained = original.moveout(n1=5, o1=0.0, d1=1.0)
    moveout_rsf(input_path, output_path, n1=5, o1=0.0, d1=1.0)
    result = _run_cli(
        "moveout",
        [str(input_path), "out=" + str(cli_path), "n1=5", "o1=0", "d1=1"],
        tmp_path,
    )

    expected = np.array(
        [
            [1.0, 0.0, 0.0, 0.0, 0.0],
            [0.5, 0.5, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.75, 0.25, 0.0],
            [0.0, 0.0, 0.0, 0.0, 1.0],
        ],
        dtype=np.float32,
    )
    assert result.returncode == 0, result.stderr
    np.testing.assert_allclose(direct, expected, atol=1e-6)
    np.testing.assert_allclose(read_rsf(output_path).data, expected, atol=1e-6)
    np.testing.assert_allclose(read_rsf(cli_path).data, expected, atol=1e-6)
    np.testing.assert_allclose(chained.numpy(), expected, atol=1e-6)
    np.testing.assert_array_equal(original.numpy(), times)
    out_header = read_rsf(output_path).header
    assert out_header.dimensions == (5, 4)
    assert out_header["label1"] == "Time"
    assert out_header["label2"] == "CMP"
    assert out_header["moveout_source"] == "../src-master/system/seismic/Mmoveout.c"
    assert not hasattr(pymadagascar, "moveout_rsf")
    with pytest.raises(MoveoutError, match="n1"):
        moveout_spikes(times, n1=0)
    with pytest.raises(MoveoutError, match="interpolation"):
        moveout_spikes(times, n1=5, interpolation="cubic")


@pytest.mark.parametrize("module", ["nmo", "halfint", "moveout"])
def test_console_script_help_smoke(module: str) -> None:
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
