"""Small in-memory regularization operators."""

from __future__ import annotations

import numpy as np

from pymadagascar.generic.operators import (
    LinearOperator,
    LinearOperatorError,
    _check_finite_values,
    _flatten_finite_to_size,
    _normalize_shape,
    _shape_size,
)


class DiagonalRegularization(LinearOperator):
    """Pointwise diagonal regularization operator ``Lx = w * x``.

    Complex weights are supported; the adjoint uses conjugated weights.
    """

    def __init__(
        self,
        weights: np.ndarray,
        *,
        model_shape: tuple[int, ...] | int | None = None,
    ) -> None:
        weight_array = np.asarray(weights)
        if weight_array.size == 0:
            raise LinearOperatorError("weights must contain at least one sample")
        _check_finite_values(weight_array, "weights")

        if model_shape is None:
            normalized_model_shape = _normalize_shape(weight_array.shape, "model_shape")
        else:
            normalized_model_shape = _normalize_shape(model_shape, "model_shape")
        model_size = _shape_size(normalized_model_shape)
        if weight_array.size != model_size:
            raise LinearOperatorError(f"weights has {weight_array.size} samples, expected {model_size}")

        self.weights = weight_array.reshape(normalized_model_shape).copy()
        super().__init__(
            normalized_model_shape,
            normalized_model_shape,
            dtype=weight_array.dtype,
            metadata={
                "operator_type": "diagonal_regularization",
                "model_shape": normalized_model_shape,
                "complex_weights": bool(np.iscomplexobj(weight_array)),
            },
        )

    def forward(self, model: np.ndarray) -> np.ndarray:
        model_arr = _flatten_finite_to_size(model, self.model_size, "model").reshape(self.model_shape)
        result = self.weights * model_arr
        return _flatten_finite_to_size(result, self.data_size, "forward result").reshape(self.data_shape)

    def adjoint(self, data: np.ndarray) -> np.ndarray:
        data_arr = _flatten_finite_to_size(data, self.data_size, "data").reshape(self.data_shape)
        result = np.conjugate(self.weights) * data_arr
        return _flatten_finite_to_size(result, self.model_size, "adjoint result").reshape(self.model_shape)


class FirstDifferenceRegularization(LinearOperator):
    """Valid-boundary first-difference regularization on a flattened model.

    Forward application computes ``x[i + 1] - x[i]`` and therefore returns
    ``model_size - 1`` samples. The adjoint is the exact transpose/Hermitian
    adjoint of that flattened stencil.
    """

    def __init__(self, model_shape: tuple[int, ...] | int, *, dtype: Any = np.float64) -> None:
        normalized_model_shape = _normalize_shape(model_shape, "model_shape")
        model_size = _shape_size(normalized_model_shape)
        if model_size < 2:
            raise LinearOperatorError("first-difference regularization requires at least 2 samples")
        super().__init__(
            normalized_model_shape,
            (model_size - 1,),
            dtype=dtype,
            metadata={
                "operator_type": "first_difference_regularization",
                "boundary": "valid",
                "stencil": [-1.0, 1.0],
                "flattened": True,
                "model_shape": normalized_model_shape,
            },
        )

    def forward(self, model: np.ndarray) -> np.ndarray:
        model_vec = _flatten_finite_to_size(model, self.model_size, "model")
        result = model_vec[1:] - model_vec[:-1]
        return _flatten_finite_to_size(result, self.data_size, "forward result").reshape(self.data_shape)

    def adjoint(self, data: np.ndarray) -> np.ndarray:
        data_vec = _flatten_finite_to_size(data, self.data_size, "data")
        result = np.zeros(self.model_size, dtype=np.result_type(data_vec.dtype, self.dtype))
        result[:-1] -= data_vec
        result[1:] += data_vec
        return _flatten_finite_to_size(result, self.model_size, "adjoint result").reshape(self.model_shape)


class SecondDifferenceRegularization(LinearOperator):
    """Valid-boundary second-difference regularization on a flattened model.

    Forward application computes ``x[i] - 2*x[i + 1] + x[i + 2]`` and returns
    ``model_size - 2`` samples.
    """

    def __init__(self, model_shape: tuple[int, ...] | int, *, dtype: Any = np.float64) -> None:
        normalized_model_shape = _normalize_shape(model_shape, "model_shape")
        model_size = _shape_size(normalized_model_shape)
        if model_size < 3:
            raise LinearOperatorError("second-difference regularization requires at least 3 samples")
        super().__init__(
            normalized_model_shape,
            (model_size - 2,),
            dtype=dtype,
            metadata={
                "operator_type": "second_difference_regularization",
                "boundary": "valid",
                "stencil": [1.0, -2.0, 1.0],
                "flattened": True,
                "model_shape": normalized_model_shape,
            },
        )

    def forward(self, model: np.ndarray) -> np.ndarray:
        model_vec = _flatten_finite_to_size(model, self.model_size, "model")
        result = model_vec[:-2] - 2.0 * model_vec[1:-1] + model_vec[2:]
        return _flatten_finite_to_size(result, self.data_size, "forward result").reshape(self.data_shape)

    def adjoint(self, data: np.ndarray) -> np.ndarray:
        data_vec = _flatten_finite_to_size(data, self.data_size, "data")
        result = np.zeros(self.model_size, dtype=np.result_type(data_vec.dtype, self.dtype))
        result[:-2] += data_vec
        result[1:-1] -= 2.0 * data_vec
        result[2:] += data_vec
        return _flatten_finite_to_size(result, self.model_size, "adjoint result").reshape(self.model_shape)
