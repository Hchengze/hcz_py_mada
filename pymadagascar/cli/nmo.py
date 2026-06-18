"""CLI for normal moveout correction."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import MissingParameterError, ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.seismic.nmo import NMOError, inverse_nmo, nmo_correct


HELP_TEXT = """NMO parameters:
  input.rsf velocity.rsf   Input CMP gather and velocity function.
  out=output.rsf           Output RSF header path.
  velocity=1500            Scalar velocity or velocity RSF path alias.
  offset=offset.rsf        Optional offset values; otherwise axis 2 coordinates.
  axis=1                   1-based RSF time axis.
  offset_axis=2            1-based RSF offset axis.
  half=yes                 If yes, offset axis stores half-offset.
  h0=0                     Reference offset.
  stretch=0.5              Madagascar-style stretch mute threshold; 0 disables.
  inv=no                   If yes, apply inverse NMO.
"""


def nmo_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.params.get("out") or params.params.get("output")
    if output_path in {None, "", "-", "stdout"}:
        raise MissingParameterError("out")
    velocity = _velocity_argument(params)
    axis = params.get_int("axis", default=1)
    offset_axis = params.get_int("offset_axis", default=params.get_int("xaxis", default=2))
    half = params.get_bool("half", default=True)
    h0 = params.get_float("h0", default=0.0)
    stretch_value = params.get_float("stretch", default=params.get_float("str", default=0.5))
    stretch = None if stretch_value == 0.0 else stretch_value
    offset = params.params.get("offset")
    inverse = params.get_bool("inv", default=params.get_bool("inverse", default=False))
    assert input_path is not None

    try:
        if inverse:
            inverse_nmo(
                input_path,
                velocity,
                output_path,
                axis=axis,
                offset_axis=offset_axis,
                offset=offset,
                half=half,
                h0=h0,
                stretch=stretch,
            )
        else:
            nmo_correct(
                input_path,
                velocity,
                output_path,
                axis=axis,
                offset_axis=offset_axis,
                offset=offset,
                half=half,
                h0=h0,
                stretch=stretch,
            )
    except (NMOError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        nmo_command,
        argv,
        prog="pymada-nmo",
        description="Apply normal moveout correction to a CMP gather.",
        help_text=HELP_TEXT,
    )


def _velocity_argument(params: RSFParams) -> str:
    value = params.params.get("velocity") or params.params.get("vel") or params.params.get("v")
    if value is not None:
        return value
    if len(params.positionals) >= 2:
        return params.positionals[1]
    raise MissingParameterError("velocity")


if __name__ == "__main__":
    sys.exit(main())
