from __future__ import annotations

import importlib
import pkgutil

import numpy as np
import pytest

import pymadagascar
import pymadagascar.api as public_api
import pymadagascar.cli as cli_package
from pymadagascar.generic.linear_operator import (
    DiagonalRegularization,
    FirstDifferenceRegularization,
    IdentityOperator,
    LinearOperatorError,
    MatrixOperator,
    SecondDifferenceRegularization,
    StackedOperator,
    complex_dot_test,
    dot_test,
)


def test_identity_and_damping_regularization_reuse_existing_operators() -> None:
    model = np.array([[1.0, -2.0], [3.0, 0.5]])
    identity = IdentityOperator(model.shape)
    damping = 0.25 * identity

    np.testing.assert_allclose(identity.forward(model), model)
    np.testing.assert_allclose(damping.forward(model), 0.25 * model)
    np.testing.assert_allclose(damping.adjoint(model), 0.25 * model)
    assert dot_test(damping, seed=10).passed


def test_diagonal_regularization_forward_adjoint_and_dot_test() -> None:
    weights = np.array([1.0, 2.0, -0.5, 0.25])
    operator = DiagonalRegularization(weights, model_shape=(2, 2))
    model = np.array([[2.0, -1.0], [4.0, 8.0]])
    data = np.array([[1.0, 0.5], [-2.0, 3.0]])

    np.testing.assert_allclose(operator.forward(model), weights.reshape(2, 2) * model)
    np.testing.assert_allclose(operator.adjoint(data), weights.reshape(2, 2) * data)
    assert operator.model_shape == (2, 2)
    assert operator.data_shape == (2, 2)
    assert operator.metadata["operator_type"] == "diagonal_regularization"
    assert dot_test(operator, seed=12).passed


def test_complex_diagonal_regularization_uses_conjugate_adjoint() -> None:
    weights = np.array([1.0 + 2.0j, -0.5j, 3.0 - 1.0j])
    operator = DiagonalRegularization(weights)
    data = np.array([2.0 - 1.0j, 0.5 + 2.0j, -1.0 + 0.25j])

    np.testing.assert_allclose(operator.adjoint(data), np.conjugate(weights) * data)
    assert operator.metadata["complex_weights"] is True
    assert complex_dot_test(operator, seed=5, rtol=1e-11, atol=1e-11).passed


def test_first_difference_forward_adjoint_boundary_rule() -> None:
    operator = FirstDifferenceRegularization(5)
    model = np.array([1.0, 3.0, 2.0, 8.0, 5.0])
    data = np.array([2.0, -1.0, 0.5, 4.0])

    np.testing.assert_allclose(operator.forward(model), np.array([2.0, -1.0, 6.0, -3.0]))
    np.testing.assert_allclose(operator.adjoint(data), np.array([-2.0, 3.0, -1.5, -3.5, 4.0]))
    assert operator.data_shape == (4,)
    assert operator.metadata["boundary"] == "valid"
    assert operator.metadata["stencil"] == [-1.0, 1.0]


def test_first_difference_real_and_complex_dot_tests() -> None:
    real_operator = FirstDifferenceRegularization((2, 3))
    complex_operator = FirstDifferenceRegularization(6, dtype=np.complex128)

    assert dot_test(real_operator, seed=4).passed
    assert complex_dot_test(complex_operator, seed=6, rtol=1e-11, atol=1e-11).passed


def test_second_difference_forward_adjoint_and_dot_test() -> None:
    operator = SecondDifferenceRegularization(5)
    model = np.array([1.0, 3.0, 2.0, 8.0, 5.0])
    data = np.array([2.0, -1.0, 0.5])

    np.testing.assert_allclose(operator.forward(model), np.array([-3.0, 7.0, -9.0]))
    np.testing.assert_allclose(operator.adjoint(data), np.array([2.0, -5.0, 4.5, -2.0, 0.5]))
    assert operator.data_shape == (3,)
    assert operator.metadata["stencil"] == [1.0, -2.0, 1.0]
    assert dot_test(operator, seed=8).passed


def test_regularization_shape_and_finite_validation() -> None:
    with pytest.raises(LinearOperatorError, match="weights has 3 samples, expected 4"):
        DiagonalRegularization(np.ones(3), model_shape=(2, 2))
    with pytest.raises(LinearOperatorError, match="non-finite"):
        DiagonalRegularization(np.array([1.0, np.nan]))
    with pytest.raises(LinearOperatorError, match="at least 2 samples"):
        FirstDifferenceRegularization(1)
    with pytest.raises(LinearOperatorError, match="at least 3 samples"):
        SecondDifferenceRegularization(2)


def test_regularization_rejects_non_finite_inputs() -> None:
    diagonal = DiagonalRegularization(np.ones(3))
    first_difference = FirstDifferenceRegularization(3)

    with pytest.raises(LinearOperatorError, match="non-finite"):
        diagonal.forward(np.array([1.0, np.nan, 2.0]))
    with pytest.raises(LinearOperatorError, match="non-finite"):
        diagonal.adjoint(np.array([1.0, np.inf, 2.0]))
    with pytest.raises(LinearOperatorError, match="non-finite"):
        first_difference.forward(np.array([1.0, np.nan, 2.0]))


def test_stacked_data_and_regularization_operator_is_dot_test_ready() -> None:
    data_operator = MatrixOperator(np.array([[1.0, 0.0, 2.0, -1.0], [0.5, 3.0, 0.0, 1.0]]))
    regularization = 0.1 * FirstDifferenceRegularization(4)
    stacked = StackedOperator([data_operator, regularization])
    model = np.array([1.0, -2.0, 0.5, 3.0])
    data = np.arange(5.0)

    np.testing.assert_allclose(
        stacked.forward(model),
        np.concatenate([data_operator.forward(model), regularization.forward(model)]),
    )
    np.testing.assert_allclose(
        stacked.adjoint(data),
        data_operator.adjoint(data[:2]) + regularization.adjoint(data[2:]),
    )
    assert stacked.model_shape == (4,)
    assert stacked.data_shape == (5,)
    assert dot_test(stacked, seed=14).passed


def test_regularization_composes_with_existing_operator_algebra() -> None:
    smoother = MatrixOperator(np.array([[0.5, 0.5, 0.0], [0.0, 0.5, 0.5]]))
    diagonal = DiagonalRegularization(np.array([1.0, 2.0, 3.0]))
    composed = smoother @ diagonal
    model = np.array([1.0, -1.0, 2.0])

    np.testing.assert_allclose(composed.forward(model), smoother.forward(diagonal.forward(model)))
    assert composed.model_shape == (3,)
    assert composed.data_shape == (2,)
    assert dot_test(composed, seed=16).passed


def test_regularization_operators_are_not_root_or_api_exports() -> None:
    for name in [
        "DiagonalRegularization",
        "FirstDifferenceRegularization",
        "SecondDifferenceRegularization",
    ]:
        assert not hasattr(pymadagascar, name)
        assert not hasattr(public_api, name)


def test_no_cli_modules_added_for_regularization_subset() -> None:
    module_names = {module.name for module in pkgutil.iter_modules(cli_package.__path__)}

    assert "regularization" not in module_names
    assert "diagonal_regularization" not in module_names
    assert "first_difference_regularization" not in module_names
    assert "second_difference_regularization" not in module_names
    assert "lsqr" not in module_names
    assert "cgls" not in module_names
    assert importlib.import_module("pymadagascar.generic.linear_operator")
