"""Small in-memory least-squares problem and diagnostics layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from pymadagascar.generic.operators import (
    LinearOperator,
    LinearOperatorError,
    _finite_nonnegative_float,
    _finite_optional_nonnegative_float,
    _flatten_finite_to_size,
    _json_safe,
    _norm2,
    as_linear_operator,
)


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

        from pymadagascar.generic.solvers import SolverIterationRecord

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
        from pymadagascar.generic.solvers import SolverResult

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
