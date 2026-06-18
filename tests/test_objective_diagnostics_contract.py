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
    FirstDifferenceRegularization,
    LeastSquaresProblem,
    LinearOperatorError,
    MatrixOperator,
    ObjectiveDiagnostics,
    SolverHistory,
    SolverIterationRecord,
    StoppingDiagnostics,
    conjugate_gradient,
)


def test_objective_diagnostics_summary_is_json_safe_and_deterministic() -> None:
    problem = LeastSquaresProblem(
        MatrixOperator(np.array([[1.0, 2.0], [0.5, -1.0]])),
        np.array([1.0, -2.0]),
        regularization=FirstDifferenceRegularization(2),
        reg_weight=0.25,
        metadata={"problem": "toy"},
    )
    summary = problem.to_summary(np.array([2.0, -1.0]), iteration=3, metadata={"stage": "I0-3"})

    assert summary["iteration"] == 3
    assert summary["objective"] == pytest.approx(summary["data_objective"] + summary["regularization_objective"])
    assert summary["total_residual_norm"] >= summary["data_residual_norm"]
    assert summary["gradient_norm"] is not None
    assert summary["converged"] is False
    assert summary["stopping_reason"] == "not_converged"
    assert summary["metadata"]["problem"] == "toy"
    assert summary["metadata"]["stage"] == "I0-3"
    assert summary["metadata"]["model_shape"] == [2]
    assert summary["metadata"]["regularization_shape"] == [1]
    assert json.loads(json.dumps(summary, sort_keys=True)) == summary


def test_objective_diagnostics_can_become_iteration_record() -> None:
    diagnostic = ObjectiveDiagnostics(
        objective=1.25,
        data_objective=1.0,
        regularization_objective=0.25,
        data_residual_norm=2.0**0.5,
        regularization_residual_norm=0.5**0.5,
        total_residual_norm=2.5**0.5,
        iteration=4,
        gradient_norm=0.75,
        metadata={"accepted": True},
    )
    record = diagnostic.to_iteration_record()

    assert record.iteration == 4
    assert record.objective == pytest.approx(1.25)
    assert record.residual_norm == pytest.approx(2.5**0.5)
    assert record.gradient_norm == pytest.approx(0.75)
    assert record.metadata == {"accepted": True}


def test_stopping_diagnostics_threshold_reasons() -> None:
    assert (
        StoppingDiagnostics.from_thresholds(iteration=2, residual_norm=1e-4, residual_tolerance=1e-3).stopping_reason
        == "residual_tolerance"
    )
    assert (
        StoppingDiagnostics.from_thresholds(iteration=2, objective=1e-5, objective_tolerance=1e-4).stopping_reason
        == "objective_tolerance"
    )
    assert (
        StoppingDiagnostics.from_thresholds(iteration=2, gradient_norm=1e-6, gradient_tolerance=1e-5).stopping_reason
        == "gradient_tolerance"
    )
    maxiter = StoppingDiagnostics.from_thresholds(iteration=10, max_iterations=10)
    assert maxiter.stopping_reason == "max_iterations"
    assert maxiter.converged is False
    not_converged = StoppingDiagnostics.from_thresholds(iteration=1, residual_norm=10.0)
    assert not_converged.stopping_reason == "not_converged"
    invalid = StoppingDiagnostics.from_thresholds(iteration=1, invalid_state=True)
    assert invalid.stopping_reason == "invalid_state"
    assert invalid.converged is False


def test_stopping_diagnostics_summary_is_json_safe() -> None:
    diagnostic = StoppingDiagnostics.from_thresholds(
        iteration=5,
        residual_norm=0.1,
        objective=0.005,
        gradient_norm=0.2,
        max_iterations=5,
        metadata={"solver": "prototype"},
    )
    summary = diagnostic.to_summary()

    assert summary == {
        "iteration": 5,
        "converged": False,
        "stopping_reason": "max_iterations",
        "residual_norm": 0.1,
        "objective": 0.005,
        "gradient_norm": 0.2,
        "metadata": {"solver": "prototype"},
    }
    assert json.loads(json.dumps(summary, sort_keys=True)) == summary


def test_diagnostics_validation_errors_are_clear() -> None:
    with pytest.raises(LinearOperatorError, match="objective"):
        ObjectiveDiagnostics(
            objective=np.nan,
            data_objective=0.0,
            regularization_objective=0.0,
            data_residual_norm=0.0,
            regularization_residual_norm=0.0,
            total_residual_norm=0.0,
        )
    with pytest.raises(LinearOperatorError, match="iteration"):
        StoppingDiagnostics(iteration=-1, converged=False, stopping_reason="not_converged")
    with pytest.raises(LinearOperatorError, match="residual_tolerance"):
        StoppingDiagnostics.from_thresholds(iteration=0, residual_tolerance=-1.0)
    with pytest.raises(LinearOperatorError, match="max_iterations"):
        StoppingDiagnostics.from_thresholds(iteration=0, max_iterations=-1)


def test_problem_iteration_record_and_solver_result_are_summary_compatible() -> None:
    problem = LeastSquaresProblem(
        MatrixOperator(np.array([[1.0, 0.0], [0.0, 2.0]])),
        np.array([1.0, -1.0]),
        regularization=FirstDifferenceRegularization(2),
        reg_weight=0.1,
    )
    model0 = np.array([0.0, 0.0])
    model1 = np.array([1.0, -0.25])
    records = (
        problem.iteration_record(model0, iteration=0),
        problem.iteration_record(model1, iteration=1, metadata={"accepted": True}),
    )
    history = SolverHistory(records, converged=False, stopping_reason="max_iterations")
    result = problem.solver_result(
        model1,
        iterations=1,
        converged=False,
        stopping_reason="max_iterations",
        history=history,
    )
    summary = result.to_summary()

    assert summary["iterations"] == 1
    assert summary["objective"] == pytest.approx(problem.objective(model1))
    assert summary["residual_norm"] == pytest.approx(problem.diagnostics(model1).total_residual_norm)
    assert summary["history"]["records"][1]["metadata"]["accepted"] is True
    assert json.loads(json.dumps(summary, sort_keys=True)) == summary


def test_problem_and_diagnostics_are_not_public_root_or_api_exports() -> None:
    for name in ["LeastSquaresProblem", "ObjectiveDiagnostics", "StoppingDiagnostics"]:
        assert not hasattr(pymadagascar, name)
        assert not hasattr(public_api, name)


def test_no_cli_modules_added_for_problem_layer() -> None:
    module_names = {module.name for module in pkgutil.iter_modules(cli_package.__path__)}

    assert "least_squares_problem" not in module_names
    assert "objective_diagnostics" not in module_names
    assert "stopping_diagnostics" not in module_names
    assert "lsqr" not in module_names
    assert "cgls" not in module_names
    assert importlib.import_module("pymadagascar.generic.linear_operator")


def test_existing_conjugate_gradient_result_contract_still_has_no_history() -> None:
    result = conjugate_gradient(MatrixOperator(np.array([[2.0, 0.0], [0.0, 3.0]])), np.array([1.0, 1.0]), niter=5)

    assert hasattr(result, "solution")
    assert hasattr(result, "residual_norm")
    assert hasattr(result, "iterations")
    assert hasattr(result, "converged")
    assert not hasattr(result, "history")
