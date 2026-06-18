"""Module-only CLI for global or axis-wise medians."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.generic.statistics import StatisticsError, median_rsf
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """Median parameters:
  input.rsf               Real input RSF file.
  out=median.rsf          Output RSF header path.
  axis=0                  0/global or a 1-based RSF axis.
  nan_policy=propagate    propagate, omit, or raise.
"""


def median_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    axis = params.get_int("axis", 0)
    assert input_path is not None
    assert output_path is not None
    try:
        median_rsf(
            input_path,
            output_path,
            axis=None if axis == 0 else axis,
            nan_policy=params.get_string("nan_policy", "propagate"),
        )
    except (StatisticsError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        median_command,
        argv,
        prog="python -m pymadagascar.cli.median",
        description="Write a global or axis-wise median.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
