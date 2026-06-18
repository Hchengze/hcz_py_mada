from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys

import numpy as np
import pytest

from pymadagascar.generic.linear_operator import (
    CallableLinearOperator,
    IdentityOperator,
    LinearOperatorError,
    MatrixOperator,
    complex_dot_test,
    conjgrad_solve,
    conjugate_gradient,
    conjugate_gradient_normal,
    dot_test,
)
from pymadagascar.io.rsf import read_rsf, write_rsf
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


def test_matrix_operator_forward_and_adjoint() -> None:
    operator = MatrixOperator(np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]))

    np.testing.assert_allclose(operator.forward(np.array([1.0, 1.0])), np.array([3.0, 7.0, 11.0]))
    np.testing.assert_allclose(operator.adjoint(np.ones(3)), np.array([9.0, 12.0]))
    assert operator.model_shape == (2,)
    assert operator.data_shape == (3,)


def test_real_dot_test_identity_and_matrix_pass() -> None:
    assert dot_test(IdentityOperator(5), seed=7).passed
    assert dot_test(MatrixOperator(np.array([[1.0, 2.0], [3.0, -1.0]])), seed=4).passed


def test_real_dot_test_bad_adjoint_fails() -> None:
    matrix = np.array([[1.0, 2.0], [3.0, -1.0]])
    operator = CallableLinearOperator(
        2,
        2,
        lambda model: matrix @ model.reshape(-1),
        lambda data: matrix.T @ data.reshape(-1) + np.array([1.0, 0.0]),
    )

    result = dot_test(operator, seed=2, rtol=1e-12, atol=1e-12)

    assert not result.passed
    assert result.abs_error > 0.0


def test_complex_dot_test_identity_matrix_and_bad_adjoint() -> None:
    matrix = np.array([[1.0 + 2.0j, 3.0 - 1.0j], [0.5j, -2.0 + 0.25j]], dtype=np.complex128)
    assert complex_dot_test(IdentityOperator(3, dtype=complex), seed=5).passed
    assert complex_dot_test(MatrixOperator(matrix), seed=5).passed

    bad_operator = CallableLinearOperator(
        2,
        2,
        lambda model: matrix @ model.reshape(-1),
        lambda data: matrix.T @ data.reshape(-1),
        dtype=np.complex128,
    )
    bad = complex_dot_test(bad_operator, seed=5, rtol=1e-12, atol=1e-12)

    assert not bad.passed


def test_conjugate_gradient_spd_small_system() -> None:
    matrix = np.array([[4.0, 1.0], [1.0, 3.0]])
    rhs = np.array([1.0, 2.0])

    result = conjugate_gradient(MatrixOperator(matrix), rhs, niter=10, tol=1e-12)

    assert result.converged
    np.testing.assert_allclose(result.solution, np.linalg.solve(matrix, rhs), rtol=1e-10, atol=1e-10)


def test_conjugate_gradient_normal_and_damp() -> None:
    matrix = np.array([[1.0, 0.0], [1.0, 1.0], [0.0, 1.0]])
    rhs = np.array([1.0, 2.0, 2.0])
    damp = 0.25

    result = conjugate_gradient_normal(MatrixOperator(matrix), rhs, niter=10, tol=1e-12)
    damped = conjugate_gradient_normal(MatrixOperator(matrix), rhs, niter=10, tol=1e-12, damp=damp)

    np.testing.assert_allclose(result.solution, np.linalg.lstsq(matrix, rhs, rcond=None)[0], rtol=1e-10, atol=1e-10)
    expected_damped = np.linalg.solve(matrix.T @ matrix + damp**2 * np.eye(2), matrix.T @ rhs)
    np.testing.assert_allclose(damped.solution, expected_damped, rtol=1e-10, atol=1e-10)


def test_complex_conjugate_gradient_hermitian_and_normal() -> None:
    hermitian = np.array([[4.0 + 0.0j, 1.0 - 0.5j], [1.0 + 0.5j, 3.0 + 0.0j]], dtype=np.complex128)
    hrhs = np.array([1.0 + 2.0j, 2.0 - 1.0j], dtype=np.complex128)
    hresult = conjugate_gradient(MatrixOperator(hermitian), hrhs, niter=10, tol=1e-12)

    matrix = np.array(
        [[1.0 + 1.0j, 0.0], [1.0, 1.0 - 0.5j], [0.0, 2.0 + 0.25j]],
        dtype=np.complex128,
    )
    rhs = np.array([1.0 + 0.5j, 2.0 - 0.25j, -1.0 + 0.75j], dtype=np.complex128)
    nresult = conjugate_gradient_normal(MatrixOperator(matrix), rhs, niter=10, tol=1e-12)

    np.testing.assert_allclose(hresult.solution, np.linalg.solve(hermitian, hrhs), rtol=1e-10, atol=1e-10)
    expected_normal = np.linalg.solve(matrix.conj().T @ matrix, matrix.conj().T @ rhs)
    np.testing.assert_allclose(nresult.solution, expected_normal, rtol=1e-10, atol=1e-10)


