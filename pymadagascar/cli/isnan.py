"""Module-only CLI for finite and non-finite sample masks."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.generic.statistics import StatisticsError, isnan_rsf
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """Mask parameters:
  input.rsf               Numeric input RSF file.
  out=mask.rsf            Output int32 0/1 RSF path.
  mode=nan                nan, inf, nonfinite, or finite.
"""


def isnan_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        isnan_rsf(
            input_path,
            output_path,
            mode=params.get_string("mode", "nan"),
        )
    except (StatisticsError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        isnan_command,
        argv,
        prog="python -m pymadagascar.cli.isnan",
        description="Write a shape-preserving finite/non-finite sample mask.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
