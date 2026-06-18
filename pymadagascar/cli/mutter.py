"""Module-only CLI for a small linear above/below mute subset."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import MissingParameterError, ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.seismic.mute import MuteError, mutter_rsf


HELP_TEXT = """Mutter parameters:
  gather.rsf              Input 2D RSF gather.
  out=muted.rsf           Output RSF header path.
  v=1500                  Positive linear mute velocity.
  t0=0                    Base mute time.
  time_axis=1             1-based regular time axis.
  offset_axis=2           1-based regular offset axis.
  side=above              above mutes early times; below mutes late times.
  taper=0                 Transition width in time-axis samples.

This subset uses regular o#/d# coordinates and does not read an offset header
file or implement hyperbolic, half-offset, CDPtype, or multi-slope modes.
"""


def mutter_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    if not params.has("v"):
        raise MissingParameterError("v")
    assert input_path is not None
    assert output_path is not None
    try:
        mutter_rsf(
            input_path,
            output_path,
            time_axis=params.get_int("time_axis", params.get_int("axis", 1)),
            offset_axis=params.get_int("offset_axis", 2),
            v=params.get_float("v"),
            t0=params.get_float("t0", 0.0),
            side=params.get_string("side", "above"),
            taper=params.get_int("taper", 0),
        )
    except (MuteError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        mutter_command,
        argv,
        prog="python -m pymadagascar.cli.mutter",
        description="Apply a regular-axis linear mute to a small 2D gather.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
