"""Module-only CLI for cumulative numerical integration."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.signal.calculus import CalculusError, integral_rsf


HELP_TEXT = """Integral parameters:
  input.rsf               Input RSF file.
  out=integral.rsf        Output RSF header path.
  axis=1                  1-based RSF axis.
  method=trapezoid        trapezoid or cumsum.
  scale_by_d=y            Use input header d# as integration spacing.

This is a general cumulative NumPy subset, not a full clone of the small
user/songxl finite-difference wave-extrapolation helper.
"""


def integral_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        integral_rsf(
            input_path,
            output_path,
            axis=params.get_int("axis", 1),
            method=params.get_string("method", "trapezoid"),
            scale_by_d=params.get_bool("scale_by_d", True),
        )
    except (CalculusError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        integral_command,
        argv,
        prog="python -m pymadagascar.cli.integral",
        description="Cumulatively integrate RSF data along one regular axis.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
