from __future__ import annotations

import numpy as np
import pytest

from pymadagascar.generic.linear_operator import (
    CallableLinearOperator,
    FirstDifferenceRegularization,
    LeastSquaresProblem,
    LinearOperatorError,
    MatrixOperator,
    StackedOperator,
)


def test_unregularized_residual_and_objective_match_matrix_reference() -> None:
    matrix = np.array([[1.0, 2.0], [0.5, -1.0], [3.0, 0.0]])
    data = np.array([1.0, -2.0, 0.5])
    model = np.array([2.0, -1.0])
    problem = LeastSquaresProblem(MatrixOperator(matrix), data)

    expected_residual = matrix @ model - data

    np.testing.assert_allclose(problem.data_residual(model), expected_residual)
    np.testing.assert_allclose(problem.regularization_residual(model), np.zeros(0))
    np.testing.assert_allclose(problem.total_residual(model), expected_residual)
    assert problem.objective(model) == pytest.approx(0.5 * np.vdot(expected_residual, expected_residual).real)
    assert problem.has_regularization is False


def test_regularized_residual_objective_and_stacked_consistency() -> None:
    matrix = np.array([[1.0, 0.0, 2.0], [0.5, -1.0, 1.0]])
    data = np.array([1.0, 0.25])
    model = np.array([2.0, -1.0, 0.5])
    regularization = FirstDifferenceRegularization(3)
    weight = 0.2
    problem = LeastSquaresProblem(MatrixOperator(matrix), data, regularization=regularization, reg_weight=weight)
    stacked = StackedOperator([MatrixOperator(matrix), weight * regularization])

    expected_data_residual = matrix @ model - data
    expected_regularization_residual = weight * np.diff(model)
    expected_total = np.concatenate([expected_data_residual, expected_regularization_residual])
    stacked_rhs = np.concatenate([data, np.zeros(regularization.data_size)])

    np.testing.assert_allclose(problem.data_residual(model), expected_data_residual)
    np.testing.assert_allclose(problem.regularization_residual(model), expected_regularization_residual)
    np.testing.assert_allclose(problem.total_residual(model), expected_total)
    np.testing.assert_allclose(problem.total_residual(model), stacked.forward(model) - stacked_rhs)
    assert problem.objective(model) == pytest.approx(0.5 * np.vdot(expected_total, expected_total).real)
    assert problem.has_regularization is True
    assert problem.regularization_shape == regularization.data_shape


def test_zero_regularization_weight_equals_no_regularization() -> None:
    matrix = np.array([[2.0, 0.0], [0.0, 3.0]])
    data = np.array([1.0, -1.0])
    model = np.array([0.5, 0.25])
    unregularized = LeastSquaresProblem(MatrixOperator(matrix), data)
    zero_weight = LeastSquaresProblem(
        MatrixOperator(matrix),
        data,
        regularization=FirstDifferenceRegularization(2),
        reg_weight=0.0,
    )

    np.testing.assert_allclose(zero_weight.total_residual(model), unregularized.total_residual(model))
    assert zero_weight.objective(model) == pytest.approx(unregularized.objective(model))
    assert zero_weight.has_regularization is False
    assert zero_weight.regularization_shape is None


def test_gradient_matches_explicit_regularized_matrix_reference() -> None:
    matrix = np.array([[1.0, 2.0, 0.0], [0.5, -1.0, 3.0]])
    difference_matrix = np.array([[-1.0, 1.0, 0.0], [0.0, -1.0, 1.0]])
    data = np.array([1.0, -2.0])
    model = np.array([0.5, -1.5, 2.0])
    weight = 0.3
    problem = LeastSquaresProblem(
        MatrixOperator(matrix),
        data,
        regularization=FirstDifferenceRegularization(3),
        reg_weight=weight,
    )

    expected = matrix.T @ (matrix @ model - data) + (weight**2) * difference_matrix.T @ (difference_matrix @ model)

    np.testing.assert_allclose(problem.gradient(model), expected)


def test_gradient_matches_finite_difference_directional_derivative() -> None:
    matrix = np.array([[1.0, -2.0, 0.5], [0.25, 1.0, 2.0]])
    data = np.array([0.75, -1.25])
    model = np.array([0.5, -0.25, 1.5])
    direction = np.array([0.3, -0.7, 0.2])
    problem = LeastSquaresProblem(
        MatrixOperator(matrix),
        data,
        regularization=FirstDifferenceRegularization(3),
        reg_weight=0.15,
    )

    eps = 1e-6
    finite_difference = (problem.objective(model + eps * direction) - problem.objective(model - eps * direction)) / (
        2.0 * eps
    )
    directional_gradient = float(np.vdot(problem.gradient(model), direction).real)

    assert directional_gradient == pytest.approx(finite_difference, rel=1e-7, abs=1e-7)


def test_complex_problem_uses_hermitian_residual_objective_and_gradient() -> None:
    matrix = np.array([[1.0 + 0.5j, 2.0 - 1.0j], [0.25j, -1.0 + 0.75j]])
    data = np.array([1.0 - 1.0j, 0.5 + 0.25j])
    model = np.array([0.25 + 0.5j, -1.0 + 0.75j])
    problem = LeastSquaresProblem(MatrixOperator(matrix), data)

    residual = matrix @ model - data

    np.testing.assert_allclose(problem.data_residual(model), residual)
    assert problem.objective(model) == pytest.approx(0.5 * np.vdot(residual, residual).real)
    np.testing.assert_allclose(problem.gradient(model), matrix.conj().T @ residual)


def test_problem_shape_mismatches_raise_clear_errors() -> None:
    operator = MatrixOperator(np.ones((3, 2)))

    with pytest.raises(LinearOperatorError, match="data has 2 samples, expected 3"):
        LeastSquaresProblem(operator, np.ones(2))
    with pytest.raises(LinearOperatorError, match="regularization model_shape"):
        LeastSquaresProblem(operator, np.ones(3), regularization=FirstDifferenceRegularization(3), reg_weight=1.0)
    with pytest.raises(LinearOperatorError, match="model has 3 samples, expected 2"):
        LeastSquaresProblem(operator, np.ones(3)).data_residual(np.ones(3))


def test_problem_rejects_non_finite_data_model_weight_and_operator_output() -> None:
    operator = MatrixOperator(np.eye(2))

    with pytest.raises(LinearOperatorError, match="data contains non-finite"):
        LeastSquaresProblem(operator, np.array([1.0, np.nan]))
    with pytest.raises(LinearOperatorError, match="reg_weight"):
        LeastSquaresProblem(operator, np.ones(2), reg_weight=np.inf)
    with pytest.raises(LinearOperatorError, match="reg_weight"):
        LeastSquaresProblem(operator, np.ones(2), reg_weight=-1.0)
    with pytest.raises(LinearOperatorError, match="model contains non-finite"):
        LeastSquaresProblem(operator, np.ones(2)).objective(np.array([1.0, np.nan]))

    bad_operator = CallableLinearOperator(
        2,
        2,
        lambda model: np.array([model.reshape(-1)[0], np.nan]),
        lambda data: np.asarray(data),
    )
    with pytest.raises(LinearOperatorError, match="forward result contains non-finite"):
        LeastSquaresProblem(bad_operator, np.ones(2)).data_residual(np.ones(2))
