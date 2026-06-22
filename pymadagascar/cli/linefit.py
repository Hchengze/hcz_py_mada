"""CLI for bounded 2D table line fitting."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.generic.array_algebra import ArrayAlgebraError, linefit_rsf
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """Linefit parameters:
  input.rsf               Float coordinate/value table with n1=2.
  out=output.rsf          Output fitted line RSF header path.
  n=100                   Output grid sample count.
  o=0 d=1                 Output grid origin and spacing.

This bounded sflinefit subset fits y=a*x+b by ordinary least squares and
evaluates the fitted line on a regular output grid. It does not implement
multi-trace pattern= files or robust regression.
"""


def linefit_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        linefit_rsf(
            input_path,
            output_path,
            n=params.get_int("n"),
            o=params.get_float("o"),
            d=params.get_float("d"),
        )
    except (ArrayAlgebraError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        linefit_command,
        argv,
        prog="pymada-linefit",
        description="Fit y=a*x+b from an n1=2 RSF table.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
