from __future__ import annotations

import json

import numpy as np
import pytest

import pymadagascar
import pymadagascar.api as public_api
from pymadagascar.generic.linear_operator import (
    LinearOperatorError,
    SolverHistory,
    SolverIterationRecord,
    SolverResult,
    conjugate_gradient,
    MatrixOperator,
)


def test_solver_history_summary_is_json_serializable_and_deterministic() -> None:
    records = (
        SolverIterationRecord(0, residual_norm=3.0, objective=4.5, metadata={"phase": "start"}),
        SolverIterationRecord(
            1,
            residual_norm=0.25,
            objective=0.03125,
            gradient_norm=0.5,
            step_length=0.75,
            metadata={"accepted": True},
        ),
    )
    history = SolverHistory(records, converged=True, stopping_reason="residual_tol", metadata={"solver": "toy"})
    summary = history.to_summary()

    assert summary == {
        "records": [record.to_summary() for record in records],
        "converged": True,
        "stopping_reason": "residual_tol",
        "final_iteration": 1,
        "metadata": {"solver": "toy"},
    }
    assert json.loads(json.dumps(summary, sort_keys=True)) == summary


def test_solver_result_summary_contains_final_model_and_history() -> None:
    history = SolverHistory(
        (SolverIterationRecord(0, 2.0), SolverIterationRecord(2, 0.1, objective=0.005)),
        converged=False,
        stopping_reason="maxiter",
    )
    result = SolverResult(
        final_model=np.array([1.0, -2.0], dtype=np.float32),
        converged=False,
        iterations=2,
        residual_norm=0.1,
        objective=0.005,
        history=history,
        metadata={"operator": "matrix"},
    )
    summary = result.to_summary()

    assert summary["final_model"] == [1.0, -2.0]
    assert summary["final_model_shape"] == [2]
    assert summary["final_model_dtype"] == "float32"
    assert summary["converged"] is False
    assert summary["iterations"] == 2
    assert summary["stopping_reason"] == "maxiter"
    assert summary["history"]["final_iteration"] == 2
    assert json.loads(json.dumps(summary, sort_keys=True)) == summary


def test_solver_result_summary_handles_complex_models() -> None:
    result = SolverResult(
        final_model=np.array([1.0 + 2.0j, -0.5j], dtype=np.complex64),
        converged=True,
        iterations=1,
        residual_norm=0.0,
        objective=0.0,
        stopping_reason="exact",
    )
    summary = result.to_summary()

    assert summary["final_model"] == [
        {"real": 1.0, "imag": 2.0},
        {"real": 0.0, "imag": -0.5},
    ]
    assert json.loads(json.dumps(summary, sort_keys=True)) == summary


def test_history_and_result_validation_errors_are_clear() -> None:
    with pytest.raises(LinearOperatorError, match="iteration"):
        SolverIterationRecord(-1, residual_norm=1.0)
    with pytest.raises(LinearOperatorError, match="residual_norm"):
        SolverIterationRecord(0, residual_norm=np.nan)
    with pytest.raises(LinearOperatorError, match="gradient_norm"):
        SolverIterationRecord(0, residual_norm=1.0, gradient_norm=-1.0)
    with pytest.raises(LinearOperatorError, match="sorted"):
        SolverHistory((SolverIterationRecord(2, 1.0), SolverIterationRecord(1, 0.5)))
    with pytest.raises(LinearOperatorError, match="stopping_reason"):
        SolverHistory(stopping_reason="")
    with pytest.raises(LinearOperatorError, match="final_model"):
        SolverResult(
            final_model=np.array([1.0, np.inf]),
            converged=False,
            iterations=0,
            residual_norm=1.0,
        )


def test_solver_history_is_not_public_root_or_api_export() -> None:
    for name in ["SolverIterationRecord", "SolverHistory", "SolverResult"]:
        assert not hasattr(pymadagascar, name)
        assert not hasattr(public_api, name)


def test_existing_conjugate_gradient_result_contract_is_unchanged() -> None:
    matrix = MatrixOperator(np.array([[4.0, 1.0], [1.0, 3.0]]))
    rhs = np.array([1.0, 2.0])

    result = conjugate_gradient(matrix, rhs, niter=10, tol=1e-12)

    assert hasattr(result, "solution")
    assert hasattr(result, "residual_norm")
    assert hasattr(result, "iterations")
    assert hasattr(result, "converged")
    assert not hasattr(result, "history")
    np.testing.assert_allclose(result.solution, np.linalg.solve(matrix.matrix, rhs), rtol=1e-10, atol=1e-10)
