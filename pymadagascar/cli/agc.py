"""CLI for seismic automatic gain control."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.seismic.agc import AGCError, agc_rsf


HELP_TEXT = """AGC parameters:
  input.rsf        Input RSF gather.
  out=output.rsf   Output RSF header path.
  rect=0.5         Local RMS window length in time-axis units.
  axis=1           1-based RSF time axis.
  eps=1e-12        Minimum RMS before output is zeroed.
"""


def agc_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    rect = params.get_float("rect")
    axis = params.get_int("axis", default=1)
    eps = params.get_float("eps", default=1e-12)
    assert input_path is not None
    assert output_path is not None

    try:
        agc_rsf(input_path, output_path, rect=rect, axis=axis, eps=eps)
    except (AGCError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        agc_command,
        argv,
        prog="pymada-agc",
        description="Apply local RMS automatic gain control to RSF gathers.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
