"""Minimal LSQR learning example for small in-memory least-squares problems."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from pymadagascar.generic.least_squares import LeastSquaresProblem
from pymadagascar.generic.operators import MatrixOperator
from pymadagascar.generic.regularization import FirstDifferenceRegularization
from pymadagascar.generic.solvers import run_lsqr, run_lsqr_problem


def _print_result(label: str, result: object) -> None:
    """Print the compact diagnostics useful for comparing small LSQR runs."""

    final_model = getattr(result, "final_model")
    residual_norm = getattr(result, "residual_norm")
    objective = getattr(result, "objective")
    stopping_reason = getattr(result, "stopping_reason")

    print(f"{label}:")
    print(f"  final_model: {np.array2string(final_model, precision=6)}")
    print(f"  residual_norm: {residual_norm:.6g}")
    print(f"  objective: {objective:.6g}")
    print(f"  stopping_reason: {stopping_reason}")


def main(argv: Sequence[str] | None = None) -> int:
    """Run a tiny deterministic LSQR comparison without writing files."""

    del argv

    matrix = np.array(
        [
            [1.0, 0.0],
            [1.0, 1.0],
            [1.0, 2.0],
            [1.0, 3.0],
        ],
        dtype=float,
    )
    data = np.array([1.0, 2.0, 2.1, 3.9], dtype=float)
    operator = MatrixOperator(matrix)

    lsqr_result = run_lsqr(operator, data, maxiter=8, tol=1e-12)
    dense_model, *_ = np.linalg.lstsq(matrix, data, rcond=None)

    _print_result("unregularized LSQR", lsqr_result)
    print(f"  dense_lstsq: {np.array2string(dense_model, precision=6)}")
    print(
        "  max_abs_difference: "
        f"{np.max(np.abs(lsqr_result.final_model - dense_model)):.3e}"
    )

    problem = LeastSquaresProblem(operator, data)
    problem_result = run_lsqr_problem(problem, maxiter=8, tol=1e-12)
    _print_result("LeastSquaresProblem LSQR", problem_result)

    regularization = FirstDifferenceRegularization(2)
    regularized_problem = LeastSquaresProblem(
        operator,
        data,
        regularization=regularization,
        reg_weight=0.25,
    )
    regularized_result = run_lsqr_problem(
        regularized_problem,
        x0=np.array([0.5, 0.0]),
        maxiter=8,
        tol=1e-12,
    )
    _print_result("regularized LSQR with model-space x0", regularized_result)

    print("preconditioned LSQR is intentionally not enabled in this prototype.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
