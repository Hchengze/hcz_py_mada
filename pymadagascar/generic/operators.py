"""Small-data linear operators and dot-test helpers.

This module is a Python-first subset for local RSF workflows. It is not the
full Madagascar external-operator pipe framework.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from pymadagascar.io.rsf import read_rsf


PathLike = str | Path


class LinearOperatorError(ValueError):
    """Raised when a linear operator or solver request is invalid."""


@dataclass(frozen=True)
class DotTestResult:
    """Result from a real or complex dot-product adjoint test."""

    lhs: complex | float
    rhs: complex | float
    abs_error: float
    rel_error: float
    passed: bool
    rtol: float
    atol: float

class LinearOperator:
    """Base class for small in-memory linear operators."""

    def __init__(
        self,
        model_shape: tuple[int, ...] | int,
        data_shape: tuple[int, ...] | int,
        *,
        dtype: Any = np.float64,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.model_shape = _normalize_shape(model_shape, "model_shape")
        self.data_shape = _normalize_shape(data_shape, "data_shape")
        self.model_size = _shape_size(self.model_shape)
        self.data_size = _shape_size(self.data_shape)
        self.dtype = np.dtype(dtype)
        self.metadata = dict(metadata or {})

    def forward(self, model: np.ndarray) -> np.ndarray:
        """Apply the forward operator."""

        raise NotImplementedError

    def adjoint(self, data: np.ndarray) -> np.ndarray:
        """Apply the adjoint operator."""

        raise NotImplementedError

    def __mul__(self, scalar: complex | float) -> "ScaledOperator":
        return ScaledOperator(self, scalar)

    def __rmul__(self, scalar: complex | float) -> "ScaledOperator":
        return ScaledOperator(self, scalar)

    def __add__(self, other: "LinearOperator") -> "SumOperator":
        return SumOperator(self, as_linear_operator(other))

    def __matmul__(self, other: "LinearOperator") -> "ComposedOperator":
        return ComposedOperator(self, as_linear_operator(other))

class MatrixOperator(LinearOperator):
    """Linear operator backed by a 2-D dense matrix.

    The matrix shape is ``(data_size, model_size)``. Forward application uses
    ``A @ model`` and adjoint application uses ``A.conj().T @ data``.
    """

    def __init__(
        self,
        matrix: np.ndarray,
        *,
        model_shape: tuple[int, ...] | int | None = None,
        data_shape: tuple[int, ...] | int | None = None,
    ) -> None:
        array = np.asarray(matrix)
        if array.ndim != 2:
            raise LinearOperatorError("MatrixOperator requires a 2-D matrix")
        _check_finite_values(array, "matrix")

        data_size, model_size = array.shape
        model_shape = (model_size,) if model_shape is None else model_shape
        data_shape = (data_size,) if data_shape is None else data_shape

        if _shape_size(_normalize_shape(model_shape, "model_shape")) != model_size:
            raise LinearOperatorError(
                f"model_shape has {_shape_size(_normalize_shape(model_shape, 'model_shape'))} samples, "
                f"but matrix has {model_size} columns"
            )
        if _shape_size(_normalize_shape(data_shape, "data_shape")) != data_size:
            raise LinearOperatorError(
                f"data_shape has {_shape_size(_normalize_shape(data_shape, 'data_shape'))} samples, "
                f"but matrix has {data_size} rows"
            )

        self.matrix = array
        super().__init__(model_shape, data_shape, dtype=array.dtype)

    @classmethod
    def from_rsf(
        cls,
        path: PathLike,
        *,
        model_shape: tuple[int, ...] | int | None = None,
        data_shape: tuple[int, ...] | int | None = None,
    ) -> "MatrixOperator":
        """Read a 2-D RSF matrix and build a matrix-backed operator."""

        return cls(read_rsf(path).data, model_shape=model_shape, data_shape=data_shape)

    def forward(self, model: np.ndarray) -> np.ndarray:
        model_vec = _flatten_finite_to_size(model, self.model_size, "model")
        return np.asarray(self.matrix @ model_vec).reshape(self.data_shape)

    def adjoint(self, data: np.ndarray) -> np.ndarray:
        data_vec = _flatten_finite_to_size(data, self.data_size, "data")
        return np.asarray(self.matrix.conj().T @ data_vec).reshape(self.model_shape)


class IdentityOperator(LinearOperator):
    """Identity operator for toy examples and CLI smoke checks."""

    def __init__(self, shape: tuple[int, ...] | int, *, dtype: Any = np.float64) -> None:
        super().__init__(shape, shape, dtype=dtype)

    def forward(self, model: np.ndarray) -> np.ndarray:
        return _flatten_finite_to_size(model, self.model_size, "model").reshape(self.data_shape)

    def adjoint(self, data: np.ndarray) -> np.ndarray:
        return _flatten_finite_to_size(data, self.data_size, "data").reshape(self.model_shape)


class CallableLinearOperator(LinearOperator):
    """Linear operator backed by Python callables."""

    def __init__(
        self,
        model_shape: tuple[int, ...] | int,
        data_shape: tuple[int, ...] | int,
        forward: Callable[[np.ndarray], np.ndarray],
        adjoint: Callable[[np.ndarray], np.ndarray],
        *,
        dtype: Any = np.float64,
    ) -> None:
        super().__init__(model_shape, data_shape, dtype=dtype)
        self._forward = forward
        self._adjoint = adjoint

    def forward(self, model: np.ndarray) -> np.ndarray:
        model_arr = _flatten_finite_to_size(model, self.model_size, "model").reshape(self.model_shape)
        result = np.asarray(self._forward(model_arr))
        return _flatten_finite_to_size(result, self.data_size, "forward result").reshape(self.data_shape)

    def adjoint(self, data: np.ndarray) -> np.ndarray:
        data_arr = _flatten_finite_to_size(data, self.data_size, "data").reshape(self.data_shape)
        result = np.asarray(self._adjoint(data_arr))
        return _flatten_finite_to_size(result, self.model_size, "adjoint result").reshape(self.model_shape)


class ScaledOperator(LinearOperator):
    """Operator representing ``alpha * A``."""

    def __init__(self, operator: LinearOperator, scalar: complex | float) -> None:
        self.operator = as_linear_operator(operator)
        self.scalar = _finite_scalar(scalar, "scalar")
        super().__init__(
            self.operator.model_shape,
            self.operator.data_shape,
            dtype=np.result_type(self.operator.dtype, self.scalar),
            metadata={
                "operator_type": "scaled",
                "base_model_shape": self.operator.model_shape,
                "base_data_shape": self.operator.data_shape,
            },
        )

    def forward(self, model: np.ndarray) -> np.ndarray:
        _flatten_finite_to_size(model, self.model_size, "model")
        result = self.scalar * self.operator.forward(model)
        return _flatten_finite_to_size(result, self.data_size, "forward result").reshape(self.data_shape)

    def adjoint(self, data: np.ndarray) -> np.ndarray:
        _flatten_finite_to_size(data, self.data_size, "data")
        result = np.conjugate(self.scalar) * self.operator.adjoint(data)
        return _flatten_finite_to_size(result, self.model_size, "adjoint result").reshape(self.model_shape)


class SumOperator(LinearOperator):
    """Operator representing ``A + B`` with matching domain and range."""

    def __init__(self, left: LinearOperator, right: LinearOperator) -> None:
        self.left = as_linear_operator(left)
        self.right = as_linear_operator(right)
        if self.left.model_shape != self.right.model_shape:
            raise LinearOperatorError(
                f"operator sum requires matching model shapes, got {self.left.model_shape} and {self.right.model_shape}"
            )
        if self.left.data_shape != self.right.data_shape:
            raise LinearOperatorError(
                f"operator sum requires matching data shapes, got {self.left.data_shape} and {self.right.data_shape}"
            )
        super().__init__(
            self.left.model_shape,
            self.left.data_shape,
            dtype=np.result_type(self.left.dtype, self.right.dtype),
            metadata={
                "operator_type": "sum",
                "left_model_shape": self.left.model_shape,
                "right_model_shape": self.right.model_shape,
                "data_shape": self.left.data_shape,
            },
        )

    def forward(self, model: np.ndarray) -> np.ndarray:
        _flatten_finite_to_size(model, self.model_size, "model")
        result = self.left.forward(model) + self.right.forward(model)
        return _flatten_finite_to_size(result, self.data_size, "forward result").reshape(self.data_shape)

    def adjoint(self, data: np.ndarray) -> np.ndarray:
        _flatten_finite_to_size(data, self.data_size, "data")
        result = self.left.adjoint(data) + self.right.adjoint(data)
        return _flatten_finite_to_size(result, self.model_size, "adjoint result").reshape(self.model_shape)


class ComposedOperator(LinearOperator):
    """Operator representing ``A @ B``, meaning ``A(Bx)``."""

    def __init__(self, outer: LinearOperator, inner: LinearOperator) -> None:
        self.outer = as_linear_operator(outer)
        self.inner = as_linear_operator(inner)
        if self.inner.data_shape != self.outer.model_shape:
            raise LinearOperatorError(
                "operator composition requires inner data_shape to match outer model_shape, "
                f"got {self.inner.data_shape} and {self.outer.model_shape}"
            )
        super().__init__(
            self.inner.model_shape,
            self.outer.data_shape,
            dtype=np.result_type(self.inner.dtype, self.outer.dtype),
            metadata={
                "operator_type": "composed",
                "inner_model_shape": self.inner.model_shape,
                "inner_data_shape": self.inner.data_shape,
                "outer_model_shape": self.outer.model_shape,
                "outer_data_shape": self.outer.data_shape,
            },
        )

    def forward(self, model: np.ndarray) -> np.ndarray:
        _flatten_finite_to_size(model, self.model_size, "model")
        result = self.outer.forward(self.inner.forward(model))
        return _flatten_finite_to_size(result, self.data_size, "forward result").reshape(self.data_shape)

    def adjoint(self, data: np.ndarray) -> np.ndarray:
        _flatten_finite_to_size(data, self.data_size, "data")
        result = self.inner.adjoint(self.outer.adjoint(data))
        return _flatten_finite_to_size(result, self.model_size, "adjoint result").reshape(self.model_shape)


class StackedOperator(LinearOperator):
    """Vertical stack ``[A; B; ...]`` with a shared domain."""

    def __init__(self, operators: list[LinearOperator] | tuple[LinearOperator, ...]) -> None:
        if not operators:
            raise LinearOperatorError("stacked operator requires at least one operator")
        self.operators = tuple(as_linear_operator(operator) for operator in operators)
        model_shape = self.operators[0].model_shape
        for index, operator in enumerate(self.operators[1:], start=1):
            if operator.model_shape != model_shape:
                raise LinearOperatorError(
                    "stacked operator requires matching model shapes, "
                    f"operator 0 has {model_shape} and operator {index} has {operator.model_shape}"
                )
        self.component_data_shapes = tuple(operator.data_shape for operator in self.operators)
        self.component_data_sizes = tuple(operator.data_size for operator in self.operators)
        super().__init__(
            model_shape,
            (sum(self.component_data_sizes),),
            dtype=np.result_type(*(operator.dtype for operator in self.operators)),
            metadata={
                "operator_type": "stacked",
                "component_count": len(self.operators),
                "component_data_shapes": self.component_data_shapes,
                "model_shape": model_shape,
            },
        )

    def forward(self, model: np.ndarray) -> np.ndarray:
        _flatten_finite_to_size(model, self.model_size, "model")
        parts = [
            _flatten_finite_to_size(operator.forward(model), operator.data_size, "forward component")
            for operator in self.operators
        ]
        return np.concatenate(parts).reshape(self.data_shape)

    def adjoint(self, data: np.ndarray) -> np.ndarray:
        data_vec = _flatten_finite_to_size(data, self.data_size, "data")
        pieces = []
        start = 0
        for operator, size in zip(self.operators, self.component_data_sizes, strict=True):
            stop = start + size
            component = data_vec[start:stop].reshape(operator.data_shape)
            pieces.append(operator.adjoint(component))
            start = stop
        result = np.sum(np.stack(pieces, axis=0), axis=0)
        return _flatten_finite_to_size(result, self.model_size, "adjoint result").reshape(self.model_shape)

def dot_test(
    operator: LinearOperator,
    model_shape: tuple[int, ...] | int | None = None,
    data_shape: tuple[int, ...] | int | None = None,
    *,
    seed: int = 0,
    complex_mode: bool = False,
    rtol: float = 1e-5,
    atol: float = 1e-6,
) -> DotTestResult:
    """Check ``<A x, y> == <x, A* y>`` for a linear operator."""

    _check_optional_shape(model_shape, operator.model_shape, "model_shape")
    _check_optional_shape(data_shape, operator.data_shape, "data_shape")
    _check_tolerances(rtol, atol)

    rng = np.random.default_rng(seed)
    x = _random_array(rng, operator.model_shape, complex_mode=complex_mode)
    y = _random_array(rng, operator.data_shape, complex_mode=complex_mode)

    ax = operator.forward(x)
    aty = operator.adjoint(y)
    lhs = _inner(ax, y, complex_mode=complex_mode)
    rhs = _inner(x, aty, complex_mode=complex_mode)
    abs_error = float(abs(lhs - rhs))
    rel_error = _relative_error(lhs, rhs, abs_error)
    passed = bool(np.allclose(lhs, rhs, rtol=rtol, atol=atol))
    return DotTestResult(lhs, rhs, abs_error, rel_error, passed, rtol, atol)


def complex_dot_test(
    operator: LinearOperator,
    model_shape: tuple[int, ...] | int | None = None,
    data_shape: tuple[int, ...] | int | None = None,
    *,
    seed: int = 0,
    rtol: float = 1e-5,
    atol: float = 1e-6,
) -> DotTestResult:
    """Run a dot test using complex random vectors and Hermitian products."""

    return dot_test(
        operator,
        model_shape=model_shape,
        data_shape=data_shape,
        seed=seed,
        complex_mode=True,
        rtol=rtol,
        atol=atol,
    )

def as_linear_operator(A: LinearOperator | np.ndarray) -> LinearOperator:
    """Return ``A`` as a ``LinearOperator``."""

    if isinstance(A, LinearOperator):
        return A
    return MatrixOperator(np.asarray(A))

def format_dot_test_result(result: DotTestResult) -> str:
    """Format a dot-test result as stable line-oriented text."""

    return "\n".join(
        [
            f"lhs={_format_scalar(result.lhs)}",
            f"rhs={_format_scalar(result.rhs)}",
            f"abs_error={result.abs_error:.9g}",
            f"rel_error={result.rel_error:.9g}",
            f"pass={'true' if result.passed else 'false'}",
        ]
    )

def _normalize_shape(shape: tuple[int, ...] | int, name: str) -> tuple[int, ...]:
    if isinstance(shape, int):
        values = (shape,)
    else:
        values = tuple(int(value) for value in shape)
    if not values or any(value <= 0 for value in values):
        raise LinearOperatorError(f"{name} must contain positive dimensions")
    return values


def _shape_size(shape: tuple[int, ...]) -> int:
    return int(np.prod(shape, dtype=np.int64))


def _flatten_to_size(array: np.ndarray, size: int, name: str) -> np.ndarray:
    result = np.asarray(array).reshape(-1)
    if result.size != size:
        raise LinearOperatorError(f"{name} has {result.size} samples, expected {size}")
    return result


def _flatten_finite_to_size(array: np.ndarray, size: int, name: str) -> np.ndarray:
    result = _flatten_to_size(array, size, name)
    _check_finite_values(result, name)
    return result


def _check_finite_values(array: np.ndarray, name: str) -> None:
    try:
        finite = np.isfinite(array)
    except TypeError as exc:
        raise LinearOperatorError(f"{name} must contain finite numeric values") from exc
    if not np.all(finite):
        raise LinearOperatorError(f"{name} contains non-finite values")


def _finite_scalar(value: complex | float, name: str) -> complex | float:
    array = np.asarray(value)
    if array.shape != ():
        raise LinearOperatorError(f"{name} must be a scalar")
    _check_finite_values(array, name)
    return array.item()


def _finite_float(value: object, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise LinearOperatorError(f"{name} must be finite") from exc
    if not np.isfinite(number):
        raise LinearOperatorError(f"{name} must be finite")
    return number


def _finite_nonnegative_float(value: object, name: str) -> float:
    number = _finite_float(value, name)
    if number < 0.0:
        raise LinearOperatorError(f"{name} must be nonnegative")
    return number


def _finite_optional_float(value: object | None, name: str) -> float | None:
    if value is None:
        return None
    return _finite_float(value, name)


def _finite_optional_nonnegative_float(value: object | None, name: str) -> float | None:
    if value is None:
        return None
    return _finite_nonnegative_float(value, name)


def _json_safe(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return _json_safe(value.tolist())
    if isinstance(value, np.generic):
        return _json_safe(value.item())
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _check_optional_shape(
    value: tuple[int, ...] | int | None,
    expected: tuple[int, ...],
    name: str,
) -> None:
    if value is None:
        return
    normalized = _normalize_shape(value, name)
    if normalized != expected:
        raise LinearOperatorError(f"{name}={normalized} does not match operator shape {expected}")


def _random_array(
    rng: np.random.Generator,
    shape: tuple[int, ...],
    *,
    complex_mode: bool,
) -> np.ndarray:
    real = rng.standard_normal(shape)
    if not complex_mode:
        return real
    return real + 1j * rng.standard_normal(shape)


def _inner(a: np.ndarray, b: np.ndarray, *, complex_mode: bool) -> complex | float:
    left = np.asarray(a).reshape(-1)
    right = np.asarray(b).reshape(-1)
    if left.size != right.size:
        raise LinearOperatorError("inner-product arrays must have the same size")
    if complex_mode:
        return np.vdot(left, right)
    return float(np.dot(left, right))


def _relative_error(lhs: complex | float, rhs: complex | float, abs_error: float) -> float:
    scale = max(float(abs(lhs)), float(abs(rhs)), np.finfo(float).eps)
    return float(abs_error / scale)


def _check_tolerances(rtol: float, atol: float) -> None:
    if rtol < 0 or atol < 0:
        raise LinearOperatorError("rtol and atol must be nonnegative")

def _norm2(vector: np.ndarray) -> float:
    return float(np.real(np.vdot(vector, vector)))

def _format_scalar(value: complex | float) -> str:
    scalar = np.asarray(value).item()
    if isinstance(scalar, complex):
        return f"{scalar.real:.9g}{scalar.imag:+.9g}j"
    return f"{float(scalar):.9g}"
