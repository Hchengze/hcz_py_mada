"""CLI for seismic top mute."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.seismic.mute import MuteError, mute_rsf


HELP_TEXT = """Mute parameters:
  input.rsf        Input RSF gather.
  out=output.rsf   Output RSF header path.
  t0=0.0           Base mute time.
  v=1500           Linear mute velocity; t_mute=t0+abs(offset)/v.
  axis=1           1-based RSF time axis.
  offset_axis=2    1-based RSF offset/trace axis.
  taper=0.0        Optional taper length in time-axis units.
"""


def mute_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    t0 = params.get_float("t0")
    v = params.get_float("v")
    axis = params.get_int("axis", default=1)
    offset_axis = params.get_int("offset_axis", default=params.get_int("xaxis", default=2))
    taper = params.get_float("taper", default=0.0)
    assert input_path is not None
    assert output_path is not None

    try:
        mute_rsf(input_path, output_path, t0=t0, v=v, axis=axis, offset_axis=offset_axis, taper=taper)
    except (MuteError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        mute_command,
        argv,
        prog="pymada-mute",
        description="Apply a linear top mute to RSF gathers.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
