"""CLI for semblance velocity scanning."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.seismic.nmo import NMOError
from pymadagascar.seismic.semblance import SemblanceError, semblance_scan


HELP_TEXT = """Semblance parameters:
  input.rsf          Input CMP gather.
  out=semblance.rsf  Output semblance panel.
  vmin=1500          First velocity.
  vmax=3000          Last velocity.
  dv=50              Velocity increment.
  offset=offset.rsf  Optional offset values; otherwise axis 2 coordinates.
  half=yes           If yes, offset axis stores half-offset.
  stretch=0.5        Stretch mute threshold; 0 disables.
  smooth=0           Half-window in samples for time smoothing.
"""


def semblance_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    vmin = params.get_float("vmin")
    vmax = params.get_float("vmax")
    dv = params.get_float("dv")
    axis = params.get_int("axis", default=1)
    offset_axis = params.get_int("offset_axis", default=params.get_int("xaxis", default=2))
    half = params.get_bool("half", default=True)
    h0 = params.get_float("h0", default=0.0)
    stretch_value = params.get_float("stretch", default=params.get_float("str", default=0.5))
    stretch = None if stretch_value == 0.0 else stretch_value
    smooth = params.get_int("smooth", default=0)
    offset = params.params.get("offset")
    assert input_path is not None
    assert output_path is not None

    try:
        semblance_scan(
            input_path,
            output_path,
            vmin=vmin,
            vmax=vmax,
            dv=dv,
            axis=axis,
            offset_axis=offset_axis,
            offset=offset,
            half=half,
            h0=h0,
            stretch=stretch,
            smooth=smooth,
        )
    except (SemblanceError, NMOError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        semblance_command,
        argv,
        prog="pymada-semblance",
        description="Compute a velocity semblance panel from a CMP gather.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
