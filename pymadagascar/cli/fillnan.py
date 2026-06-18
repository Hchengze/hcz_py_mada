"""Module-only CLI for replacing NaN and Inf samples."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.generic.statistics import StatisticsError, fillnan_rsf
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """Fill parameters:
  input.rsf               Numeric input RSF file.
  out=filled.rsf          Output RSF header path.
  mode=nan                nan, inf, or nonfinite.
  value=0                 Replacement value.
"""


def fillnan_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        fillnan_rsf(
            input_path,
            output_path,
            mode=params.get_string("mode", "nan"),
            value=params.get_float("value", 0.0),
        )
    except (StatisticsError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        fillnan_command,
        argv,
        prog="python -m pymadagascar.cli.fillnan",
        description="Replace selected NaN or Inf samples.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
