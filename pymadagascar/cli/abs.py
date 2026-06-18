"""Module-only CLI for sample-wise absolute value."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.generic.unary import UnaryMathError, abs_rsf
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """Absolute-value parameters:
  input.rsf               Input RSF file.
  out=abs.rsf             Output RSF header path.

Complex input is supported and produces real magnitude output.
"""


def abs_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        abs_rsf(input_path, output_path)
    except (UnaryMathError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        abs_command,
        argv,
        prog="python -m pymadagascar.cli.abs",
        description="Write sample-wise RSF magnitudes.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
