"""Small in-memory CG, CGNR, and bounded CGLS solver helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from pymadagascar.generic.least_squares import LeastSquaresProblem
from pymadagascar.generic.operators import (
    IdentityOperator,
    LinearOperator,
    LinearOperatorError,
    StackedOperator,
    _check_finite_values,
    _finite_nonnegative_float,
    _finite_optional_float,
    _finite_optional_nonnegative_float,
    _flatten_finite_to_size,
    _flatten_to_size,
    _json_safe,
    _norm2,
    as_linear_operator,
)
from pymadagascar.generic.preconditioners import (
    DiagonalPreconditioner,
    IdentityPreconditioner,
    Preconditioner,
    as_preconditioner,
)


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


def run_cgls(
    A: LinearOperator | np.ndarray,
    b: np.ndarray,
    *,
    x0: np.ndarray | None = None,
    maxiter: int = 10,
    tol: float = 1e-6,
    track_history: bool = True,
    metadata: dict[str, Any] | None = None,
    preconditioner: Preconditioner | np.ndarray | None = None,
) -> SolverResult:
    """Solve a bounded unregularized least-squares problem with CGLS.

    This direct-module prototype minimizes ``0.5 * ||A x - b||**2`` and
    delegates diagnostics/result construction to :class:`LeastSquaresProblem`.
    Convergence uses the normal-residual norm ``||A^H (b - A x)||`` relative
    to its initial value (with a unit floor). Use :func:`run_cgls_problem` for
    existing regularized problems.
    """

    problem = LeastSquaresProblem(A, b)
    return run_cgls_problem(
        problem,
        x0=x0,
        maxiter=maxiter,
        tol=tol,
        track_history=track_history,
        metadata=metadata,
        preconditioner=preconditioner,
    )


def run_cgls_problem(
    problem: LeastSquaresProblem,
    *,
    x0: np.ndarray | None = None,
    maxiter: int = 10,
    tol: float = 1e-6,
    track_history: bool = True,
    metadata: dict[str, Any] | None = None,
    preconditioner: Preconditioner | np.ndarray | None = None,
) -> SolverResult:
    """Solve a small existing :class:`LeastSquaresProblem` with CGLS.

    Active regularization reuses the augmented system ``[A; lambda L]`` and
    ``[b; 0]``. The data residual is ``b - A x``; for regularized problems the
    CGLS recurrence uses the full augmented residual while problem diagnostics
    retain separate data and regularization norms/objective terms.
    """

    if not isinstance(problem, LeastSquaresProblem):
        raise LinearOperatorError("problem must be a LeastSquaresProblem")
    if isinstance(maxiter, (bool, np.bool_)) or int(maxiter) != maxiter or int(maxiter) <= 0:
        raise LinearOperatorError("maxiter must be a positive integer")
    maxiter_value = int(maxiter)
    tol_value = _finite_nonnegative_float(tol, "tol")

    normalized_preconditioner = _normalize_cgls_preconditioner(problem, preconditioner)
    if normalized_preconditioner is None:
        operator, rhs = _augmented_least_squares_system(problem)
    else:
        operator, rhs = _preconditioned_augmented_least_squares_system(
            problem,
            normalized_preconditioner,
        )
    rhs_vec = _flatten_finite_to_size(rhs, operator.data_size, "augmented data")
    if normalized_preconditioner is None:
        if x0 is None:
            start = np.zeros(operator.model_shape, dtype=np.result_type(operator.dtype, rhs_vec.dtype))
        else:
            start = _flatten_finite_to_size(x0, problem.model_size, "x0").reshape(
                problem.model_shape
            )
    else:
        start = _latent_initial_from_model_initial(
            x0,
            problem,
            normalized_preconditioner,
            dtype=np.result_type(operator.dtype, rhs_vec.dtype, normalized_preconditioner.dtype),
        )
    dtype = np.result_type(operator.dtype, rhs_vec.dtype, start.dtype)
    x = np.asarray(start, dtype=dtype).copy()
    residual = rhs_vec.astype(dtype, copy=False) - np.asarray(
        operator.forward(x), dtype=dtype
    ).reshape(-1)
    normal_residual = np.asarray(
        operator.adjoint(residual.reshape(operator.data_shape)), dtype=dtype
    ).reshape(-1)
    search_direction = normal_residual.copy()
    gamma = _norm2(normal_residual)
    initial_gradient_norm = float(np.sqrt(gamma))
    threshold = tol_value * max(initial_gradient_norm, 1.0)

    records: list[SolverIterationRecord] = []

    def model_from_variable(variable: np.ndarray) -> np.ndarray:
        if normalized_preconditioner is None:
            return variable.reshape(problem.model_shape)
        model = normalized_preconditioner.forward(
            variable.reshape(normalized_preconditioner.model_shape)
        )
        return _flatten_finite_to_size(
            model,
            problem.model_size,
            "preconditioned model",
        ).reshape(problem.model_shape)

    preconditioner_metadata = _cgls_preconditioner_metadata(normalized_preconditioner)

    def append_record(iteration: int, step_length: float | None) -> None:
        if not track_history:
            return
        model = model_from_variable(x)
        diagnostics = problem.diagnostics(
            model,
            iteration=iteration,
            include_gradient=True,
        )
        convergence_normal_residual_norm = float(np.sqrt(_norm2(normal_residual)))
        convergence_normal_residual_space = (
            "latent" if normalized_preconditioner is not None else "model"
        )
        records.append(
            SolverIterationRecord(
                iteration=iteration,
                residual_norm=diagnostics.total_residual_norm,
                objective=diagnostics.objective,
                gradient_norm=diagnostics.gradient_norm,
                step_length=step_length,
                metadata={
                    "solver": "cgls",
                    "residual_space": (
                        "augmented_least_squares"
                        if problem.has_regularization
                        else "data"
                    ),
                    "data_residual_convention": "b_minus_Ax",
                    "data_residual_norm": diagnostics.data_residual_norm,
                    "regularization_residual_norm": diagnostics.regularization_residual_norm,
                    "normal_residual_norm": convergence_normal_residual_norm,
                    "normal_residual_space": convergence_normal_residual_space,
                    "convergence_normal_residual_norm": convergence_normal_residual_norm,
                    "convergence_normal_residual_space": convergence_normal_residual_space,
                    "model_gradient_norm": diagnostics.gradient_norm,
                    "convergence_residual_space": "normal_equation",
                    "objective_kind": "least_squares",
                    **preconditioner_metadata,
                },
            )
        )

    append_record(0, None)
    converged = initial_gradient_norm <= threshold
    stopping_reason = "gradient_tolerance" if converged else "max_iterations"
    invalid_state: str | None = None
    completed_iterations = 0

    for iteration in range(1, maxiter_value + 1):
        if converged:
            break
        projected = np.asarray(
            operator.forward(search_direction.reshape(operator.model_shape)), dtype=dtype
        ).reshape(-1)
        curvature = _norm2(projected)
        if curvature <= np.finfo(float).eps:
            invalid_state = "CGLS breakdown: projected search direction has zero norm"
            stopping_reason = "invalid_state"
            break
        alpha = gamma / curvature
        x = x + alpha * search_direction.reshape(operator.model_shape)
        residual = residual - alpha * projected
        next_normal_residual = np.asarray(
            operator.adjoint(residual.reshape(operator.data_shape)), dtype=dtype
        ).reshape(-1)
        next_gamma = _norm2(next_normal_residual)
        normal_residual = next_normal_residual
        completed_iterations = iteration
        append_record(iteration, float(alpha))
        gradient_norm = float(np.sqrt(next_gamma))
        if gradient_norm <= threshold:
            converged = True
            stopping_reason = "gradient_tolerance"
            gamma = next_gamma
            break
        if gamma <= np.finfo(float).eps:
            invalid_state = "CGLS breakdown: normal residual lost positive norm"
            stopping_reason = "invalid_state"
            gamma = next_gamma
            break
        beta = next_gamma / gamma
        search_direction = next_normal_residual + beta * search_direction
        gamma = next_gamma

    final_model = model_from_variable(x)
    final_diagnostics = problem.diagnostics(final_model, include_gradient=True)
    final_normal_residual_norm = float(np.sqrt(_norm2(normal_residual)))
    convergence_normal_residual_space = (
        "latent" if normalized_preconditioner is not None else "model"
    )
    run_metadata = {
        "solver": "cgls",
        "max_iterations": maxiter_value,
        "tolerance": tol_value,
        "tolerance_kind": "relative_initial_normal_residual_with_unit_floor",
        "initial_normal_residual_norm": initial_gradient_norm,
        "normal_residual_norm": (
            final_diagnostics.gradient_norm
            if normalized_preconditioner is None
            else final_normal_residual_norm
        ),
        "normal_residual_space": convergence_normal_residual_space,
        "convergence_normal_residual_norm": final_normal_residual_norm,
        "convergence_normal_residual_space": convergence_normal_residual_space,
        "model_gradient_norm": final_diagnostics.gradient_norm,
        "residual_space": (
            "augmented_least_squares" if problem.has_regularization else "data"
        ),
        "data_residual_convention": "b_minus_Ax",
        "convergence_residual_space": "normal_equation",
        "data_residual_norm": final_diagnostics.data_residual_norm,
        "regularization_residual_norm": final_diagnostics.regularization_residual_norm,
        "regularization_via": _cgls_regularization_metadata(
            problem,
            normalized_preconditioner,
        ),
        "objective_kind": "least_squares",
        "track_history": bool(track_history),
        **preconditioner_metadata,
        **dict(metadata or {}),
    }
    if normalized_preconditioner is not None:
        run_metadata["latent_normal_residual_norm"] = final_normal_residual_norm
    if invalid_state is not None:
        run_metadata["invalid_state"] = invalid_state
    history = (
        SolverHistory(
            tuple(records),
            converged=converged,
            stopping_reason=stopping_reason,
            metadata=run_metadata,
        )
        if track_history
        else None
    )
    return problem.solver_result(
        final_model,
        iterations=completed_iterations,
        converged=converged,
        stopping_reason=stopping_reason,
        history=history,
        include_gradient=True,
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

def _augmented_least_squares_system(
    problem: LeastSquaresProblem,
) -> tuple[LinearOperator, np.ndarray]:
    if not problem.has_regularization or problem.regularization is None:
        return problem.operator, problem.data.copy()
    regularization = problem.reg_weight * problem.regularization
    operator = StackedOperator((problem.operator, regularization))
    zeros = np.zeros(
        problem.regularization.data_size,
        dtype=np.result_type(problem.data.dtype, regularization.dtype),
    )
    rhs = np.concatenate([problem.data.reshape(-1), zeros])
    return operator, rhs.reshape(operator.data_shape)


def _normalize_cgls_preconditioner(
    problem: LeastSquaresProblem,
    preconditioner: Preconditioner | np.ndarray | None,
) -> Preconditioner | None:
    if preconditioner is None:
        return None
    normalized = as_preconditioner(
        preconditioner,
        model_shape=problem.model_shape,
        dtype=problem.operator.dtype,
    )
    if normalized.data_shape != problem.model_shape:
        raise LinearOperatorError(
            "preconditioner range_shape must match problem model_shape, "
            f"got {normalized.data_shape} and {problem.model_shape}"
        )
    return normalized


def _preconditioned_augmented_least_squares_system(
    problem: LeastSquaresProblem,
    preconditioner: Preconditioner,
) -> tuple[LinearOperator, np.ndarray]:
    data_operator = problem.operator @ preconditioner
    if not problem.has_regularization or problem.regularization is None:
        return data_operator, problem.data.copy()
    regularization = problem.reg_weight * (problem.regularization @ preconditioner)
    operator = StackedOperator((data_operator, regularization))
    zeros = np.zeros(
        problem.regularization.data_size,
        dtype=np.result_type(problem.data.dtype, regularization.dtype),
    )
    rhs = np.concatenate([problem.data.reshape(-1), zeros])
    return operator, rhs.reshape(operator.data_shape)


def _latent_initial_from_model_initial(
    x0: np.ndarray | None,
    problem: LeastSquaresProblem,
    preconditioner: Preconditioner,
    *,
    dtype: Any,
) -> np.ndarray:
    if x0 is None:
        return np.zeros(preconditioner.model_shape, dtype=dtype)

    model_start = _flatten_finite_to_size(x0, problem.model_size, "x0").reshape(
        problem.model_shape
    )
    if isinstance(preconditioner, IdentityPreconditioner):
        return _flatten_finite_to_size(
            model_start,
            preconditioner.model_size,
            "latent x0",
        ).reshape(preconditioner.model_shape)
    if isinstance(preconditioner, DiagonalPreconditioner):
        latent = model_start / preconditioner.weights
        return _flatten_finite_to_size(
            latent,
            preconditioner.model_size,
            "latent x0",
        ).reshape(preconditioner.model_shape)
    raise LinearOperatorError(
        "x0 is a model-space initial model; this prototype can only map it to "
        "a latent initial state for identity or diagonal preconditioners"
    )


def _cgls_preconditioner_metadata(
    preconditioner: Preconditioner | None,
) -> dict[str, Any]:
    if preconditioner is None:
        return {}
    diagnostics = preconditioner.diagnostics()
    return {
        "preconditioned": True,
        "right_preconditioning": True,
        "preconditioner_kind": diagnostics.kind,
        "preconditioner_is_identity": diagnostics.is_identity,
        "preconditioner_is_diagonal": diagnostics.is_diagonal,
        "preconditioner_condition_hint": diagnostics.condition_hint,
        "preconditioner_scale_range": diagnostics.scale_range,
        "preconditioner_complex_supported": diagnostics.complex_supported,
        "variable_space": "latent",
        "solution_space": "model",
        "preconditioner_domain_shape": diagnostics.domain_shape,
        "preconditioner_range_shape": diagnostics.range_shape,
    }


def _cgls_regularization_metadata(
    problem: LeastSquaresProblem,
    preconditioner: Preconditioner | None,
) -> str | None:
    if not problem.has_regularization:
        return None
    if preconditioner is None:
        return "StackedOperator[A, lambda*L]"
    return "StackedOperator[A @ M, lambda*L @ M]"
