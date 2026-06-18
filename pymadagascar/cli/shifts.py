"""Module-only CLI for integer sample shifts."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import MissingParameterError, ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.signal.conditioning import ConditioningError, shifts_rsf


HELP_TEXT = """Shifts parameters:
  input.rsf               Input RSF file.
  out=shifted.rsf         Output RSF header path.
  shift=3                 Integer sample shift; positive delays samples.
  axis=1                  1-based RSF axis.
  fill=0.0                Fill value for non-circular shifts.
  circular=n              If yes, use periodic wrapping.

This is an integer-sample conditioning subset. It does not implement upstream
multi-slope interpolation output.
"""


def shifts_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    if not params.has("shift"):
        raise MissingParameterError("shift")
    assert input_path is not None
    assert output_path is not None
    try:
        shifts_rsf(
            input_path,
            output_path,
            shift=params.get_int("shift"),
            axis=params.get_int("axis", 1),
            fill=params.get_float("fill", 0.0),
            circular=params.get_bool("circular", False),
        )
    except (ConditioningError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        shifts_command,
        argv,
        prog="python -m pymadagascar.cli.shifts",
        description="Shift RSF samples by an integer amount along one axis.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
