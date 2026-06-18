"""Module-only CLI for regular-axis linear resampling."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.generic.sampling import SamplingError, linear_rsf
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """Linear resampling parameters:
  input.rsf               Input RSF file.
  out=output.rsf          Output RSF header path.
  axis=1                  1-based RSF axis to resample.
  n=200                   Output sample count; defaults to input axis length.
  o=0 d=0.004             Output origin and spacing; default to input o#/d#.
  fill=0.0                Value outside the input coordinate range.

This is a regular-grid NumPy interpolation subset. It does not implement the
full upstream sflinear irregular coordinate/value-table and regularization
parameter surface.
"""


def linear_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        linear_rsf(
            input_path,
            output_path,
            axis=params.get_int("axis", 1),
            n=params.get_int("n") if params.has("n") else None,
            o=params.get_float("o") if params.has("o") else None,
            d=params.get_float("d") if params.has("d") else None,
            fill=params.get_float("fill", 0.0),
        )
    except (SamplingError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        linear_command,
        argv,
        prog="python -m pymadagascar.cli.linear",
        description="Linearly resample one regular RSF axis.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
