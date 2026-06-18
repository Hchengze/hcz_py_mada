from __future__ import annotations

import importlib
import pkgutil

import numpy as np
import pytest

import pymadagascar
import pymadagascar.api as public_api
import pymadagascar.cli as cli_package
from pymadagascar.generic.linear_operator import (
    ComposedOperator,
    IdentityOperator,
    LinearOperatorError,
    MatrixOperator,
    ScaledOperator,
    StackedOperator,
    SumOperator,
    complex_dot_test,
    dot_test,
)


def test_scaled_operator_forward_adjoint_and_real_dot_test() -> None:
    matrix = np.array([[1.0, 2.0], [3.0, -1.0], [0.5, 4.0]])
    base = MatrixOperator(matrix)
    operator = ScaledOperator(base, 2.5)
    model = np.array([2.0, -1.0])
    data = np.array([1.0, -2.0, 0.5])

    np.testing.assert_allclose(operator.forward(model), 2.5 * (matrix @ model))
    np.testing.assert_allclose(operator.adjoint(data), 2.5 * (matrix.T @ data))
    assert operator.model_shape == (2,)
    assert operator.data_shape == (3,)
    assert operator.metadata["operator_type"] == "scaled"
    assert dot_test(operator, seed=11).passed


def test_complex_scaled_operator_uses_hermitian_adjoint() -> None:
    matrix = np.array([[1.0 + 2.0j, 0.5 - 1.0j], [2.0 - 0.25j, -1.0j]])
    alpha = 1.5 - 0.75j
    base = MatrixOperator(matrix)
    operator = alpha * base
    data = np.array([0.25 + 0.5j, -1.0 + 2.0j])

    np.testing.assert_allclose(operator.adjoint(data), np.conjugate(alpha) * (matrix.conj().T @ data))
    assert complex_dot_test(operator, seed=9, rtol=1e-11, atol=1e-11).passed


def test_sum_operator_forward_adjoint_and_dot_test() -> None:
    left_matrix = np.array([[1.0, 2.0], [0.0, -1.0], [3.0, 0.5]])
    right_matrix = np.array([[0.5, -1.0], [2.0, 0.25], [1.0, 1.0]])
    left = MatrixOperator(left_matrix)
    right = MatrixOperator(right_matrix)
    operator = SumOperator(left, right)
    model = np.array([1.5, -2.0])
    data = np.array([0.25, 1.0, -0.5])

    expected = (left_matrix + right_matrix) @ model
    expected_adjoint = (left_matrix + right_matrix).T @ data
    np.testing.assert_allclose(operator.forward(model), expected)
    np.testing.assert_allclose(operator.adjoint(data), expected_adjoint)
    assert operator.metadata["operator_type"] == "sum"
    assert dot_test(left + right, seed=3).passed


def test_composed_operator_forward_adjoint_and_dot_test() -> None:
    outer_matrix = np.array([[1.0, 2.0, -1.0], [0.5, 0.0, 3.0]])
    inner_matrix = np.array([[2.0, -1.0, 0.0, 1.0], [0.0, 3.0, 1.0, -2.0], [1.0, 0.5, -0.5, 0.0]])
    outer = MatrixOperator(outer_matrix)
    inner = MatrixOperator(inner_matrix)
    operator = ComposedOperator(outer, inner)
    model = np.array([1.0, -1.0, 2.0, 0.5])
    data = np.array([0.25, -2.0])

    expected_matrix = outer_matrix @ inner_matrix
    np.testing.assert_allclose(operator.forward(model), expected_matrix @ model)
    np.testing.assert_allclose(operator.adjoint(data), expected_matrix.T @ data)
    assert operator.model_shape == (4,)
    assert operator.data_shape == (2,)
    assert operator.metadata["operator_type"] == "composed"
    assert dot_test(outer @ inner, seed=5).passed


def test_stacked_operator_forward_adjoint_and_dot_test() -> None:
    first_matrix = np.array([[1.0, 0.0, 2.0], [0.5, -1.0, 0.0]])
    second_matrix = np.array([[2.0, 1.0, -1.0], [0.0, 3.0, 0.5], [1.0, 0.0, 1.0]])
    first = MatrixOperator(first_matrix)
    second = MatrixOperator(second_matrix)
    operator = StackedOperator([first, second])
    model = np.array([1.0, -2.0, 0.5])
    data = np.arange(5.0)

    np.testing.assert_allclose(
        operator.forward(model),
        np.concatenate([first_matrix @ model, second_matrix @ model]),
    )
    expected_adjoint = first_matrix.T @ data[:2] + second_matrix.T @ data[2:]
    np.testing.assert_allclose(operator.adjoint(data), expected_adjoint)
    assert operator.data_shape == (5,)
    assert operator.metadata["operator_type"] == "stacked"
    assert operator.metadata["component_count"] == 2
    assert dot_test(operator, seed=13).passed


def test_identity_composition_preserves_operator_behavior() -> None:
    matrix = np.array([[1.0, -2.0], [0.5, 3.0], [2.0, 1.0]])
    operator = MatrixOperator(matrix)
    model_identity = IdentityOperator(operator.model_shape)
    data_identity = IdentityOperator(operator.data_shape)
    model = np.array([0.25, -1.5])

    np.testing.assert_allclose((operator @ model_identity).forward(model), operator.forward(model))
    np.testing.assert_allclose((data_identity @ operator).forward(model), operator.forward(model))


def test_shape_mismatch_errors_are_clear() -> None:
    a = MatrixOperator(np.ones((3, 2)))
    b = MatrixOperator(np.ones((4, 2)))
    c = MatrixOperator(np.ones((4, 3)))

    with pytest.raises(LinearOperatorError, match="data shapes"):
        SumOperator(a, b)
    with pytest.raises(LinearOperatorError, match="inner data_shape"):
        ComposedOperator(a, b)
    with pytest.raises(LinearOperatorError, match="matching model shapes"):
        StackedOperator([a, c])
    with pytest.raises(LinearOperatorError, match="at least one"):
        StackedOperator([])


def test_finite_input_policy_for_operator_composition() -> None:
    operator = 2.0 * MatrixOperator(np.eye(2))

    with pytest.raises(LinearOperatorError, match="non-finite"):
        operator.forward(np.array([1.0, np.nan]))
    with pytest.raises(LinearOperatorError, match="non-finite"):
        operator.adjoint(np.array([1.0, np.inf]))
    with pytest.raises(LinearOperatorError, match="non-finite"):
        MatrixOperator(np.array([[1.0, np.nan]]))


def test_new_composition_helpers_are_not_root_or_api_exports() -> None:
    for name in ["ScaledOperator", "SumOperator", "ComposedOperator", "StackedOperator"]:
        assert not hasattr(pymadagascar, name)
        assert not hasattr(public_api, name)


def test_no_cli_modules_added_for_operator_composition() -> None:
    module_names = {module.name for module in pkgutil.iter_modules(cli_package.__path__)}

    assert "operator_composition" not in module_names
    assert "solver_history" not in module_names
    assert "lsqr" not in module_names
    assert "cgls" not in module_names
    assert importlib.import_module("pymadagascar.generic.linear_operator")
