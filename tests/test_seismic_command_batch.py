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
from pymadagascar.seismic.ai2refl import AI2ReflError, ai2refl, ai2refl_rsf
from pymadagascar.seismic.avo import AVOError, avo_intercept_gradient, avo_rsf
from pymadagascar.seismic.fold import FoldError, fold_rsf, fold_table


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
            "d2": 1.0,
            "label2": "Half-offset",
            "unit2": "m",
        }
    )


def _table_header(nrow: int, ncol: int) -> RSFHeader:
    return RSFHeader(
        {
            "n1": ncol,
            "o1": 0.0,
            "d1": 1.0,
            "label1": "Header key",
            "n2": nrow,
            "o2": 0.0,
            "d2": 1.0,
            "label2": "Trace",
        }
    )


def test_avo_values_header_chain_cli_and_invalid_offsets(tmp_path: Path) -> None:
    offsets = np.array([0.0, 1.0, 2.0], dtype=np.float32)
    intercept = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float32)
    gradient = np.array([0.25, -0.5, 1.5, 0.0], dtype=np.float32)
    gather = intercept[np.newaxis, :] + offsets[:, np.newaxis] * gradient[np.newaxis, :]
    input_path = tmp_path / "gather.rsf"
    output_path = tmp_path / "avo.rsf"
    cli_path = tmp_path / "avo_cli.rsf"
    write_rsf(input_path, gather, _gather_header(nt=4, nh=3))

    direct = avo_intercept_gradient(gather, o2=0.0, d2=1.0, half=False)
    original = RSFData(gather, _gather_header(nt=4, nh=3))
    chained = original.avo(half=False)
    avo_rsf(input_path, output_path, half=False)
    result = _run_cli("avo", [str(input_path), "out=" + str(cli_path), "half=n"], tmp_path)

    assert result.returncode == 0, result.stderr
    np.testing.assert_allclose(direct[0], intercept, atol=1e-6)
    np.testing.assert_allclose(direct[1], gradient, atol=1e-6)
    np.testing.assert_allclose(read_rsf(output_path).data, direct, atol=1e-6)
    np.testing.assert_allclose(read_rsf(cli_path).data, direct, atol=1e-6)
    np.testing.assert_allclose(chained.numpy(), direct, atol=1e-6)
    np.testing.assert_array_equal(original.numpy(), gather)
    header = read_rsf(output_path).header
    assert header.dimensions == (4, 2)
    assert header["label2"] == "AVO"
    assert header["avo_components"] == "intercept,gradient"
    assert not hasattr(pymadagascar, "avo_rsf")
    with pytest.raises(AVOError, match="at least two offsets"):
        avo_intercept_gradient(gather[:1])
    with pytest.raises(AVOError, match="offset length"):
        avo_intercept_gradient(gather, offsets=np.array([0.0, 1.0], dtype=np.float32))


def test_fold_values_header_chain_cli_and_invalid_columns(tmp_path: Path) -> None:
    table = np.array(
        [
            [0.0, 10.0, 100.0],
            [0.0, 10.0, 100.0],
            [100.0, 10.0, 100.0],
            [100.0, 11.0, 100.0],
            [999.0, 10.0, 100.0],
        ],
        dtype=np.float32,
    )
    input_path = tmp_path / "headers.rsf"
    output_path = tmp_path / "fold.rsf"
    cli_path = tmp_path / "fold_cli.rsf"
    write_rsf(input_path, table, _table_header(nrow=5, ncol=3))

    direct = fold_table(table, n=(2, 2, 1), o=(0.0, 10.0, 100.0), d=(100.0, 1.0, 1.0))
    original = RSFData(table, _table_header(nrow=5, ncol=3))
    chained = original.fold(n=(2, 2, 1), o=(0.0, 10.0, 100.0), d=(100.0, 1.0, 1.0))
    fold_rsf(input_path, output_path, n=(2, 2, 1), o=(0.0, 10.0, 100.0), d=(100.0, 1.0, 1.0))
    result = _run_cli(
        "fold",
        [
            str(input_path),
            "out=" + str(cli_path),
            "n1=2",
            "n2=2",
            "n3=1",
            "o1=0",
            "o2=10",
            "o3=100",
            "d1=100",
            "d2=1",
            "d3=1",
        ],
        tmp_path,
    )

    expected = np.array([[[2.0, 1.0], [0.0, 1.0]]], dtype=np.float32)
    assert result.returncode == 0, result.stderr
    np.testing.assert_allclose(direct, expected)
    np.testing.assert_allclose(read_rsf(output_path).data, expected)
    np.testing.assert_allclose(read_rsf(cli_path).data, expected)
    np.testing.assert_allclose(chained.numpy(), expected)
    np.testing.assert_array_equal(original.numpy(), table)
    header = read_rsf(output_path).header
    assert header.dimensions == (2, 2, 1)
    assert header["fold_subset"] == "numeric-header-table"
    assert not hasattr(pymadagascar, "fold_rsf")
    with pytest.raises(FoldError, match="columns"):
        fold_table(table, columns=(0, 1, 3), n=(2, 2, 1), o=(0.0, 10.0, 100.0), d=(100.0, 1.0, 1.0))
    with pytest.raises(FoldError, match="nonzero"):
        fold_table(table, n=(2, 2, 1), o=(0.0, 10.0, 100.0), d=(0.0, 1.0, 1.0))


def test_ai2refl_values_header_chain_cli_and_invalid_axis(tmp_path: Path) -> None:
    impedance = np.array([[2.0, 4.0, 8.0, 8.0], [1.0, 3.0, 6.0, 12.0]], dtype=np.float32)
    input_path = tmp_path / "ai.rsf"
    output_path = tmp_path / "refl.rsf"
    cli_path = tmp_path / "refl_cli.rsf"
    write_rsf(input_path, impedance, _gather_header(nt=4, nh=2))

    direct = ai2refl(impedance, axis=1, eps=0.0)
    original = RSFData(impedance, _gather_header(nt=4, nh=2))
    chained = original.ai2refl(axis=1, eps=0.0)
    ai2refl_rsf(input_path, output_path, axis=1, eps=0.0)
    result = _run_cli("ai2refl", [str(input_path), "out=" + str(cli_path), "axis=1", "eps=0"], tmp_path)

    expected = np.array([[1 / 3, 1 / 3, 0.0, 0.0], [0.5, 1 / 3, 1 / 3, 0.0]], dtype=np.float32)
    assert result.returncode == 0, result.stderr
    np.testing.assert_allclose(direct, expected, atol=1e-6)
    np.testing.assert_allclose(read_rsf(output_path).data, expected, atol=1e-6)
    np.testing.assert_allclose(read_rsf(cli_path).data, expected, atol=1e-6)
    np.testing.assert_allclose(chained.numpy(), expected, atol=1e-6)
    np.testing.assert_array_equal(original.numpy(), impedance)
    assert read_rsf(output_path).header.dimensions == (4, 2)
    assert read_rsf(output_path).header["ai2refl_axis"] == "1"
    assert not hasattr(pymadagascar, "ai2refl_rsf")
    with pytest.raises((AI2ReflError, ValueError), match="axis"):
        ai2refl(impedance, axis=3)
    with pytest.raises(AI2ReflError, match="non-negative"):
        ai2refl(impedance, eps=-1.0)


@pytest.mark.parametrize("module", ["avo", "fold", "ai2refl"])
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
