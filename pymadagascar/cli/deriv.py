"""Module-only CLI for first finite-difference derivatives."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.signal.calculus import CalculusError, deriv_rsf


HELP_TEXT = """Deriv parameters:
  input.rsf               Input RSF file.
  out=deriv.rsf           Output RSF header path.
  axis=1                  1-based RSF axis.
  method=central          central, forward, or backward.
  scale_by_d=y            Divide differences by input header d#.

This is a first-order finite-difference subset, not the upstream maximally
linear FIR differentiator with order=.
"""


def deriv_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        deriv_rsf(
            input_path,
            output_path,
            axis=params.get_int("axis", 1),
            method=params.get_string("method", "central"),
            scale_by_d=params.get_bool("scale_by_d", params.get_bool("scale", True)),
        )
    except (CalculusError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        deriv_command,
        argv,
        prog="python -m pymadagascar.cli.deriv",
        description="Differentiate RSF data along one regular axis.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