def test_shape_mismatch_and_invalid_mode_errors() -> None:
    with pytest.raises(LinearOperatorError, match="expected 2"):
        MatrixOperator(np.eye(2)).forward(np.ones(3))

    with pytest.raises(LinearOperatorError, match="mode"):
        conjgrad_solve(MatrixOperator(np.eye(2)), np.ones(2), mode="unsupported")

    with pytest.raises(LinearOperatorError, match="square"):
        conjugate_gradient(MatrixOperator(np.ones((3, 2))), np.ones(3))


def test_dottest_cli_subprocess_matrix_and_identity(tmp_path: Path) -> None:
    matrix_path = tmp_path / "matrix.rsf"
    write_rsf(matrix_path, np.array([[1.0, 2.0], [3.0, -1.0]], dtype=np.float32))

    matrix_result = _run_cli("dottest", [str(matrix_path), "nmodel=2", "ndata=2", "seed=3"], tmp_path)
    identity_result = _run_cli("dottest", ["op=identity", "n=4", "seed=3"], tmp_path)

    assert matrix_result.returncode == 0, matrix_result.stderr
    assert "pass=true" in matrix_result.stdout
    assert "abs_error=" in matrix_result.stdout
    assert identity_result.returncode == 0, identity_result.stderr
    assert "pass=true" in identity_result.stdout


def test_cdottest_cli_subprocess(tmp_path: Path) -> None:
    matrix_path = tmp_path / "cmatrix.rsf"
    matrix = np.array([[1.0 + 1.0j, 2.0 - 0.5j], [0.25j, -1.0 + 0.5j]], dtype=np.complex64)
    write_rsf(matrix_path, matrix)

    result = _run_cli("cdottest", [str(matrix_path), "nmodel=2", "ndata=2", "seed=3"], tmp_path)

    assert result.returncode == 0, result.stderr
    assert "pass=true" in result.stdout
    assert "lhs=" in result.stdout


def test_conjgrad_cli_subprocess(tmp_path: Path) -> None:
    matrix_path = tmp_path / "matrix.rsf"
    rhs_path = tmp_path / "rhs.rsf"
    out_path = tmp_path / "x.rsf"
    matrix = np.array([[4.0, 1.0], [1.0, 3.0]], dtype=np.float32)
    rhs = np.array([1.0, 2.0], dtype=np.float32)
    write_rsf(matrix_path, matrix)
    write_rsf(rhs_path, rhs)

    result = _run_cli(
        "conjgrad",
        [str(matrix_path), str(rhs_path), "out=" + str(out_path), "mode=spd", "niter=10", "tol=1e-12"],
        tmp_path,
    )

    assert result.returncode == 0, result.stderr
    np.testing.assert_allclose(read_rsf(out_path).data, np.linalg.solve(matrix, rhs), rtol=1e-6, atol=1e-6)


def test_cconjgrad_cli_subprocess(tmp_path: Path) -> None:
    matrix_path = tmp_path / "cmatrix.rsf"
    rhs_path = tmp_path / "crhs.rsf"
    out_path = tmp_path / "cx.rsf"
    matrix = np.array([[3.0 + 0.0j, 1.0 - 0.25j], [1.0 + 0.25j, 2.0 + 0.0j]], dtype=np.complex64)
    rhs = np.array([1.0 + 1.0j, 2.0 - 0.5j], dtype=np.complex64)
    write_rsf(matrix_path, matrix)
    write_rsf(rhs_path, rhs)

    result = _run_cli(
        "cconjgrad",
        [str(matrix_path), str(rhs_path), "out=" + str(out_path), "mode=hermitian", "niter=10", "tol=1e-12"],
        tmp_path,
    )

    assert result.returncode == 0, result.stderr
    np.testing.assert_allclose(read_rsf(out_path).data, np.linalg.solve(matrix, rhs), rtol=1e-5, atol=1e-5)


@pytest.mark.parametrize("program", ["sfdottest", "sfcdottest", "sfconjgrad", "sfcconjgrad"])
@pytest.mark.original_madagascar
def test_original_linear_operator_commands_are_optional_and_not_directly_comparable(program: str) -> None:
    if not original_madagascar_available(program):
        pytest.skip(f"Original Madagascar {program} is not installed")
    pytest.skip(
        f"Original {program} requires an external adj= operator command; "
        "the pymadagascar B-4 subset is matrix-backed and not directly comparable"
    )
