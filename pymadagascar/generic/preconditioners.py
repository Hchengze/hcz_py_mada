"""Prototype model-space preconditioner contracts and helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from pymadagascar.generic.operators import (
    LinearOperator,
    LinearOperatorError,
    _check_finite_values,
    _finite_nonnegative_float,
    _finite_optional_nonnegative_float,
    _flatten_finite_to_size,
    _json_safe,
    _normalize_shape,
    _shape_size,
)


@dataclass(frozen=True)
class PreconditionerDiagnostics:
    """Internal/prototype description of a model-space preconditioner.

    A preconditioner changes variables or scaling; unlike regularization, it
    does not add a term to the least-squares objective.
    """

    kind: str
    domain_shape: tuple[int, ...]
    range_shape: tuple[int, ...]
    is_identity: bool = False
    is_diagonal: bool = False
    condition_hint: float | None = None
    scale_range: tuple[float, float] | None = None
    complex_supported: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        kind = str(self.kind)
        if not kind:
            raise LinearOperatorError("preconditioner kind must be non-empty")
        domain_shape = _normalize_shape(self.domain_shape, "domain_shape")
        range_shape = _normalize_shape(self.range_shape, "range_shape")
        condition_hint = _finite_optional_nonnegative_float(
            self.condition_hint,
            "condition_hint",
        )
        scale_range = self.scale_range
        if scale_range is not None:
            if len(scale_range) != 2:
                raise LinearOperatorError("scale_range must contain minimum and maximum")
            minimum = _finite_nonnegative_float(scale_range[0], "scale_range minimum")
            maximum = _finite_nonnegative_float(scale_range[1], "scale_range maximum")
            if minimum > maximum:
                raise LinearOperatorError("scale_range minimum must not exceed maximum")
            scale_range = (minimum, maximum)

        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "domain_shape", domain_shape)
        object.__setattr__(self, "range_shape", range_shape)
        object.__setattr__(self, "is_identity", bool(self.is_identity))
        object.__setattr__(self, "is_diagonal", bool(self.is_diagonal))
        object.__setattr__(self, "condition_hint", condition_hint)
        object.__setattr__(self, "scale_range", scale_range)
        object.__setattr__(self, "complex_supported", bool(self.complex_supported))
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_summary(self) -> dict[str, Any]:
        """Return a deterministic JSON-serializable summary."""

        return {
            "kind": self.kind,
            "domain_shape": list(self.domain_shape),
            "range_shape": list(self.range_shape),
            "is_identity": self.is_identity,
            "is_diagonal": self.is_diagonal,
            "condition_hint": self.condition_hint,
            "scale_range": None if self.scale_range is None else list(self.scale_range),
            "complex_supported": self.complex_supported,
            "metadata": _json_safe(self.metadata),
        }

class Preconditioner(LinearOperator):
    """Semantic base for right/model-space preconditioner transforms.

    A right preconditioner maps latent variables to models via ``x = M z``;
    future solvers can operate on ``A @ M`` and reconstruct ``x`` with
    :meth:`forward`. Forward and Hermitian-adjoint actions are required so the
    transform composes with CGLS/LSQR operator algebra. This contract does not
    implement or modify a solver.
    """

    def __init__(
        self,
        domain_shape: tuple[int, ...] | int,
        range_shape: tuple[int, ...] | int,
        *,
        dtype: Any,
        kind: str,
        is_identity: bool = False,
        is_diagonal: bool = False,
        condition_hint: float | None = None,
        scale_range: tuple[float, float] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self._preconditioner_diagnostics = PreconditionerDiagnostics(
            kind=kind,
            domain_shape=_normalize_shape(domain_shape, "domain_shape"),
            range_shape=_normalize_shape(range_shape, "range_shape"),
            is_identity=is_identity,
            is_diagonal=is_diagonal,
            condition_hint=condition_hint,
            scale_range=scale_range,
            complex_supported=True,
            metadata={
                "side": "right",
                "space": "model",
                "changes_objective": False,
                **dict(metadata or {}),
            },
        )
        super().__init__(
            self._preconditioner_diagnostics.domain_shape,
            self._preconditioner_diagnostics.range_shape,
            dtype=dtype,
            metadata={
                "operator_type": "preconditioner",
                **self._preconditioner_diagnostics.metadata,
            },
        )

    def diagnostics(self) -> PreconditionerDiagnostics:
        """Return immutable contract diagnostics for this transform."""

        return self._preconditioner_diagnostics


class IdentityPreconditioner(Preconditioner):
    """Identity right preconditioner for an unchanged model variable."""

    def __init__(self, model_shape: tuple[int, ...] | int, *, dtype: Any = np.float64) -> None:
        shape = _normalize_shape(model_shape, "model_shape")
        super().__init__(
            shape,
            shape,
            dtype=dtype,
            kind="identity",
            is_identity=True,
            condition_hint=1.0,
            scale_range=(1.0, 1.0),
        )

    def forward(self, model: np.ndarray) -> np.ndarray:
        return _flatten_finite_to_size(model, self.model_size, "latent model").reshape(
            self.data_shape
        )

    def adjoint(self, data: np.ndarray) -> np.ndarray:
        return _flatten_finite_to_size(data, self.data_size, "model data").reshape(
            self.model_shape
        )


class DiagonalPreconditioner(Preconditioner):
    """Invertible diagonal right/model-space scaling transform.

    Zero weights are rejected because this contract represents a reversible
    variable scaling, not a model mask or constraint. Complex weights are
    supported and the adjoint uses their complex conjugates.
    """

    def __init__(
        self,
        weights: np.ndarray,
        *,
        model_shape: tuple[int, ...] | int | None = None,
    ) -> None:
        weight_array = np.asarray(weights)
        if weight_array.size == 0:
            raise LinearOperatorError("preconditioner weights must contain at least one sample")
        _check_finite_values(weight_array, "preconditioner weights")
        if np.any(np.abs(weight_array) == 0.0):
            raise LinearOperatorError("preconditioner weights must be nonzero")
        shape = (
            _normalize_shape(weight_array.shape, "model_shape")
            if model_shape is None
            else _normalize_shape(model_shape, "model_shape")
        )
        expected_size = _shape_size(shape)
        if weight_array.size != expected_size:
            raise LinearOperatorError(
                f"preconditioner weights has {weight_array.size} samples, expected {expected_size}"
            )
        self.weights = weight_array.reshape(shape).copy()
        magnitudes = np.abs(self.weights).reshape(-1)
        minimum = float(np.min(magnitudes))
        maximum = float(np.max(magnitudes))
        super().__init__(
            shape,
            shape,
            dtype=weight_array.dtype,
            kind="diagonal",
            is_diagonal=True,
            condition_hint=maximum / minimum,
            scale_range=(minimum, maximum),
            metadata={"complex_weights": bool(np.iscomplexobj(weight_array))},
        )

    def forward(self, model: np.ndarray) -> np.ndarray:
        latent = _flatten_finite_to_size(model, self.model_size, "latent model").reshape(
            self.model_shape
        )
        return _flatten_finite_to_size(
            self.weights * latent,
            self.data_size,
            "preconditioned model",
        ).reshape(self.data_shape)

    def adjoint(self, data: np.ndarray) -> np.ndarray:
        model = _flatten_finite_to_size(data, self.data_size, "model data").reshape(
            self.data_shape
        )
        return _flatten_finite_to_size(
            np.conjugate(self.weights) * model,
            self.model_size,
            "preconditioner adjoint result",
        ).reshape(self.model_shape)

def as_preconditioner(
    value: Preconditioner | np.ndarray | None,
    *,
    model_shape: tuple[int, ...] | int | None = None,
    dtype: Any = np.float64,
) -> Preconditioner:
    """Normalize an explicit prototype right-preconditioner request.

    ``None`` means identity and requires ``model_shape``. Arrays mean diagonal
    scaling. Arbitrary ``LinearOperator`` instances are intentionally rejected:
    regularization operators must not silently acquire preconditioner semantics.
    """

    expected_shape = None if model_shape is None else _normalize_shape(model_shape, "model_shape")
    if value is None:
        if expected_shape is None:
            raise LinearOperatorError("model_shape is required for an identity preconditioner")
        return IdentityPreconditioner(expected_shape, dtype=dtype)
    if isinstance(value, Preconditioner):
        if expected_shape is not None and value.data_shape != expected_shape:
            raise LinearOperatorError(
                "preconditioner range_shape must match target model_shape, "
                f"got {value.data_shape} and {expected_shape}"
            )
        return value
    if isinstance(value, np.ndarray):
        return DiagonalPreconditioner(value, model_shape=expected_shape)
    if isinstance(value, LinearOperator):
        raise LinearOperatorError(
            "a generic LinearOperator is not implicitly a preconditioner; "
            "use an explicit Preconditioner type"
        )
    raise LinearOperatorError("preconditioner must be None, an array, or a Preconditioner")
