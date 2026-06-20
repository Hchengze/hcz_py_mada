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
    LeastSquaresProblem,
    LinearOperatorError,
    MatrixOperator,
    SolverResult,
    run_cgls,
    run_cgls_problem,
)


def _real_system() -> tuple[np.ndarray, np.ndarray]:
    matrix = np.array([[1.0, 0.0], [1.0, 1.0], [0.0, 1.0]])
    data = np.array([1.0, 2.0, 2.0])
    return matrix, data


def test_cgls_solves_small_overdetermined_system_and_matches_numpy() -> None:
    matrix, data = _real_system()
    result = run_cgls(MatrixOperator(matrix), data, maxiter=10, tol=1e-12)

    assert isinstance(result, SolverResult)
    assert result.converged
    np.testing.assert_allclose(result.final_model, np.linalg.lstsq(matrix, data, rcond=None)[0])


def test_cgls_objective_is_nonincreasing_and_history_is_recorded() -> None:
    matrix, data = _real_system()
    result = run_cgls(matrix, data, maxiter=10, tol=1e-12)

    assert result.history is not None
    objectives = [record.objective for record in result.history.records]
    assert all(value is not None for value in objectives)
    assert all(right <= left + 1e-14 for left, right in zip(objectives, objectives[1:]))
    assert result.history.records[0].iteration == 0
    assert result.history.records[-1].iteration == result.iterations
    assert result.history.metadata["convergence_residual_space"] == "normal_equation"


def test_cgls_supports_zero_and_nonzero_initial_models() -> None:
    matrix, data = _real_system()
    expected = np.linalg.lstsq(matrix, data, rcond=None)[0]

    zero = run_cgls(matrix, data, x0=np.zeros(2), maxiter=10, tol=1e-12)
    nonzero = run_cgls(matrix, data, x0=np.array([0.5, -0.25]), maxiter=10, tol=1e-12)

    np.testing.assert_allclose(zero.final_model, expected)
    np.testing.assert_allclose(nonzero.final_model, expected)


def test_cgls_consumes_least_squares_problem() -> None:
    matrix, data = _real_system()
    problem = LeastSquaresProblem(matrix, data, metadata={"case": "problem"})
    result = run_cgls_problem(problem, maxiter=10, tol=1e-12)

    np.testing.assert_allclose(result.final_model, np.linalg.lstsq(matrix, data, rcond=None)[0])
    assert result.objective == pytest.approx(problem.objective(result.final_model))
    assert result.metadata["case"] == "problem"


def test_cgls_supports_first_difference_regularization_via_problem() -> None:
    matrix = np.eye(3)
    data = np.array([0.0, 2.0, 0.0])
    weight = 0.5
    regularization = FirstDifferenceRegularization(3)
    problem = LeastSquaresProblem(
        matrix,
        data,
        regularization=regularization,
        reg_weight=weight,
    )
    result = run_cgls_problem(problem, maxiter=10, tol=1e-12)

    difference = np.array([[-1.0, 1.0, 0.0], [0.0, -1.0, 1.0]])
    augmented_matrix = np.vstack([matrix, weight * difference])
    augmented_data = np.concatenate([data, np.zeros(2)])
    expected = np.linalg.lstsq(augmented_matrix, augmented_data, rcond=None)[0]
    np.testing.assert_allclose(result.final_model, expected)
    assert result.metadata["regularization_via"] == "StackedOperator[A, lambda*L]"
    assert result.metadata["regularization_residual_norm"] > 0.0


def test_cgls_summary_is_json_safe() -> None:
    matrix, data = _real_system()
    summary = run_cgls(matrix, data, metadata={"stage": "I0-5"}).to_summary()

    assert summary["metadata"]["stage"] == "I0-5"
    assert json.loads(json.dumps(summary, sort_keys=True)) == summary


def test_cgls_stopping_reason_gradient_tolerance_at_initial_model() -> None:
    result = run_cgls(np.eye(2), np.zeros(2), maxiter=3, tol=0.0)

    assert result.converged
    assert result.iterations == 0
    assert result.stopping_reason == "gradient_tolerance"


def test_cgls_stopping_reason_max_iterations() -> None:
    matrix = np.diag([1.0, 2.0, 4.0])
    result = run_cgls(matrix, np.ones(3), maxiter=1, tol=0.0)

    assert not result.converged
    assert result.iterations == 1
    assert result.stopping_reason == "max_iterations"


def test_cgls_without_history_keeps_result_diagnostics() -> None:
    matrix, data = _real_system()
    result = run_cgls(matrix, data, track_history=False)

    assert result.history is None
    assert result.objective is not None
    assert result.metadata["normal_residual_norm"] is not None


@pytest.mark.parametrize(
    ("call", "message"),
    [
        (lambda: run_cgls(np.eye(2), np.ones(3)), "expected 2"),
        (lambda: run_cgls(np.eye(2), np.array([1.0, np.nan])), "finite"),
        (lambda: run_cgls(np.eye(2), np.ones(2), x0=np.ones(3)), "expected 2"),
        (lambda: run_cgls(np.eye(2), np.ones(2), maxiter=0), "positive integer"),
        (lambda: run_cgls(np.eye(2), np.ones(2), tol=np.inf), "finite"),
        (lambda: run_cgls_problem(object()), "LeastSquaresProblem"),
    ],
)
def test_cgls_rejects_invalid_contract_inputs(call: object, message: str) -> None:
    with pytest.raises(LinearOperatorError, match=message):
        call()  # type: ignore[operator]


def test_cgls_supports_complex_hermitian_adjoint() -> None:
    matrix = np.array(
        [[1.0 + 1.0j, 0.0], [1.0, 1.0 - 0.5j], [0.0, 2.0 + 0.25j]],
        dtype=np.complex128,
    )
    data = np.array([1.0 + 0.5j, 2.0 - 0.25j, -1.0 + 0.75j])
    result = run_cgls(matrix, data, maxiter=10, tol=1e-12)

    np.testing.assert_allclose(result.final_model, np.linalg.lstsq(matrix, data, rcond=None)[0])
    assert result.converged


def test_cgls_adds_no_cli_or_stable_export() -> None:
    for name in ["run_cgls", "run_cgls_problem"]:
        assert hasattr(linear_operator, name)
        assert not hasattr(pymadagascar, name)
        assert not hasattr(public_api, name)
    module_names = {module.name for module in pkgutil.iter_modules(cli_package.__path__)}
    assert "cgls" not in module_names


def test_lsqr_symbol_and_separate_stable_preconditioned_solver_remain_unimplemented() -> None:
    assert hasattr(linear_operator, "run_lsqr")
    assert hasattr(linear_operator, "run_lsqr_problem")
    for name in ["lsqr", "run_preconditioned_cgls"]:
        assert not hasattr(linear_operator, name)
