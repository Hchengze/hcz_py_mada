"""Module-only CLI for real logarithms."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.generic.unary import UnaryMathError, log_rsf
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """Logarithm parameters:
  input.rsf               Real input RSF file.
  out=log.rsf             Output RSF header path.
  base=e                  e or a positive numeric base other than 1.
  invalid=nan             nan or raise for negative samples.

Zero maps to -inf.
"""


def log_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        log_rsf(
            input_path,
            output_path,
            base=params.get_string("base", "e"),
            invalid=params.get_string("invalid", "nan"),
        )
    except (UnaryMathError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        log_command,
        argv,
        prog="python -m pymadagascar.cli.log",
        description="Write real logarithms of RSF samples.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
