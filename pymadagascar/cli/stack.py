"""CLI for seismic stacking."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.seismic.stack import StackError, stack_rsf


HELP_TEXT = """Stack parameters:
  input.rsf        Input RSF gather.
  out=output.rsf   Output RSF header path.
  axis=2           1-based RSF axis to stack.
  mode=mean        mean, sum, or rms.
  nonzero=yes      If yes, mean/rms fold counts only nonzero samples.
"""


def stack_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    axis = params.get_int("axis", default=2)
    mode = params.get_string("mode", default="mean")
    nonzero = params.get_bool("nonzero", default=params.get_bool("norm", default=True))
    assert input_path is not None
    assert output_path is not None

    try:
        stack_rsf(input_path, output_path, axis=axis, mode=mode, nonzero=nonzero)
    except (StackError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        stack_command,
        argv,
        prog="pymada-stack",
        description="Stack an RSF gather over a selected axis.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
