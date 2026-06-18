"""Module-only CLI for real sample signs."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.generic.unary import UnaryMathError, sign_rsf
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """Sign parameters:
  input.rsf               Real input RSF file.
  out=sign.rsf            Output RSF header path.

Output samples are -1, 0, or 1. Complex input is rejected.
"""


def sign_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        sign_rsf(input_path, output_path)
    except (UnaryMathError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        sign_command,
        argv,
        prog="python -m pymadagascar.cli.sign",
        description="Write signs of real RSF samples.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
