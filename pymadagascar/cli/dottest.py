"""Module-only CLI for real matrix-backed dot-product tests."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import MissingParameterError, ParameterParseError, RSFParams
from pymadagascar.generic.linear_operator import (
    IdentityOperator,
    LinearOperatorError,
    MatrixOperator,
    dot_test,
    format_dot_test_result,
)
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """Dottest parameters:
  matrix.rsf              2-D RSF matrix with shape (ndata, nmodel).
  op=identity n=10        Built-in identity operator instead of matrix.rsf.
  seed=0                  Random seed for model/data vectors.
  rtol=1e-5 atol=1e-6     Pass/fail tolerances.
  nmodel=... ndata=...    Optional matrix shape validation.

This is a pure Python matrix-backed subset. It does not execute arbitrary
external operator commands and does not reproduce the full Madagascar pipe
framework used by sfdottest.
"""


def dottest_command(params: RSFParams) -> str:
    try:
        operator = _operator_from_params(params)
        result = dot_test(
            operator,
            seed=params.get_int("seed", 0),
            rtol=params.get_float("rtol", 1e-5),
            atol=params.get_float("atol", 1e-6),
        )
    except (LinearOperatorError, MissingParameterError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return format_dot_test_result(result)


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        dottest_command,
        argv,
        prog="python -m pymadagascar.cli.dottest",
        description="Check a real matrix-backed linear operator with a dot test.",
        help_text=HELP_TEXT,
    )


def _operator_from_params(params: RSFParams) -> MatrixOperator | IdentityOperator:
    op = params.params.get("op", "matrix").lower()
    if op == "identity":
        n = _identity_size(params)
        return IdentityOperator(n)
    if op != "matrix":
        raise ParameterParseError("op must be 'matrix' or 'identity'")

    path = params.input_path(required=True)
    assert path is not None
    operator = MatrixOperator.from_rsf(path)
    if operator.matrix.dtype.kind == "c":
        raise ParameterParseError("dottest supports real matrices; use cdottest for complex matrices")
    _validate_matrix_size(params, operator)
    return operator


def _identity_size(params: RSFParams) -> int:
    value = params.params.get("n") or params.params.get("nmodel")
    if value in {None, ""}:
        raise MissingParameterError("n")
    n = int(value)
    if n <= 0:
        raise ParameterParseError("n must be positive")
    return n


def _validate_matrix_size(params: RSFParams, operator: MatrixOperator) -> None:
    if params.has("nmodel") and params.get_int("nmodel") != operator.model_size:
        raise ParameterParseError(
            f"nmodel={params.get_int('nmodel')} does not match matrix columns {operator.model_size}"
        )
    if params.has("ndata") and params.get_int("ndata") != operator.data_size:
        raise ParameterParseError(
            f"ndata={params.get_int('ndata')} does not match matrix rows {operator.data_size}"
        )


if __name__ == "__main__":
    sys.exit(main())
