from __future__ import annotations

import importlib
import json
import pkgutil

import numpy as np
import pytest

import pymadagascar
import pymadagascar.api as public_api
import pymadagascar.cli as cli_package
from pymadagascar.generic.linear_operator import (
    ConjugateGradientResult,
    IdentityOperator,
    LeastSquaresProblem,
    LinearOperatorError,
    MatrixOperator,
    SolverResult,
    conjugate_gradient,
    conjugate_gradient_normal,
    run_cg_with_history,
    run_cgnr_with_history,
)


def test_default_cg_behavior_and_result_contract_are_unchanged() -> None:
    matrix = np.array([[4.0, 1.0], [1.0, 3.0]])
    rhs = np.array([1.0, 2.0])

    result = conjugate_gradient(MatrixOperator(matrix), rhs, niter=10, tol=1e-12)

    assert type(result) is ConjugateGradientResult
    assert not hasattr(result, "history")
    np.testing.assert_allclose(result.solution, np.linalg.solve(matrix, rhs))


def test_default_cgnr_behavior_and_result_contract_are_unchanged() -> None:
    matrix = np.array([[1.0, 0.0], [1.0, 1.0], [0.0, 1.0]])
    rhs = np.array([1.0, 2.0, 2.0])

    result = conjugate_gradient_normal(MatrixOperator(matrix), rhs, niter=10, tol=1e-12)

    assert type(result) is ConjugateGradientResult
    assert not hasattr(result, "history")
    np.testing.assert_allclose(result.solution, np.linalg.lstsq(matrix, rhs, rcond=None)[0])


def test_cg_history_records_initial_and_iteration_residuals() -> None:
    matrix = np.array([[4.0, 1.0], [1.0, 3.0]])
    result = run_cg_with_history(MatrixOperator(matrix), np.array([1.0, 2.0]), niter=10, tol=1e-12)

    assert isinstance(result, SolverResult)
    assert result.history is not None
    assert [record.iteration for record in result.history.records] == [0, 1, 2]
    residuals = [record.residual_norm for record in result.history.records]
    assert residuals[-1] <= residuals[0]
    assert result.history.records[1].step_length is not None
    assert result.history.records[0].metadata["residual_space"] == "linear_system"


def test_cg_history_stopping_reason_residual_tolerance() -> None:
    result = run_cg_with_history(
        MatrixOperator(np.eye(2)),
        np.zeros(2),
        niter=5,
        tol=1e-12,
    )

    assert result.converged
    assert result.iterations == 0
    assert result.stopping_reason == "residual_tolerance"
    assert result.history is not None
    assert result.history.stopping_reason == "residual_tolerance"


def test_cg_history_stopping_reason_max_iterations() -> None:
    matrix = np.array([[4.0, 1.0], [1.0, 3.0]])
    result = run_cg_with_history(MatrixOperator(matrix), np.array([1.0, 2.0]), niter=1, tol=0.0)

    assert not result.converged
    assert result.iterations == 1
    assert result.stopping_reason == "max_iterations"


def test_cg_history_invalid_state_is_reported_without_changing_default_error() -> None:
    operator = MatrixOperator(np.zeros((2, 2)))
    rhs = np.ones(2)

    with pytest.raises(LinearOperatorError, match="zero curvature"):
        conjugate_gradient(operator, rhs, niter=2)

    result = run_cg_with_history(operator, rhs, niter=2)
    assert not result.converged
    assert result.stopping_reason == "invalid_state"
    assert result.metadata["invalid_state"] == "CG breakdown: search direction has zero curvature"


def test_cgnr_history_uses_least_squares_problem_diagnostics() -> None:
    matrix = np.array([[1.0, 0.0], [1.0, 1.0], [0.0, 1.0]])
    rhs = np.array([1.0, 2.0, 2.0])
    damp = 0.2
    operator = MatrixOperator(matrix)

    result = run_cgnr_with_history(operator, rhs, niter=10, tol=1e-12, damp=damp)
    problem = LeastSquaresProblem(
        operator,
        rhs,
        regularization=IdentityOperator(2),
        reg_weight=damp,
    )

    assert result.objective == pytest.approx(problem.objective(result.final_model))
    assert result.residual_norm == pytest.approx(problem.diagnostics(result.final_model).total_residual_norm)
    assert result.history is not None
    final_record = result.history.records[-1]
    assert final_record.metadata["residual_space"] == "augmented_least_squares"
    assert final_record.metadata["convergence_residual_space"] == "normal_equation"
    assert final_record.metadata["normal_equation_residual_norm"] == pytest.approx(
        result.metadata["normal_equation_residual_norm"]
    )


def test_complex_cg_and_cgnr_history_are_supported() -> None:
    hermitian = np.array(
        [[4.0 + 0.0j, 1.0 - 0.5j], [1.0 + 0.5j, 3.0 + 0.0j]],
        dtype=np.complex128,
    )
    rhs = np.array([1.0 + 2.0j, 2.0 - 1.0j])
    cg_result = run_cg_with_history(MatrixOperator(hermitian), rhs, niter=10, tol=1e-12)

    rectangular = np.array(
        [[1.0 + 1.0j, 0.0], [1.0, 1.0 - 0.5j], [0.0, 2.0 + 0.25j]],
        dtype=np.complex128,
    )
    data = np.array([1.0 + 0.5j, 2.0 - 0.25j, -1.0 + 0.75j])
    cgnr_result = run_cgnr_with_history(MatrixOperator(rectangular), data, niter=10, tol=1e-12)

    np.testing.assert_allclose(cg_result.final_model, np.linalg.solve(hermitian, rhs))
    np.testing.assert_allclose(
        cgnr_result.final_model,
        np.linalg.solve(rectangular.conj().T @ rectangular, rectangular.conj().T @ data),
    )
    assert cg_result.history is not None
    assert cgnr_result.history is not None


def test_solver_history_result_summary_is_json_safe_and_deterministic() -> None:
    result = run_cg_with_history(
        MatrixOperator(np.diag([2.0, 3.0])),
        np.array([1.0, 1.0]),
        metadata={"stage": "I0-4"},
    )
    summary = result.to_summary()

    assert summary["metadata"]["stage"] == "I0-4"
    assert json.loads(json.dumps(summary, sort_keys=True)) == summary


def test_history_helpers_are_direct_module_only_and_add_no_cli() -> None:
    for name in ["run_cg_with_history", "run_cgnr_with_history"]:
        assert not hasattr(pymadagascar, name)
        assert not hasattr(public_api, name)

    module_names = {module.name for module in pkgutil.iter_modules(cli_package.__path__)}
    assert "cg_history" not in module_names
    assert "cgnr_history" not in module_names
    assert importlib.import_module("pymadagascar.generic.linear_operator")
