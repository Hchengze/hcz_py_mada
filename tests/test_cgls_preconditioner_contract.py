from __future__ import annotations

import numpy as np
import pytest

from pymadagascar.generic.linear_operator import (
    DiagonalPreconditioner,
    FirstDifferenceRegularization,
    IdentityPreconditioner,
    LeastSquaresProblem,
    LinearOperatorError,
    MatrixOperator,
    Preconditioner,
    run_cgls,
    run_cgls_problem,
)
from pymadagascar.generic.preconditioners import (
    DiagonalPreconditioner as DirectDiagonalPreconditioner,
)
from pymadagascar.generic.solvers import run_cgls as direct_run_cgls


def _system() -> tuple[np.ndarray, np.ndarray]:
    matrix = np.array([[1.0, 0.0], [1.0, 1.0], [0.0, 1.0]])
    data = np.array([1.0, 2.0, 2.0])
    return matrix, data


def _first_difference_matrix(size: int) -> np.ndarray:
    matrix = np.zeros((size - 1, size))
    for index in range(size - 1):
        matrix[index, index] = -1.0
        matrix[index, index + 1] = 1.0
    return matrix


class _CustomIdentityPreconditioner(Preconditioner):
    def __init__(self, shape: tuple[int, ...] | int) -> None:
        super().__init__(shape, shape, dtype=np.float64, kind="custom_identity")

    def forward(self, model: np.ndarray) -> np.ndarray:
        return np.asarray(model, dtype=self.dtype).reshape(self.data_shape)

    def adjoint(self, data: np.ndarray) -> np.ndarray:
        return np.asarray(data, dtype=self.dtype).reshape(self.model_shape)


def test_cgls_preconditioner_none_preserves_default_behavior() -> None:
    matrix, data = _system()

    baseline = run_cgls(matrix, data, maxiter=10, tol=1e-12)
    explicit_none = run_cgls(matrix, data, maxiter=10, tol=1e-12, preconditioner=None)

    np.testing.assert_allclose(explicit_none.final_model, baseline.final_model)
    assert explicit_none.metadata == baseline.metadata
    assert "preconditioned" not in explicit_none.metadata


def test_identity_preconditioner_is_equivalent_to_unpreconditioned_cgls() -> None:
    matrix, data = _system()
    baseline = run_cgls(matrix, data, maxiter=10, tol=1e-12)

    result = run_cgls(
        MatrixOperator(matrix),
        data,
        maxiter=10,
        tol=1e-12,
        preconditioner=IdentityPreconditioner(2),
    )

    np.testing.assert_allclose(result.final_model, baseline.final_model)
    assert result.objective == pytest.approx(baseline.objective)
    assert result.metadata["preconditioned"] is True
    assert result.metadata["right_preconditioning"] is True
    assert result.metadata["preconditioner_kind"] == "identity"
    assert result.metadata["variable_space"] == "latent"
    assert result.metadata["solution_space"] == "model"


def test_diagonal_preconditioner_returns_model_space_solution_and_diagnostics() -> None:
    matrix = np.array(
        [[1.0, 2.0], [0.5, -1.0], [2.0, 0.25]],
        dtype=np.float64,
    )
    true_model = np.array([1.5, -0.5])
    data = matrix @ true_model
    weights = np.array([10.0, 0.1])
    preconditioner = DiagonalPreconditioner(weights)

    result = run_cgls(
        matrix,
        data,
        maxiter=10,
        tol=1e-12,
        preconditioner=preconditioner,
    )

    np.testing.assert_allclose(result.final_model, true_model, atol=1e-10)
    assert not np.allclose(result.final_model, true_model / weights)
    assert result.metadata["preconditioner_kind"] == "diagonal"
    assert result.metadata["preconditioner_domain_shape"] == (2,)
    problem = LeastSquaresProblem(matrix, data)
    assert result.objective == pytest.approx(problem.objective(result.final_model))
    assert result.residual_norm == pytest.approx(
        np.linalg.norm(matrix @ result.final_model - data)
    )
    assert result.history is not None
    assert result.history.records[-1].objective == pytest.approx(result.objective)


