"""Module-only Madagascar-style CLI for multiplying RSF datasets."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import MissingParameterError, ParameterParseError, RSFParams
from pymadagascar.generic.array_math import ArrayMathError, multiply_rsf
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """Mul parameters:
  input.rsf other.rsf    Compatible input RSF files.
  scalar=2.0             Multiply input by a scalar instead of other.rsf.
  out=output.rsf         Output RSF header path.

This is a Python subset of sfmul/sfadd mode=mul. It supports one input file
times one other file, or one input file times scalar=.
"""


def mul_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output = params.output_path(required=True)
    assert input_path is not None
    assert output is not None

    scalar = params.get_float("scalar") if params.has("scalar") else None
    other = None
    if scalar is None:
        if len(params.positionals) < 2:
            raise ParameterParseError("mul requires other.rsf or scalar=")
        other = params.positionals[1]

    try:
        multiply_rsf(input_path, other, output, scalar=scalar)
    except (ArrayMathError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        mul_command,
        argv,
        prog="python -m pymadagascar.cli.mul",
        description="Multiply file-backed RSF datasets or multiply by scalar=.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
