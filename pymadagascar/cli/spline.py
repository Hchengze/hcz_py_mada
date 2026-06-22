"""CLI for a bounded source-aligned cubic spline interpolation subset."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.generic.remap import RemapError, spline_rsf
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """Spline parameters:
  input.rsf               Input RSF file.
  out=output.rsf          Output RSF header path.
  axis=1                  1-based RSF axis to interpolate.
  n=200                   Output sample count; defaults to input axis length.
  o=0 d=0.004             Output origin and spacing; default to input o#/d#.
  fill_value=0.0          Value outside the input coordinate range.

This bounded sfspline subset applies one-axis natural cubic spline
interpolation using NumPy only. It does not implement irregular coordinate/value
tables, endpoint derivative fp= controls, pattern= files, or streaming.
"""


def spline_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        spline_rsf(
            input_path,
            output_path,
            axis=params.get_int("axis", 1),
            n=params.get_int("n") if params.has("n") else None,
            o=params.get_float("o") if params.has("o") else None,
            d=params.get_float("d") if params.has("d") else None,
            fill_value=_fill_value(params),
        )
    except (RemapError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        spline_command,
        argv,
        prog="pymada-spline",
        description="Apply a bounded one-axis cubic spline interpolation.",
        help_text=HELP_TEXT,
    )


def _fill_value(params: RSFParams) -> float:
    if params.has("fill_value"):
        return params.get_float("fill_value")
    return params.get_float("fill", 0.0)


if __name__ == "__main__":
    sys.exit(main())
