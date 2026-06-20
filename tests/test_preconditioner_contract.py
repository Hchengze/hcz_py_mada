from __future__ import annotations

import inspect
import json
import pkgutil

import numpy as np
import pytest

import pymadagascar
import pymadagascar.api as public_api
import pymadagascar.cli as cli_package
import pymadagascar.generic.linear_operator as linear_operator
from pymadagascar.generic.linear_operator import (
    DiagonalPreconditioner,
    DiagonalRegularization,
    FirstDifferenceRegularization,
    IdentityPreconditioner,
    LeastSquaresProblem,
    LinearOperatorError,
    MatrixOperator,
    Preconditioner,
    as_preconditioner,
    run_cgls,
)


def test_identity_preconditioner_preserves_model_and_adjoint() -> None:
    preconditioner = IdentityPreconditioner((2, 2))
    model = np.arange(4.0).reshape(2, 2)

    np.testing.assert_array_equal(preconditioner.forward(model), model)
    np.testing.assert_array_equal(preconditioner.adjoint(model), model)
    assert isinstance(preconditioner, Preconditioner)


def test_diagonal_preconditioner_scales_model() -> None:
    preconditioner = DiagonalPreconditioner(np.array([0.5, 2.0, 4.0]))
    np.testing.assert_allclose(
        preconditioner.forward(np.array([2.0, 3.0, -1.0])),
        np.array([1.0, 6.0, -4.0]),
    )


def test_complex_diagonal_adjoint_uses_conjugate_weights() -> None:
    weights = np.array([1.0 + 2.0j, -0.5j])
    data = np.array([2.0 - 1.0j, 3.0 + 0.25j])
    preconditioner = DiagonalPreconditioner(weights)

    np.testing.assert_allclose(preconditioner.adjoint(data), weights.conj() * data)
    assert preconditioner.diagnostics().complex_supported


def test_diagonal_preconditioner_rejects_invalid_shape_and_nonfinite_weights() -> None:
    with pytest.raises(LinearOperatorError, match="expected 3"):
        DiagonalPreconditioner(np.ones(2), model_shape=3)
    with pytest.raises(LinearOperatorError, match="non-finite"):
        DiagonalPreconditioner(np.array([1.0, np.nan]))


def test_diagonal_preconditioner_rejects_zero_weights_as_noninvertible_scaling() -> None:
    with pytest.raises(LinearOperatorError, match="nonzero"):
        DiagonalPreconditioner(np.array([1.0, 0.0]))


def test_preconditioner_is_semantically_distinct_from_regularization() -> None:
    preconditioner = DiagonalPreconditioner(np.array([1.0, 2.0]))
    regularization = DiagonalRegularization(np.array([1.0, 2.0]))

    assert isinstance(preconditioner, Preconditioner)
    assert not isinstance(regularization, Preconditioner)
    assert preconditioner.diagnostics().metadata["changes_objective"] is False
    with pytest.raises(LinearOperatorError, match="not implicitly a preconditioner"):
        as_preconditioner(regularization)  # type: ignore[arg-type]


def test_right_preconditioned_operator_composition_has_expected_shape() -> None:
    operator = MatrixOperator(np.ones((4, 3)))
    preconditioner = DiagonalPreconditioner(np.array([1.0, 2.0, 0.5]))
    composed = operator @ preconditioner

    assert composed.model_shape == preconditioner.model_shape
    assert composed.data_shape == operator.data_shape
    np.testing.assert_allclose(composed.forward(np.ones(3)), np.array([3.5] * 4))


def test_right_preconditioned_regularized_problem_can_be_formed_without_solver() -> None:
    operator = MatrixOperator(np.eye(3))
    regularization = FirstDifferenceRegularization(3)
    preconditioner = DiagonalPreconditioner(np.array([0.5, 1.0, 2.0]))
    problem = LeastSquaresProblem(
        operator @ preconditioner,
        np.ones(3),
        regularization=regularization @ preconditioner,
        reg_weight=0.25,
    )

    latent = np.array([1.0, 2.0, 3.0])
    assert problem.model_shape == latent.shape
    assert np.isfinite(problem.objective(latent))
    np.testing.assert_allclose(preconditioner.forward(latent), np.array([0.5, 2.0, 6.0]))


def test_preconditioner_diagnostics_are_json_safe() -> None:
    summary = DiagonalPreconditioner(np.array([0.5, 2.0, 4.0])).diagnostics().to_summary()

    assert summary["kind"] == "diagonal"
    assert summary["domain_shape"] == [3]
    assert summary["range_shape"] == [3]
    assert summary["is_diagonal"] is True
    assert summary["scale_range"] == [0.5, 4.0]
    assert summary["condition_hint"] == pytest.approx(8.0)
    assert json.loads(json.dumps(summary, sort_keys=True)) == summary


def test_as_preconditioner_normalizes_identity_array_and_existing_contract() -> None:
    identity = as_preconditioner(None, model_shape=2)
    diagonal = as_preconditioner(np.array([1.0, 2.0]), model_shape=2)

    assert isinstance(identity, IdentityPreconditioner)
    assert isinstance(diagonal, DiagonalPreconditioner)
    assert as_preconditioner(diagonal, model_shape=2) is diagonal
    with pytest.raises(LinearOperatorError, match="range_shape"):
        as_preconditioner(diagonal, model_shape=3)


def test_preconditioner_contract_adds_no_cli_or_stable_export() -> None:
    names = [
        "Preconditioner",
        "PreconditionerDiagnostics",
        "IdentityPreconditioner",
        "DiagonalPreconditioner",
        "as_preconditioner",
    ]
    for name in names:
        assert hasattr(linear_operator, name)
        assert not hasattr(pymadagascar, name)
        assert not hasattr(public_api, name)
    module_names = {module.name for module in pkgutil.iter_modules(cli_package.__path__)}
    assert "preconditioner" not in module_names
    assert "precondition" not in module_names


def test_run_cgls_default_contract_is_unchanged_with_keyword_preconditioner() -> None:
    signature = inspect.signature(run_cgls)
    assert "preconditioner" in signature.parameters
    assert signature.parameters["preconditioner"].kind is inspect.Parameter.KEYWORD_ONLY
    assert signature.parameters["preconditioner"].default is None
    matrix = np.array([[1.0, 0.0], [1.0, 1.0], [0.0, 1.0]])
    data = np.array([1.0, 2.0, 2.0])
    result = run_cgls(matrix, data, maxiter=10, tol=1e-12)
    np.testing.assert_allclose(result.final_model, np.linalg.lstsq(matrix, data, rcond=None)[0])


def test_lsqr_symbol_and_preconditioned_solvers_remain_unimplemented() -> None:
    assert hasattr(linear_operator, "run_lsqr")
    assert hasattr(linear_operator, "run_lsqr_problem")
    for name in ["lsqr", "run_preconditioned_cgls", "run_pcgls"]:
        assert not hasattr(linear_operator, name)
