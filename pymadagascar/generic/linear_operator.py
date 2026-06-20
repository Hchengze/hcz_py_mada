"""Compatibility re-export layer for linear operator foundations.

The implementation lives in focused modules under pymadagascar.generic. This
module remains for existing direct imports such as
pymadagascar.generic.linear_operator.run_cgls.
"""

from __future__ import annotations

from pymadagascar.generic.least_squares import (
    LeastSquaresProblem,
    ObjectiveDiagnostics,
    StoppingDiagnostics,
)
from pymadagascar.generic.operators import (
    CallableLinearOperator,
    ComposedOperator,
    DotTestResult,
    IdentityOperator,
    LinearOperator,
    LinearOperatorError,
    MatrixOperator,
    ScaledOperator,
    StackedOperator,
    SumOperator,
    as_linear_operator,
    complex_dot_test,
    dot_test,
    format_dot_test_result,
)
from pymadagascar.generic.preconditioners import (
    DiagonalPreconditioner,
    IdentityPreconditioner,
    Preconditioner,
    PreconditionerDiagnostics,
    as_preconditioner,
)
from pymadagascar.generic.regularization import (
    DiagonalRegularization,
    FirstDifferenceRegularization,
    SecondDifferenceRegularization,
)
from pymadagascar.generic.solvers import (
    ConjugateGradientResult,
    SolverHistory,
    SolverIterationRecord,
    SolverResult,
    complex_conjgrad_solve,
    complex_conjugate_gradient,
    complex_conjugate_gradient_normal,
    conjugate_gradient,
    conjugate_gradient_normal,
    conjgrad_solve,
    run_cg_with_history,
    run_cgls,
    run_cgls_problem,
    run_cgnr_with_history,
)


__all__ = [
    "CallableLinearOperator",
    "ComposedOperator",
    "ConjugateGradientResult",
    "DiagonalPreconditioner",
    "DiagonalRegularization",
    "DotTestResult",
    "FirstDifferenceRegularization",
    "IdentityOperator",
    "IdentityPreconditioner",
    "LeastSquaresProblem",
    "LinearOperator",
    "LinearOperatorError",
    "MatrixOperator",
    "ObjectiveDiagnostics",
    "Preconditioner",
    "PreconditionerDiagnostics",
    "ScaledOperator",
    "SecondDifferenceRegularization",
    "SolverHistory",
    "SolverIterationRecord",
    "SolverResult",
    "StackedOperator",
    "StoppingDiagnostics",
    "SumOperator",
    "as_linear_operator",
    "as_preconditioner",
    "complex_conjgrad_solve",
    "complex_conjugate_gradient",
    "complex_conjugate_gradient_normal",
    "complex_dot_test",
    "conjugate_gradient",
    "conjugate_gradient_normal",
    "conjgrad_solve",
    "dot_test",
    "format_dot_test_result",
    "run_cg_with_history",
    "run_cgls",
    "run_cgls_problem",
    "run_cgnr_with_history",
]
