"""Module-only CLI for constant or linear detrending."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.signal.qc import SignalQCError, detrend_rsf


HELP_TEXT = """Detrend parameters:
  input.rsf               Numeric input RSF file.
  out=detrend.rsf         Output RSF header path.
  axis=1                  1-based RSF axis.
  type=linear             constant or linear.
  nan_policy=propagate    propagate, omit, or raise.
"""


def detrend_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        detrend_rsf(
            input_path,
            output_path,
            axis=params.get_int("axis", 1),
            type=params.get_string("type", "linear"),
            nan_policy=params.get_string("nan_policy", "propagate"),
        )
    except (SignalQCError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        detrend_command,
        argv,
        prog="python -m pymadagascar.cli.detrend",
        description="Remove a constant or linear trend along one RSF axis.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
