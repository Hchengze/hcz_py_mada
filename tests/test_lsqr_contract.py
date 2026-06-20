from __future__ import annotations

import json
import pkgutil

import numpy as np
import pytest

import pymadagascar
import pymadagascar.api as public_api
import pymadagascar.cli as cli_package
import pymadagascar.generic.linear_operator as linear_operator
from pymadagascar.generic.linear_operator import (
    FirstDifferenceRegularization,
    IdentityPreconditioner,
    LeastSquaresProblem,
    LinearOperatorError,
    MatrixOperator,
    SolverResult,
    run_lsqr,
    run_lsqr_problem,
)
from pymadagascar.generic.solvers import run_lsqr as direct_run_lsqr


def _real_system() -> tuple[np.ndarray, np.ndarray]:
    matrix = np.array(
        [
            [1.0, 0.0],
            [1.0, 1.0],
            [0.0, 1.0],
            [2.0, -1.0],
        ]
    )
    data = np.array([1.0, 2.0, 2.0, 0.5])
    return matrix, data


def test_lsqr_solves_small_overdetermined_system_and_matches_numpy() -> None:
    matrix, data = _real_system()
    result = run_lsqr(MatrixOperator(matrix), data, maxiter=10, tol=1e-12)

    assert isinstance(result, SolverResult)
    np.testing.assert_allclose(result.final_model, np.linalg.lstsq(matrix, data, rcond=None)[0])
    assert result.objective == pytest.approx(0.5 * np.linalg.norm(data - matrix @ result.final_model) ** 2)
    assert result.metadata["solver"] == "lsqr"
    assert result.metadata["algorithm"] == "golub_kahan_bidiagonalization"
    assert result.metadata["method_family"] == "golub_kahan_bidiagonalization"
    assert result.metadata["data_residual_convention"] == "b_minus_Ax"
    assert result.metadata["objective_kind"] == "least_squares"
    assert result.metadata["preconditioned"] is False
    assert result.metadata["right_preconditioning"] is False
    assert result.metadata["variable_space"] == "model"
    assert result.metadata["solution_space"] == "model"


def test_lsqr_problem_matches_direct_helper() -> None:
    matrix, data = _real_system()
    direct = run_lsqr(matrix, data, maxiter=10, tol=1e-12)
    problem = LeastSquaresProblem(matrix, data, metadata={"case": "problem"})
    via_problem = run_lsqr_problem(problem, maxiter=10, tol=1e-12)

    np.testing.assert_allclose(via_problem.final_model, direct.final_model)
    assert via_problem.metadata["case"] == "problem"


def test_lsqr_supports_regularized_problem_via_augmented_reference() -> None:
    matrix = np.array([[1.0, 0.0, 0.5], [0.0, 2.0, -1.0], [1.0, 1.0, 0.0]])
    data = np.array([1.0, -0.5, 2.0])
    regularization = FirstDifferenceRegularization(3)
    weight = 0.25
    problem = LeastSquaresProblem(
        matrix,
        data,
        regularization=regularization,
        reg_weight=weight,
    )
    result = run_lsqr_problem(problem, maxiter=20, tol=1e-12)

    reg_matrix = np.array([[-1.0, 1.0, 0.0], [0.0, -1.0, 1.0]])
    augmented_matrix = np.vstack([matrix, weight * reg_matrix])
    augmented_data = np.concatenate([data, np.zeros(2)])
    reference = np.linalg.lstsq(augmented_matrix, augmented_data, rcond=None)[0]
    np.testing.assert_allclose(result.final_model, reference)
    assert result.metadata["regularized"] is True
    assert result.metadata["residual_space"] == "augmented_least_squares"
    assert result.metadata["regularization_via"] == "StackedOperator[A, lambda*L]"


def test_lsqr_supports_nonzero_model_space_x0_with_shifted_residual() -> None:
    matrix, data = _real_system()
    x0 = np.array([10.0, -7.0])
    result = run_lsqr(matrix, data, x0=x0, maxiter=10, tol=1e-12)

    np.testing.assert_allclose(result.final_model, np.linalg.lstsq(matrix, data, rcond=None)[0])
    assert result.objective == pytest.approx(0.5 * np.linalg.norm(data - matrix @ result.final_model) ** 2)


