"""Module-only Madagascar-style CLI for dividing RSF datasets."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.generic.array_math import ArrayMathError, divide_rsf
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """Div parameters:
  input.rsf other.rsf       Compatible input RSF files.
  scalar=2.0                Divide input by a scalar instead of other.rsf.
  zero_policy=raise|warn|nan|inf
  out=output.rsf            Output RSF header path.

The default zero_policy=raise reports zero denominators instead of silently
keeping input samples.
"""


def div_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output = params.output_path(required=True)
    assert input_path is not None
    assert output is not None

    scalar = params.get_float("scalar") if params.has("scalar") else None
    other = None
    if scalar is None:
        if len(params.positionals) < 2:
            raise ParameterParseError("div requires other.rsf or scalar=")
        other = params.positionals[1]
    zero_policy = params.get_string("zero_policy", "raise")

    try:
        divide_rsf(input_path, other, output, scalar=scalar, zero_policy=zero_policy)
    except (ArrayMathError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        div_command,
        argv,
        prog="python -m pymadagascar.cli.div",
        description="Divide file-backed RSF datasets or divide by scalar=.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
