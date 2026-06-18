"""Module-only CLI for real small-data conjugate-gradient solves."""

from __future__ import annotations

from collections.abc import Sequence
import sys

import numpy as np

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.generic.linear_operator import LinearOperatorError, MatrixOperator, conjgrad_solve
from pymadagascar.io.rsf import RSFError, read_rsf, write_rsf


HELP_TEXT = """Conjgrad parameters:
  matrix.rsf rhs.rsf      2-D matrix and right-hand-side RSF.
  out=x.rsf               Output solution RSF path.
  mode=normal             normal least-squares mode, or mode=spd.
  niter=10 tol=1e-6       Iteration count and convergence tolerance.
  damp=0.0                Tikhonov damping for normal equations or A+damp^2 I.

This is a small in-memory matrix-backed subset. It does not execute arbitrary
external operators, use preconditioners, or stream large datasets.
"""


def conjgrad_command(params: RSFParams) -> int:
    try:
        matrix_path, rhs_path = _input_paths(params)
        output_path = params.output_path(required=True)
        assert output_path is not None

        operator = MatrixOperator.from_rsf(matrix_path)
        rhs = np.asarray(read_rsf(rhs_path).data)
        if operator.matrix.dtype.kind == "c" or rhs.dtype.kind == "c":
            raise ParameterParseError("conjgrad supports real inputs; use cconjgrad for complex inputs")
        result = conjgrad_solve(
            operator,
            rhs,
            mode=params.get_string("mode", "normal"),
            niter=params.get_int("niter", 10),
            tol=params.get_float("tol", 1e-6),
            damp=params.get_float("damp", 0.0),
        )
        header = {
            "label1": "model",
            "solver": "conjgrad",
            "solver_mode": params.get_string("mode", "normal"),
            "solver_niter": result.iterations,
            "solver_converged": "y" if result.converged else "n",
            "solver_residual_norm": result.residual_norm,
            "solver_tol": params.get_float("tol", 1e-6),
            "solver_damp": params.get_float("damp", 0.0),
        }
        write_rsf(output_path, np.asarray(result.solution), header=header)
    except (LinearOperatorError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        conjgrad_command,
        argv,
        prog="python -m pymadagascar.cli.conjgrad",
        description="Solve a real small-data matrix system with CG.",
        help_text=HELP_TEXT,
    )


def _input_paths(params: RSFParams) -> tuple[str, str]:
    matrix_path = params.input_path(required=True)
    if len(params.positionals) < 2:
        raise ParameterParseError("rhs.rsf is required")
    rhs_path = params.positionals[1]
    assert matrix_path is not None
    return matrix_path, rhs_path


if __name__ == "__main__":
    sys.exit(main())
