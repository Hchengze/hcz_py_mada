"""Module-only Madagascar-style CLI for time-power RSF gain."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.generic.array_math import ArrayMathError, tpow_rsf
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """Tpow parameters:
  input.rsf              Input RSF file.
  power=1.5              Power for coordinate ** power. tpow= is accepted.
  axis=1                 1-based RSF axis used for coordinates.
  abs_time=y|n           Use absolute coordinates before exponentiation.
  out=output.rsf         Output RSF header path.

Fractional powers set non-positive coordinates to zero by default.
"""


def tpow_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output = params.output_path(required=True)
    assert input_path is not None
    assert output is not None

    power = params.get_float("power", params.get_float("tpow", 1.0) if params.has("tpow") else 1.0)
    axis = params.get_int("axis", 1)
    abs_time = params.get_bool("abs_time", False)

    try:
        tpow_rsf(input_path, output, power=power, axis=axis, abs_time=abs_time)
    except (ArrayMathError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        tpow_command,
        argv,
        prog="python -m pymadagascar.cli.tpow",
        description="Apply coordinate power gain to a file-backed RSF dataset.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
