from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys

import numpy as np
import pytest

from pymadagascar.api import RSFData
from pymadagascar.generic import linefit as package_linefit
from pymadagascar.generic import match as package_match
from pymadagascar.generic import matmult as package_matmult
from pymadagascar.generic.array_algebra import (
    ArrayAlgebraError,
    linefit,
    linefit_rsf,
    match,
    match_rsf,
    matmult,
    matmult_rsf,
)
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf


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


def _vector_header(n1: int) -> RSFHeader:
    return RSFHeader({"n1": n1, "o1": 0.0, "d1": 1.0, "label1": "Vector"})


def _matrix_header(n1: int, n2: int) -> RSFHeader:
    return RSFHeader(
        {
            "n1": n1,
            "o1": 0.0,
            "d1": 1.0,
            "label1": "Column",
            "n2": n2,
            "o2": 10.0,
            "d2": 2.0,
            "label2": "Row",
        }
    )


def test_matmult_values_header_chain_cli_and_invalid_shape(tmp_path: Path) -> None:
    vector = np.array([1.0, 2.0, -1.0], dtype=np.float32)
    matrix = np.array([[1.0, 0.0, 2.0], [0.5, -1.0, 1.0]], dtype=np.float32)
    input_path = tmp_path / "x.rsf"
    mat_path = tmp_path / "a.rsf"
    output_path = tmp_path / "y.rsf"
    cli_path = tmp_path / "cli.rsf"
    write_rsf(input_path, vector, _vector_header(3))
    write_rsf(mat_path, matrix, _matrix_header(3, 2))

    direct = matmult(vector, matrix)
    matmult_rsf(input_path, mat_path, output_path)
    result = _run_cli("matmult", [str(input_path), str(mat_path), "out=" + str(cli_path)], tmp_path)
    chained = RSFData(vector, _vector_header(3)).matmult(
        RSFData(matrix, _matrix_header(3, 2))
    )

    assert package_matmult is matmult
    assert result.returncode == 0, result.stderr
    np.testing.assert_allclose(direct, matrix @ vector)
    np.testing.assert_allclose(read_rsf(output_path).data, direct)
    np.testing.assert_allclose(read_rsf(cli_path).data, direct)
    np.testing.assert_allclose(chained.numpy(), direct)
    assert read_rsf(output_path).header.dimensions == (2,)
    assert read_rsf(output_path).header["label1"] == "Row"
    assert read_rsf(output_path).header["matmult_adj"] == "n"
    with pytest.raises(ArrayAlgebraError, match="shape mismatch"):
        matmult(vector[:2], matrix)


def test_match_forward_adjoint_chain_cli_and_no_mutation(tmp_path: Path) -> None:
    filt = np.array([0.25, 1.0, -0.5], dtype=np.float32)
    noise = np.array([[1.0, 2.0, 0.0, -1.0], [0.0, 1.0, 1.0, 0.0]], dtype=np.float32)
    filter_path = tmp_path / "filter.rsf"
    noise_path = tmp_path / "noise.rsf"
    output_path = tmp_path / "matched.rsf"
    cli_path = tmp_path / "matched_cli.rsf"
    write_rsf(filter_path, filt, _vector_header(filt.size))
    write_rsf(noise_path, noise, _matrix_header(4, 2))

    direct = match(filt, noise)
    match_rsf(filter_path, noise_path, output_path)
    result = _run_cli("match", [str(filter_path), str(noise_path), "out=" + str(cli_path)], tmp_path)
    rsf = RSFData(filt, _vector_header(filt.size))
    chained = rsf.match(RSFData(noise, _matrix_header(4, 2)))
    adjoint = match(direct, noise, adj=True, nf=filt.size)

    assert package_match is match
    assert result.returncode == 0, result.stderr
    np.testing.assert_allclose(read_rsf(output_path).data, direct)
    np.testing.assert_allclose(read_rsf(cli_path).data, direct)
    np.testing.assert_allclose(chained.numpy(), direct)
    np.testing.assert_array_equal(rsf.numpy(), filt)
    assert adjoint.shape == filt.shape
    assert read_rsf(output_path).header["match_adj"] == "n"
    assert read_rsf(output_path).header["match_nf"] == str(filt.size)
    with pytest.raises(ArrayAlgebraError, match="nf"):
        match(direct, noise, adj=True)


def test_linefit_values_header_chain_cli_and_zero_determinant(tmp_path: Path) -> None:
    x = np.array([0.0, 1.0, 2.0, 3.0], dtype=np.float32)
    y = 2.0 * x + 1.0
    table = np.column_stack([x, y]).astype(np.float32)
    input_path = tmp_path / "table.rsf"
    output_path = tmp_path / "line.rsf"
    cli_path = tmp_path / "line_cli.rsf"
    write_rsf(input_path, table, _matrix_header(2, 4))

    direct = linefit(table, n=5, o=0.0, d=0.5)
    linefit_rsf(input_path, output_path, n=5, o=0.0, d=0.5)
    result = _run_cli("linefit", [str(input_path), "out=" + str(cli_path), "n=5", "o=0", "d=0.5"], tmp_path)
    chained = RSFData(table, _matrix_header(2, 4)).linefit(n=5, o=0.0, d=0.5)

    assert package_linefit is linefit
    assert result.returncode == 0, result.stderr
    np.testing.assert_allclose(direct, np.array([1, 2, 3, 4, 5], dtype=np.float32))
    np.testing.assert_allclose(read_rsf(output_path).data, direct)
    np.testing.assert_allclose(read_rsf(cli_path).data, direct)
    np.testing.assert_allclose(chained.numpy(), direct)
    assert read_rsf(output_path).header.dimensions == (5,)
    assert read_rsf(output_path).header["d1"] == "0.5"
    assert read_rsf(output_path).header["linefit_model"] == "y=a*x+b"
    with pytest.raises(ArrayAlgebraError, match="zero determinant"):
        linefit(np.array([[1.0, 1.0], [1.0, 2.0]], dtype=np.float32), n=3, o=0.0, d=1.0)


@pytest.mark.parametrize("module", ["matmult", "match", "linefit"])
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
