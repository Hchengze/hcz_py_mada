"""Module-only CLI for simple maximum picking along an RSF axis."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.generic.sampling import SamplingError, max1_rsf
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """Max1 parameters:
  input.rsf               Input RSF file.
  out=max1.rsf            Output RSF header path.
  axis=1                  1-based RSF axis to search.
  mode=value              value, index, or coord.
  abs=y                   Search by absolute value but return original value.
  nan_policy=propagate    propagate or omit.

This subset returns one value/index/coordinate per remaining trace. It does not
emit upstream sfmax1's complex list of local maxima with np= and sorted=.
"""


def max1_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        max1_rsf(
            input_path,
            output_path,
            axis=params.get_int("axis", 1),
            mode=params.get_string("mode", "value"),
            abs_search=params.get_bool("abs", False),
            nan_policy=params.get_string("nan_policy", "propagate"),
        )
    except (SamplingError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        max1_command,
        argv,
        prog="python -m pymadagascar.cli.max1",
        description="Pick maximum values, indices, or coordinates along an RSF axis.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