def test_lsqr_supports_complex_small_system() -> None:
    matrix = np.array(
        [
            [1.0 + 1.0j, 0.0],
            [0.5, 2.0 - 0.25j],
            [1.0j, -1.0],
        ]
    )
    data = np.array([1.0 - 0.5j, 2.0 + 1.0j, -0.25j])
    result = run_lsqr(matrix, data, maxiter=10, tol=1e-12)

    np.testing.assert_allclose(result.final_model, np.linalg.lstsq(matrix, data, rcond=None)[0])
    assert result.metadata["normal_residual_space"] == "model"


def test_lsqr_history_and_summary_are_json_safe() -> None:
    matrix, data = _real_system()
    result = run_lsqr(matrix, data, maxiter=10, tol=1e-12, metadata={"stage": "I0-9B1"})

    assert result.history is not None
    assert result.history.records[0].iteration == 0
    assert result.history.records[-1].iteration == result.iterations
    assert result.history.metadata["stage"] == "I0-9B1"
    assert result.history.records[-1].metadata["convergence_residual_space"] == "data"
    summary = result.to_summary()
    json.dumps(summary)
    assert summary["metadata"]["stage"] == "I0-9B1"


def test_lsqr_without_history_keeps_result_diagnostics() -> None:
    matrix, data = _real_system()
    result = run_lsqr(matrix, data, track_history=False)

    assert result.history is None
    assert result.metadata["track_history"] is False
    assert result.metadata["convergence_residual_norm"] is not None
    assert result.metadata["model_gradient_norm"] is not None


@pytest.mark.parametrize(
    ("call", "message"),
    [
        (lambda: run_lsqr(np.eye(2), np.ones(3)), "expected 2"),
        (lambda: run_lsqr(np.eye(2), np.array([1.0, np.nan])), "finite"),
        (lambda: run_lsqr(np.eye(2), np.ones(2), x0=np.ones(3)), "expected 2"),
        (lambda: run_lsqr(np.eye(2), np.ones(2), maxiter=0), "positive integer"),
        (lambda: run_lsqr(np.eye(2), np.ones(2), tol=np.inf), "finite"),
        (lambda: run_lsqr_problem(object()), "LeastSquaresProblem"),
    ],
)
def test_lsqr_rejects_invalid_contract_inputs(call: object, message: str) -> None:
    with pytest.raises(LinearOperatorError, match=message):
        call()


def test_lsqr_zero_rhs_stops_cleanly() -> None:
    result = run_lsqr(np.eye(2), np.zeros(2), maxiter=3, tol=0.0)

    np.testing.assert_array_equal(result.final_model, np.zeros(2))
    assert result.converged
    assert result.stopping_reason == "zero_rhs"
    assert result.iterations == 0


def test_lsqr_zero_operator_reports_breakdown_without_crashing() -> None:
    result = run_lsqr(np.zeros((3, 2)), np.ones(3), maxiter=3, tol=1e-12)

    np.testing.assert_array_equal(result.final_model, np.zeros(2))
    assert not result.converged
    assert result.stopping_reason == "breakdown_alpha"
    assert "invalid_state" in result.metadata


def test_lsqr_rejects_preconditioner_boundary_for_i0_9b1() -> None:
    with pytest.raises(LinearOperatorError, match="preconditioned LSQR is not implemented"):
        run_lsqr(np.eye(2), np.ones(2), preconditioner=IdentityPreconditioner(2))


def test_lsqr_direct_module_reexport_and_api_boundaries() -> None:
    assert direct_run_lsqr is run_lsqr
    assert hasattr(linear_operator, "run_lsqr")
    assert hasattr(linear_operator, "run_lsqr_problem")
    assert not hasattr(pymadagascar, "run_lsqr")
    assert not hasattr(public_api, "run_lsqr")
    module_names = {module.name for module in pkgutil.iter_modules(cli_package.__path__)}
    assert "lsqr" not in module_names
