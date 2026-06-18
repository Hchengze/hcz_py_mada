"""Small-data linear operators, dot tests, and CG solvers.

This module is a Python-first subset for local RSF workflows. It is not the
full Madagascar external-operator pipe framework.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
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


@dataclass(frozen=True)
class ConjugateGradientResult:
    """Conjugate-gradient solution and final convergence metadata."""

    solution: np.ndarray
    residual_norm: float
    iterations: int
    converged: bool


@dataclass(frozen=True)
class SolverIterationRecord:
    """Internal/prototype per-iteration solver diagnostic record."""

    iteration: int
    residual_norm: float
    objective: float | None = None
    gradient_norm: float | None = None
    step_length: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        iteration = int(self.iteration)
        if iteration < 0:
            raise LinearOperatorError("iteration must be nonnegative")
        object.__setattr__(self, "iteration", iteration)
        object.__setattr__(
            self,
            "residual_norm",
            _finite_nonnegative_float(self.residual_norm, "residual_norm"),
        )
        object.__setattr__(self, "objective", _finite_optional_float(self.objective, "objective"))
        object.__setattr__(
            self,
            "gradient_norm",
            _finite_optional_nonnegative_float(self.gradient_norm, "gradient_norm"),
        )
        object.__setattr__(
            self,
            "step_length",
            _finite_optional_nonnegative_float(self.step_length, "step_length"),
        )
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_summary(self) -> dict[str, Any]:
        """Return a deterministic JSON-serializable summary."""

        return {
            "iteration": self.iteration,
            "residual_norm": self.residual_norm,
            "objective": self.objective,
            "gradient_norm": self.gradient_norm,
            "step_length": self.step_length,
            "metadata": _json_safe(self.metadata),
        }


@dataclass(frozen=True)
class SolverHistory:
    """Internal/prototype solver-history contract.

    The I0-4 direct-module helpers can populate this record for the existing
    CG/CGNR iteration core. Existing solver functions keep their original
    return contract and do not expose history by default.
    """

    records: tuple[SolverIterationRecord, ...] = field(default_factory=tuple)
    converged: bool = False
    stopping_reason: str = "not_started"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        records = tuple(self.records)
        iterations = [record.iteration for record in records]
        if iterations != sorted(iterations):
            raise LinearOperatorError("history records must be sorted by iteration")
        reason = str(self.stopping_reason)
        if not reason:
            raise LinearOperatorError("stopping_reason must be non-empty")
        object.__setattr__(self, "records", records)
        object.__setattr__(self, "converged", bool(self.converged))
        object.__setattr__(self, "stopping_reason", reason)
        object.__setattr__(self, "metadata", dict(self.metadata))

    @property
    def final_iteration(self) -> int:
        """Return the last recorded iteration, or zero for an empty history."""

        if not self.records:
            return 0
        return self.records[-1].iteration

    def to_summary(self) -> dict[str, Any]:
        """Return a deterministic JSON-serializable summary."""

        return {
            "records": [record.to_summary() for record in self.records],
            "converged": self.converged,
            "stopping_reason": self.stopping_reason,
            "final_iteration": self.final_iteration,
            "metadata": _json_safe(self.metadata),
        }


@dataclass(frozen=True)
class SolverResult:
    """Internal/prototype solver-result contract.

    This is a diagnostics container, not a new solver implementation and not a
    public inversion-result schema.
    """

    final_model: np.ndarray
    converged: bool
    iterations: int
    residual_norm: float
    objective: float | None = None
    history: SolverHistory | None = None
    stopping_reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        model = np.asarray(self.final_model).copy()
        _check_finite_values(model, "final_model")
        iterations = int(self.iterations)
        if iterations < 0:
            raise LinearOperatorError("iterations must be nonnegative")
        residual_norm = _finite_nonnegative_float(self.residual_norm, "residual_norm")
        objective = _finite_optional_float(self.objective, "objective")
        history = self.history
        reason = self.stopping_reason
        if reason is None:
            reason = history.stopping_reason if history is not None else "converged" if self.converged else "not_converged"
        reason = str(reason)
        if not reason:
            raise LinearOperatorError("stopping_reason must be non-empty")

        object.__setattr__(self, "final_model", model)
        object.__setattr__(self, "converged", bool(self.converged))
        object.__setattr__(self, "iterations", iterations)
        object.__setattr__(self, "residual_norm", residual_norm)
        object.__setattr__(self, "objective", objective)
        object.__setattr__(self, "history", history)
        object.__setattr__(self, "stopping_reason", reason)
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_summary(self) -> dict[str, Any]:
        """Return a deterministic JSON-serializable summary."""

        return {
            "final_model": _json_safe(self.final_model),
            "final_model_shape": list(self.final_model.shape),
            "final_model_dtype": str(self.final_model.dtype),
            "converged": self.converged,
            "iterations": self.iterations,
            "residual_norm": self.residual_norm,
            "objective": self.objective,
            "stopping_reason": self.stopping_reason,
            "history": None if self.history is None else self.history.to_summary(),
            "metadata": _json_safe(self.metadata),
        }


@dataclass(frozen=True)
class ObjectiveDiagnostics:
    """Internal/prototype least-squares objective diagnostic record."""

    objective: float
    data_objective: float
    regularization_objective: float
    data_residual_norm: float
    regularization_residual_norm: float
    total_residual_norm: float
    iteration: int = 0
    gradient_norm: float | None = None
    converged: bool = False
    stopping_reason: str = "not_converged"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        iteration = int(self.iteration)
        if iteration < 0:
            raise LinearOperatorError("iteration must be nonnegative")
        reason = str(self.stopping_reason)
        if not reason:
            raise LinearOperatorError("stopping_reason must be non-empty")

        object.__setattr__(self, "iteration", iteration)
        object.__setattr__(self, "objective", _finite_nonnegative_float(self.objective, "objective"))
        object.__setattr__(
            self,
            "data_objective",
            _finite_nonnegative_float(self.data_objective, "data_objective"),
        )
        object.__setattr__(
            self,
            "regularization_objective",
            _finite_nonnegative_float(self.regularization_objective, "regularization_objective"),
        )
        object.__setattr__(
            self,
            "data_residual_norm",
            _finite_nonnegative_float(self.data_residual_norm, "data_residual_norm"),
        )
        object.__setattr__(
            self,
            "regularization_residual_norm",
            _finite_nonnegative_float(self.regularization_residual_norm, "regularization_residual_norm"),
        )
        object.__setattr__(
            self,
            "total_residual_norm",
            _finite_nonnegative_float(self.total_residual_norm, "total_residual_norm"),
        )
        object.__setattr__(
            self,
            "gradient_norm",
            _finite_optional_nonnegative_float(self.gradient_norm, "gradient_norm"),
        )
        object.__setattr__(self, "converged", bool(self.converged))
        object.__setattr__(self, "stopping_reason", reason)
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_iteration_record(self) -> SolverIterationRecord:
        """Return the matching internal solver-history iteration record."""

        return SolverIterationRecord(
            self.iteration,
            residual_norm=self.total_residual_norm,
            objective=self.objective,
            gradient_norm=self.gradient_norm,
            metadata=self.metadata,
        )

    def to_summary(self) -> dict[str, Any]:
        """Return a deterministic JSON-serializable summary."""

        return {
            "iteration": self.iteration,
            "objective": self.objective,
            "data_objective": self.data_objective,
            "regularization_objective": self.regularization_objective,
            "data_residual_norm": self.data_residual_norm,
            "regularization_residual_norm": self.regularization_residual_norm,
            "total_residual_norm": self.total_residual_norm,
            "gradient_norm": self.gradient_norm,
            "converged": self.converged,
            "stopping_reason": self.stopping_reason,
            "metadata": _json_safe(self.metadata),
        }


@dataclass(frozen=True)
class StoppingDiagnostics:
    """Internal/prototype stopping-state diagnostic record."""

    iteration: int
    converged: bool
    stopping_reason: str
    residual_norm: float | None = None
    objective: float | None = None
    gradient_norm: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        iteration = int(self.iteration)
        if iteration < 0:
            raise LinearOperatorError("iteration must be nonnegative")
        reason = str(self.stopping_reason)
        if not reason:
            raise LinearOperatorError("stopping_reason must be non-empty")

        object.__setattr__(self, "iteration", iteration)
        object.__setattr__(self, "converged", bool(self.converged))
        object.__setattr__(self, "stopping_reason", reason)
        object.__setattr__(
            self,
            "residual_norm",
            _finite_optional_nonnegative_float(self.residual_norm, "residual_norm"),
        )
        object.__setattr__(self, "objective", _finite_optional_nonnegative_float(self.objective, "objective"))
        object.__setattr__(
            self,
            "gradient_norm",
            _finite_optional_nonnegative_float(self.gradient_norm, "gradient_norm"),
        )
        object.__setattr__(self, "metadata", dict(self.metadata))

    @classmethod
    def from_thresholds(
        cls,
        *,
        iteration: int,
        residual_norm: float | None = None,
        objective: float | None = None,
        gradient_norm: float | None = None,
        max_iterations: int | None = None,
        residual_tolerance: float | None = None,
        objective_tolerance: float | None = None,
        gradient_tolerance: float | None = None,
        invalid_state: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> "StoppingDiagnostics":
        """Classify a small solver state without running or modifying a solver."""

        iteration_value = int(iteration)
        if iteration_value < 0:
            raise LinearOperatorError("iteration must be nonnegative")
        residual_value = _finite_optional_nonnegative_float(residual_norm, "residual_norm")
        objective_value = _finite_optional_nonnegative_float(objective, "objective")
        gradient_value = _finite_optional_nonnegative_float(gradient_norm, "gradient_norm")
        maxiter_value = None if max_iterations is None else int(max_iterations)
        if maxiter_value is not None and maxiter_value < 0:
            raise LinearOperatorError("max_iterations must be nonnegative")
        residual_tol = _finite_optional_nonnegative_float(residual_tolerance, "residual_tolerance")
        objective_tol = _finite_optional_nonnegative_float(objective_tolerance, "objective_tolerance")
        gradient_tol = _finite_optional_nonnegative_float(gradient_tolerance, "gradient_tolerance")

        converged = False
        reason = "not_converged"
        if invalid_state:
            reason = "invalid_state"
        elif residual_tol is not None and residual_value is not None and residual_value <= residual_tol:
            converged = True
            reason = "residual_tolerance"
        elif objective_tol is not None and objective_value is not None and objective_value <= objective_tol:
            converged = True
            reason = "objective_tolerance"
        elif gradient_tol is not None and gradient_value is not None and gradient_value <= gradient_tol:
            converged = True
            reason = "gradient_tolerance"
        elif maxiter_value is not None and iteration_value >= maxiter_value:
            reason = "max_iterations"

        return cls(
            iteration=iteration_value,
            converged=converged,
            stopping_reason=reason,
            residual_norm=residual_value,
            objective=objective_value,
            gradient_norm=gradient_value,
            metadata=dict(metadata or {}),
        )

    def to_summary(self) -> dict[str, Any]:
        """Return a deterministic JSON-serializable summary."""

        return {
            "iteration": self.iteration,
            "converged": self.converged,
            "stopping_reason": self.stopping_reason,
            "residual_norm": self.residual_norm,
            "objective": self.objective,
            "gradient_norm": self.gradient_norm,
            "metadata": _json_safe(self.metadata),
        }


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


class LeastSquaresProblem:
    """Small in-memory least-squares residual/objective diagnostics layer.

    This class evaluates ``0.5 ||A x - b||^2 + 0.5 ||lambda L x||^2`` and its
    normal-equation gradient. It is not a solver and is not a production
    inversion framework.
    """

    def __init__(
        self,
        operator: LinearOperator | np.ndarray,
        data: np.ndarray,
        *,
        regularization: LinearOperator | np.ndarray | None = None,
        reg_weight: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.operator = as_linear_operator(operator)
        self.data = _flatten_finite_to_size(data, self.operator.data_size, "data").reshape(
            self.operator.data_shape
        ).copy()
        self.regularization = None if regularization is None else as_linear_operator(regularization)
        if self.regularization is not None and self.regularization.model_shape != self.operator.model_shape:
            raise LinearOperatorError(
                "regularization model_shape must match operator model_shape, "
                f"got {self.regularization.model_shape} and {self.operator.model_shape}"
            )
        self.reg_weight = _finite_nonnegative_float(reg_weight, "reg_weight")
        self.metadata = dict(metadata or {})
        self.model_shape = self.operator.model_shape
        self.data_shape = self.operator.data_shape
        self.model_size = self.operator.model_size
        self.data_size = self.operator.data_size

    @property
    def has_regularization(self) -> bool:
        """Return whether regularization contributes to the objective."""

        return self.regularization is not None and self.reg_weight > 0.0

    @property
    def regularization_shape(self) -> tuple[int, ...] | None:
        """Return the active regularization residual shape, if present."""

        if not self.has_regularization:
            return None
        return self.regularization.data_shape if self.regularization is not None else None

    def data_residual(self, model: np.ndarray) -> np.ndarray:
        """Return ``A x - b`` in the data space."""

        _flatten_finite_to_size(model, self.model_size, "model")
        predicted = self.operator.forward(model)
        result = predicted - self.data
        return _flatten_finite_to_size(result, self.data_size, "data residual").reshape(self.data_shape)

    def regularization_residual(self, model: np.ndarray) -> np.ndarray:
        """Return ``lambda L x`` or an empty vector when inactive."""

        _flatten_finite_to_size(model, self.model_size, "model")
        if not self.has_regularization or self.regularization is None:
            return np.zeros((0,), dtype=np.result_type(self.operator.dtype, self.data.dtype, float))
        result = self.reg_weight * self.regularization.forward(model)
        return _flatten_finite_to_size(
            result,
            self.regularization.data_size,
            "regularization residual",
        ).reshape(self.regularization.data_shape)

    def total_residual(self, model: np.ndarray) -> np.ndarray:
        """Return ``concat(A x - b, lambda L x)`` as a flat vector."""

        data_residual = self.data_residual(model).reshape(-1)
        regularization_residual = self.regularization_residual(model).reshape(-1)
        if regularization_residual.size == 0:
            return data_residual.copy()
        return np.concatenate([data_residual, regularization_residual])

    def objective_terms(self, model: np.ndarray) -> tuple[float, float, float]:
        """Return ``(total, data, regularization)`` objective values."""

        data_residual = self.data_residual(model)
        regularization_residual = self.regularization_residual(model)
        data_objective = 0.5 * _norm2(data_residual)
        regularization_objective = 0.5 * _norm2(regularization_residual)
        total = data_objective + regularization_objective
        return (
            _finite_nonnegative_float(total, "objective"),
            _finite_nonnegative_float(data_objective, "data_objective"),
            _finite_nonnegative_float(regularization_objective, "regularization_objective"),
        )

    def objective(self, model: np.ndarray) -> float:
        """Return the total least-squares objective value."""

        total, _, _ = self.objective_terms(model)
        return total

    def gradient(self, model: np.ndarray) -> np.ndarray:
        """Return the normal-equation gradient at ``model``."""

        _flatten_finite_to_size(model, self.model_size, "model")
        data_gradient = self.operator.adjoint(self.data_residual(model))
        result = np.asarray(data_gradient)
        if self.has_regularization and self.regularization is not None:
            regularization_residual = self.regularization_residual(model)
            result = result + self.reg_weight * self.regularization.adjoint(regularization_residual)
        return _flatten_finite_to_size(result, self.model_size, "gradient").reshape(self.model_shape)

    def diagnostics(
        self,
        model: np.ndarray,
        *,
        iteration: int = 0,
        converged: bool = False,
        stopping_reason: str = "not_converged",
        include_gradient: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> ObjectiveDiagnostics:
        """Evaluate residual, objective, and optional gradient diagnostics."""

        total, data_objective, regularization_objective = self.objective_terms(model)
        data_residual = self.data_residual(model)
        regularization_residual = self.regularization_residual(model)
        total_residual = self.total_residual(model)
        gradient_norm = None
        if include_gradient:
            gradient_norm = float(np.sqrt(_norm2(self.gradient(model))))

        diagnostic_metadata = {
            "model_shape": self.model_shape,
            "data_shape": self.data_shape,
            "regularization_shape": self.regularization_shape,
            "has_regularization": self.has_regularization,
            "reg_weight": self.reg_weight,
            **self.metadata,
            **dict(metadata or {}),
        }
        return ObjectiveDiagnostics(
            objective=total,
            data_objective=data_objective,
            regularization_objective=regularization_objective,
            data_residual_norm=float(np.sqrt(_norm2(data_residual))),
            regularization_residual_norm=float(np.sqrt(_norm2(regularization_residual))),
            total_residual_norm=float(np.sqrt(_norm2(total_residual))),
            iteration=iteration,
            gradient_norm=gradient_norm,
            converged=converged,
            stopping_reason=stopping_reason,
            metadata=diagnostic_metadata,
        )

    def iteration_record(
        self,
        model: np.ndarray,
        *,
        iteration: int,
        include_gradient: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> SolverIterationRecord:
        """Return a solver-history-compatible iteration record."""

        return self.diagnostics(
            model,
            iteration=iteration,
            include_gradient=include_gradient,
            metadata=metadata,
        ).to_iteration_record()

    def solver_result(
        self,
        model: np.ndarray,
        *,
        iterations: int,
        converged: bool,
        stopping_reason: str,
        history: SolverHistory | None = None,
        include_gradient: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> SolverResult:
        """Return a solver-result-compatible diagnostics container."""

        diagnostics = self.diagnostics(
            model,
            iteration=iterations,
            converged=converged,
            stopping_reason=stopping_reason,
            include_gradient=include_gradient,
            metadata=metadata,
        )
        return SolverResult(
            final_model=np.asarray(model).reshape(self.model_shape),
            converged=converged,
            iterations=iterations,
            residual_norm=diagnostics.total_residual_norm,
            objective=diagnostics.objective,
            history=history,
            stopping_reason=stopping_reason,
            metadata=diagnostics.metadata,
        )

    def to_summary(self, model: np.ndarray, **diagnostics_kwargs: Any) -> dict[str, Any]:
        """Return a deterministic JSON-serializable diagnostics summary."""

        return self.diagnostics(model, **diagnostics_kwargs).to_summary()


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


def conjugate_gradient(
    A: LinearOperator | np.ndarray,
    b: np.ndarray,
    *,
    x0: np.ndarray | None = None,
    niter: int = 10,
    tol: float = 1e-6,
    damp: float = 0.0,
) -> ConjugateGradientResult:
    """Solve a small SPD/Hermitian system with conjugate gradients."""

    operator = as_linear_operator(A)
    if operator.model_size != operator.data_size:
        raise LinearOperatorError("conjugate_gradient requires a square operator")
    _check_solver_options(niter, tol, damp)

    rhs = _flatten_to_size(b, operator.data_size, "b")
    start = None if x0 is None else _flatten_to_size(x0, operator.model_size, "x0")
    damp2 = float(damp) ** 2

    def matvec(x: np.ndarray) -> np.ndarray:
        result = operator.forward(x.reshape(operator.model_shape)).reshape(-1)
        if damp2:
            result = result + damp2 * x
        return result

    result = _cg_solve(matvec, rhs, x0=start, niter=niter, tol=tol)
    return ConjugateGradientResult(
        result.solution.reshape(operator.model_shape),
        result.residual_norm,
        result.iterations,
        result.converged,
    )


def conjugate_gradient_normal(
    A: LinearOperator | np.ndarray,
    b: np.ndarray,
    *,
    x0: np.ndarray | None = None,
    niter: int = 10,
    tol: float = 1e-6,
    damp: float = 0.0,
) -> ConjugateGradientResult:
    """Solve ``min ||A x - b||^2 + damp^2 ||x||^2`` with CGNR."""

    operator = as_linear_operator(A)
    _check_solver_options(niter, tol, damp)

    data = _flatten_to_size(b, operator.data_size, "b")
    rhs = operator.adjoint(data.reshape(operator.data_shape)).reshape(-1)
    start = None if x0 is None else _flatten_to_size(x0, operator.model_size, "x0")
    damp2 = float(damp) ** 2

    def normal_matvec(x: np.ndarray) -> np.ndarray:
        model = x.reshape(operator.model_shape)
        result = operator.adjoint(operator.forward(model)).reshape(-1)
        if damp2:
            result = result + damp2 * x
        return result

    result = _cg_solve(normal_matvec, rhs, x0=start, niter=niter, tol=tol)
    return ConjugateGradientResult(
        result.solution.reshape(operator.model_shape),
        result.residual_norm,
        result.iterations,
        result.converged,
    )


def run_cg_with_history(
    A: LinearOperator | np.ndarray,
    b: np.ndarray,
    *,
    x0: np.ndarray | None = None,
    niter: int = 10,
    tol: float = 1e-6,
    damp: float = 0.0,
    metadata: dict[str, Any] | None = None,
) -> SolverResult:
    """Run the existing CG core and return prototype iteration diagnostics.

    This helper is intentionally separate from :func:`conjugate_gradient` so
    the established default return contract and CLI behavior remain unchanged.
    The recorded objective is residual energy, ``0.5 * ||r||**2``.
    """

    operator = as_linear_operator(A)
    if operator.model_size != operator.data_size:
        raise LinearOperatorError("run_cg_with_history requires a square operator")
    niter_value, tol_value, damp_value = _finite_solver_options(niter, tol, damp)

    rhs = _flatten_finite_to_size(b, operator.data_size, "b")
    start = None if x0 is None else _flatten_finite_to_size(x0, operator.model_size, "x0")
    damp2 = damp_value**2

    def matvec(x: np.ndarray) -> np.ndarray:
        result = operator.forward(x.reshape(operator.model_shape)).reshape(-1)
        if damp2:
            result = result + damp2 * x
        return result

    def record_factory(
        iteration: int,
        _model: np.ndarray,
        residual_norm: float,
        step_length: float | None,
    ) -> SolverIterationRecord:
        return SolverIterationRecord(
            iteration=iteration,
            residual_norm=residual_norm,
            objective=0.5 * residual_norm**2,
            gradient_norm=residual_norm,
            step_length=step_length,
            metadata={
                "solver": "cg",
                "residual_space": "linear_system",
                "objective_kind": "residual_energy",
            },
        )

    run = _cg_run(
        matvec,
        rhs,
        x0=start,
        niter=niter_value,
        tol=tol_value,
        record_factory=record_factory,
        capture_invalid_state=True,
    )
    run_metadata = {
        "solver": "cg",
        "max_iterations": niter_value,
        "tolerance": tol_value,
        "damp": damp_value,
        "residual_space": "linear_system",
        "objective_kind": "residual_energy",
        **dict(metadata or {}),
    }
    if run.invalid_state is not None:
        run_metadata["invalid_state"] = run.invalid_state
    history = SolverHistory(
        run.records,
        converged=run.result.converged,
        stopping_reason=run.stopping_reason,
        metadata=run_metadata,
    )
    return SolverResult(
        final_model=run.result.solution.reshape(operator.model_shape),
        converged=run.result.converged,
        iterations=run.result.iterations,
        residual_norm=run.result.residual_norm,
        objective=0.5 * run.result.residual_norm**2,
        history=history,
        stopping_reason=run.stopping_reason,
        metadata=run_metadata,
    )


def run_cgnr_with_history(
    A: LinearOperator | np.ndarray,
    b: np.ndarray,
    *,
    x0: np.ndarray | None = None,
    niter: int = 10,
    tol: float = 1e-6,
    damp: float = 0.0,
    metadata: dict[str, Any] | None = None,
) -> SolverResult:
    """Run the existing CGNR core with I0-3 least-squares diagnostics.

    Convergence is still determined by the normal-equation residual used by
    the existing CGNR implementation. History ``residual_norm`` values instead
    report the augmented least-squares residual from ``LeastSquaresProblem``;
    each record also carries the normal-equation residual explicitly.
    """

    operator = as_linear_operator(A)
    niter_value, tol_value, damp_value = _finite_solver_options(niter, tol, damp)

    data = _flatten_finite_to_size(b, operator.data_size, "b")
    rhs = operator.adjoint(data.reshape(operator.data_shape)).reshape(-1)
    start = None if x0 is None else _flatten_finite_to_size(x0, operator.model_size, "x0")
    damp2 = damp_value**2
    regularization = (
        IdentityOperator(operator.model_shape, dtype=operator.dtype)
        if damp_value > 0.0
        else None
    )
    problem = LeastSquaresProblem(
        operator,
        data.reshape(operator.data_shape),
        regularization=regularization,
        reg_weight=damp_value,
    )

    def normal_matvec(x: np.ndarray) -> np.ndarray:
        model = x.reshape(operator.model_shape)
        result = operator.adjoint(operator.forward(model)).reshape(-1)
        if damp2:
            result = result + damp2 * x
        return result

    def record_factory(
        iteration: int,
        model: np.ndarray,
        normal_residual_norm: float,
        step_length: float | None,
    ) -> SolverIterationRecord:
        diagnostics = problem.diagnostics(
            model.reshape(operator.model_shape),
            iteration=iteration,
            include_gradient=True,
        )
        return SolverIterationRecord(
            iteration=iteration,
            residual_norm=diagnostics.total_residual_norm,
            objective=diagnostics.objective,
            gradient_norm=diagnostics.gradient_norm,
            step_length=step_length,
            metadata={
                "solver": "cgnr",
                "residual_space": "augmented_least_squares",
                "data_residual_norm": diagnostics.data_residual_norm,
                "regularization_residual_norm": diagnostics.regularization_residual_norm,
                "normal_equation_residual_norm": normal_residual_norm,
                "convergence_residual_space": "normal_equation",
                "objective_kind": "least_squares",
            },
        )

    run = _cg_run(
        normal_matvec,
        rhs,
        x0=start,
        niter=niter_value,
        tol=tol_value,
        record_factory=record_factory,
        capture_invalid_state=True,
    )
    final_model = run.result.solution.reshape(operator.model_shape)
    final_diagnostics = problem.diagnostics(final_model, include_gradient=True)
    run_metadata = {
        "solver": "cgnr",
        "max_iterations": niter_value,
        "tolerance": tol_value,
        "damp": damp_value,
        "residual_space": "augmented_least_squares",
        "convergence_residual_space": "normal_equation",
        "normal_equation_residual_norm": run.result.residual_norm,
        "data_residual_norm": final_diagnostics.data_residual_norm,
        "regularization_residual_norm": final_diagnostics.regularization_residual_norm,
        "objective_kind": "least_squares",
        **dict(metadata or {}),
    }
    if run.invalid_state is not None:
        run_metadata["invalid_state"] = run.invalid_state
    history = SolverHistory(
        run.records,
        converged=run.result.converged,
        stopping_reason=run.stopping_reason,
        metadata=run_metadata,
    )
    return SolverResult(
        final_model=final_model,
        converged=run.result.converged,
        iterations=run.result.iterations,
        residual_norm=final_diagnostics.total_residual_norm,
        objective=final_diagnostics.objective,
        history=history,
        stopping_reason=run.stopping_reason,
        metadata=run_metadata,
    )


def conjgrad_solve(
    A: LinearOperator | np.ndarray,
    b: np.ndarray,
    *,
    x0: np.ndarray | None = None,
    niter: int = 10,
    tol: float = 1e-6,
    damp: float = 0.0,
    mode: str = "normal",
) -> ConjugateGradientResult:
    """Dispatch to the small-data CG subset by mode."""

    normalized = mode.lower()
    if normalized == "normal":
        return conjugate_gradient_normal(A, b, x0=x0, niter=niter, tol=tol, damp=damp)
    if normalized in {"spd", "hermitian"}:
        return conjugate_gradient(A, b, x0=x0, niter=niter, tol=tol, damp=damp)
    raise LinearOperatorError("mode must be 'normal', 'spd', or 'hermitian'")


def complex_conjugate_gradient(
    A: LinearOperator | np.ndarray,
    b: np.ndarray,
    *,
    x0: np.ndarray | None = None,
    niter: int = 10,
    tol: float = 1e-6,
    damp: float = 0.0,
) -> ConjugateGradientResult:
    """Solve a small complex Hermitian system with conjugate gradients."""

    return conjugate_gradient(A, b, x0=x0, niter=niter, tol=tol, damp=damp)


def complex_conjugate_gradient_normal(
    A: LinearOperator | np.ndarray,
    b: np.ndarray,
    *,
    x0: np.ndarray | None = None,
    niter: int = 10,
    tol: float = 1e-6,
    damp: float = 0.0,
) -> ConjugateGradientResult:
    """Solve a small complex least-squares normal equation."""

    return conjugate_gradient_normal(A, b, x0=x0, niter=niter, tol=tol, damp=damp)


def complex_conjgrad_solve(
    A: LinearOperator | np.ndarray,
    b: np.ndarray,
    *,
    x0: np.ndarray | None = None,
    niter: int = 10,
    tol: float = 1e-6,
    damp: float = 0.0,
    mode: str = "normal",
) -> ConjugateGradientResult:
    """Dispatch to the complex CG subset by mode."""

    return conjgrad_solve(A, b, x0=x0, niter=niter, tol=tol, damp=damp, mode=mode)


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


@dataclass(frozen=True)
class _CGRun:
    result: ConjugateGradientResult
    records: tuple[SolverIterationRecord, ...]
    stopping_reason: str
    invalid_state: str | None = None


def _cg_solve(
    matvec: Callable[[np.ndarray], np.ndarray],
    b: np.ndarray,
    *,
    x0: np.ndarray | None,
    niter: int,
    tol: float,
) -> ConjugateGradientResult:
    return _cg_run(
        matvec,
        b,
        x0=x0,
        niter=niter,
        tol=tol,
        record_factory=None,
        capture_invalid_state=False,
    ).result


def _cg_run(
    matvec: Callable[[np.ndarray], np.ndarray],
    b: np.ndarray,
    *,
    x0: np.ndarray | None,
    niter: int,
    tol: float,
    record_factory: Callable[
        [int, np.ndarray, float, float | None], SolverIterationRecord
    ]
    | None,
    capture_invalid_state: bool,
) -> _CGRun:
    rhs = np.asarray(b)
    dtype = np.result_type(rhs.dtype, np.asarray(matvec(np.zeros_like(rhs))).dtype)
    x = np.zeros(rhs.shape, dtype=dtype) if x0 is None else np.asarray(x0, dtype=dtype).copy()
    r = rhs.astype(dtype, copy=False) - np.asarray(matvec(x), dtype=dtype)
    p = r.copy()
    rsold = _norm2(r)
    rhs_norm = float(np.sqrt(_norm2(rhs)))
    threshold = float(tol) * max(rhs_norm, 1.0)
    residual_norm = float(np.sqrt(rsold))
    records: list[SolverIterationRecord] = []
    if record_factory is not None:
        records.append(record_factory(0, x.copy(), residual_norm, None))
    if residual_norm <= threshold:
        return _CGRun(
            ConjugateGradientResult(x, residual_norm, 0, True),
            tuple(records),
            "residual_tolerance",
        )

    converged = False
    completed_iterations = 0
    for iteration in range(1, int(niter) + 1):
        ap = np.asarray(matvec(p), dtype=dtype)
        denom = np.vdot(p, ap)
        if abs(denom) <= np.finfo(float).eps:
            message = "CG breakdown: search direction has zero curvature"
            if not capture_invalid_state:
                raise LinearOperatorError(message)
            return _CGRun(
                ConjugateGradientResult(x, residual_norm, completed_iterations, False),
                tuple(records),
                "invalid_state",
                message,
            )
        alpha = rsold / denom
        x = x + alpha * p
        r = r - alpha * ap
        rsnew = _norm2(r)
        residual_norm = float(np.sqrt(rsnew))
        completed_iterations = iteration
        if record_factory is not None:
            records.append(
                record_factory(iteration, x.copy(), residual_norm, float(abs(alpha)))
            )
        if residual_norm <= threshold:
            converged = True
            break
        beta = rsnew / rsold
        p = r + beta * p
        rsold = rsnew

    reason = "residual_tolerance" if converged else "max_iterations"
    return _CGRun(
        ConjugateGradientResult(x, residual_norm, completed_iterations, converged),
        tuple(records),
        reason,
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


def _check_solver_options(niter: int, tol: float, damp: float) -> None:
    if int(niter) < 0:
        raise LinearOperatorError("niter must be nonnegative")
    if tol < 0:
        raise LinearOperatorError("tol must be nonnegative")
    if damp < 0:
        raise LinearOperatorError("damp must be nonnegative")


def _finite_solver_options(niter: int, tol: float, damp: float) -> tuple[int, float, float]:
    _check_solver_options(niter, tol, damp)
    return (
        int(niter),
        _finite_nonnegative_float(tol, "tol"),
        _finite_nonnegative_float(damp, "damp"),
    )


def _norm2(vector: np.ndarray) -> float:
    return float(np.real(np.vdot(vector, vector)))


def _format_scalar(value: complex | float) -> str:
    scalar = np.asarray(value).item()
    if isinstance(scalar, complex):
        return f"{scalar.real:.9g}{scalar.imag:+.9g}j"
    return f"{float(scalar):.9g}"
