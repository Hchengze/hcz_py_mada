"""CLI for half-order trace integration and differentiation."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.seismic.halfint import HalfIntError, halfint_rsf


HELP_TEXT = """HalfInt parameters:
  input.rsf               Input RSF traces.
  out=output.rsf          Output RSF header path.
  axis=1                  1-based RSF axis for the half-order transform.
  inv=n                   If yes, do half-order differentiation instead of integration.
  adj=n                   If yes, use the adjoint/anticausal phase convention.
  rho=1-1/n1              Leaky stabilizer for the zero-frequency floor.
"""


def halfint_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        halfint_rsf(
            input_path,
            output_path,
            axis=params.get_int("axis", 1),
            inv=params.get_bool("inv", default=params.get_bool("inverse", default=False)),
            adj=params.get_bool("adj", default=False),
            rho=params.get_float("rho") if params.has("rho") else None,
        )
    except (HalfIntError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        halfint_command,
        argv,
        prog="pymada-halfint",
        description="Apply a bounded sfhalfint half-order trace transform.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