def test_cgls_problem_uses_preconditioned_augmented_regularized_system() -> None:
    matrix = np.array(
        [
            [1.0, 0.0, 0.5],
            [0.5, 1.0, 0.0],
            [0.0, 0.25, 1.0],
            [1.0, -0.5, 0.25],
        ],
        dtype=np.float64,
    )
    data = np.array([1.0, -0.5, 0.25, 2.0])
    reg_weight = 0.4
    weights = np.array([0.5, 2.0, 1.5])
    problem = LeastSquaresProblem(
        MatrixOperator(matrix),
        data,
        regularization=FirstDifferenceRegularization(3),
        reg_weight=reg_weight,
    )

    result = run_cgls_problem(
        problem,
        maxiter=20,
        tol=1e-12,
        preconditioner=DiagonalPreconditioner(weights),
    )

    diagonal = np.diag(weights)
    augmented_matrix = np.vstack(
        [matrix @ diagonal, reg_weight * _first_difference_matrix(3) @ diagonal]
    )
    augmented_data = np.concatenate([data, np.zeros(2)])
    expected_latent = np.linalg.lstsq(augmented_matrix, augmented_data, rcond=None)[0]
    expected_model = diagonal @ expected_latent

    np.testing.assert_allclose(result.final_model, expected_model, atol=1e-10)
    assert result.objective == pytest.approx(problem.objective(result.final_model))
    assert result.metadata["regularization_via"] == "StackedOperator[A @ M, lambda*L @ M]"
    assert result.metadata["regularization_residual_norm"] > 0.0


def test_complex_diagonal_preconditioner_preserves_hermitian_cgls_path() -> None:
    matrix = np.array(
        [[1.0 + 0.5j, 0.25], [0.5 - 0.25j, 1.0 + 1.0j], [0.0, 2.0 - 0.5j]],
        dtype=np.complex128,
    )
    true_model = np.array([0.5 - 0.25j, -1.0 + 0.75j])
    data = matrix @ true_model
    preconditioner = DiagonalPreconditioner(np.array([2.0 + 0.5j, -0.25 + 1.5j]))

    result = run_cgls(
        matrix,
        data,
        maxiter=10,
        tol=1e-12,
        preconditioner=preconditioner,
    )

    np.testing.assert_allclose(result.final_model, true_model, atol=1e-10)
    assert result.converged
    assert result.metadata["preconditioner_kind"] == "diagonal"
    assert result.history is not None
    assert result.history.records[-1].residual_norm <= result.history.records[0].residual_norm


def test_model_space_x0_is_mapped_to_latent_initial_state() -> None:
    matrix = np.array([[2.0, 0.0], [0.0, 3.0], [1.0, 1.0]])
    initial_model = np.array([2.0, -1.0])
    data = matrix @ initial_model

    diagonal = run_cgls(
        matrix,
        data,
        x0=initial_model,
        maxiter=5,
        tol=0.0,
        preconditioner=DiagonalPreconditioner(np.array([4.0, 0.5])),
    )
    identity = run_cgls(
        matrix,
        data,
        x0=initial_model,
        maxiter=5,
        tol=0.0,
        preconditioner=IdentityPreconditioner(2),
    )

    assert diagonal.converged
    assert diagonal.iterations == 0
    np.testing.assert_allclose(diagonal.final_model, initial_model)
    assert identity.converged
    assert identity.iterations == 0
    np.testing.assert_allclose(identity.final_model, initial_model)


def test_general_preconditioner_rejects_non_none_model_space_x0() -> None:
    with pytest.raises(LinearOperatorError, match="model-space initial model"):
        run_cgls(
            np.eye(2),
            np.ones(2),
            x0=np.zeros(2),
            preconditioner=_CustomIdentityPreconditioner(2),
        )


def test_preconditioner_error_inputs_remain_explicit() -> None:
    with pytest.raises(LinearOperatorError, match="range_shape"):
        run_cgls(np.eye(2), np.ones(2), preconditioner=IdentityPreconditioner(3))
    with pytest.raises(LinearOperatorError, match="not implicitly a preconditioner"):
        run_cgls(np.eye(2), np.ones(2), preconditioner=FirstDifferenceRegularization(2))
    with pytest.raises(LinearOperatorError, match="nonzero"):
        DiagonalPreconditioner(np.array([1.0, 0.0]))


def test_compat_and_direct_imports_accept_right_preconditioner() -> None:
    matrix, data = _system()

    compat_result = run_cgls(
        matrix,
        data,
        maxiter=10,
        tol=1e-12,
        preconditioner=DiagonalPreconditioner(np.array([0.5, 2.0])),
    )
    direct_result = direct_run_cgls(
        matrix,
        data,
        maxiter=10,
        tol=1e-12,
        preconditioner=DirectDiagonalPreconditioner(np.array([0.5, 2.0])),
    )

    np.testing.assert_allclose(direct_result.final_model, compat_result.final_model)
    assert direct_result.metadata["preconditioner_kind"] == "diagonal"
