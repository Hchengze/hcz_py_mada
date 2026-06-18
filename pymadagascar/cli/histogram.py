"""Module-only CLI for small-data histogram tables."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.generic.unary import UnaryMathError, histogram_rsf
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """Histogram parameters:
  input.rsf               Real input RSF file.
  out=hist.rsf            Output RSF header path.
  bins=10                 Positive number of bins.
  min=-1 max=1            Optional histogram range limits.
  density=n               Output density instead of counts.

Output is a 2D RSF table with columns center,value. Non-finite input samples
are omitted.
"""


def histogram_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        histogram_rsf(
            input_path,
            output_path,
            bins=params.get_int("bins", 10),
            min_value=params.get_float("min") if params.has("min") else None,
            max_value=params.get_float("max") if params.has("max") else None,
            density=params.get_bool("density", False),
        )
    except (UnaryMathError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        histogram_command,
        argv,
        prog="python -m pymadagascar.cli.histogram",
        description="Write a bin-center/count-or-density RSF histogram table.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
