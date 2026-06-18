"""Module-only CLI for scalar sample-wise powers."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import MissingParameterError, ParameterParseError, RSFParams
from pymadagascar.generic.unary import UnaryMathError, pow_rsf
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """Power parameters:
  input.rsf               Real input RSF file.
  out=pow.rsf             Output RSF header path.
  exponent=2              Required scalar sample exponent.

This is an sfmath-style input**exponent convenience subset. Upstream sfpow is
an axis-coordinate gain program and remains represented by pymadagascar tpow.
"""


def pow_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    if not params.has("exponent"):
        raise MissingParameterError("exponent")
    assert input_path is not None
    assert output_path is not None
    try:
        pow_rsf(
            input_path,
            output_path,
            exponent=params.get_float("exponent"),
        )
    except (UnaryMathError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        pow_command,
        argv,
        prog="python -m pymadagascar.cli.pow",
        description="Raise real RSF samples to a scalar exponent.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
