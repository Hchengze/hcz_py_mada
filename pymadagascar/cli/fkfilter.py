"""CLI for 2D FK fan velocity filtering."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.seismic.fk import FKError, fk_filter


HELP_TEXT = """FK filter parameters:
  input.rsf           2D shot gather input RSF file.
  out=output.rsf      Output RSF header path.
  vmin=               Minimum apparent velocity to pass.
  vmax=               Maximum apparent velocity to pass.
  taper=0             Cosine taper width in velocity units.
  reject=no           Reject the selected fan instead of passing it.
  time_axis=1         1-based RSF time axis.
  space_axis=2        1-based RSF space/offset axis.

Velocity is abs(frequency) / abs(wavenumber). With d1 in seconds and d2 in
meters, velocity is meters/second.
"""


def fkfilter_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    vmin = params.get_float("vmin", default=None)
    vmax = params.get_float("vmax", default=None)
    taper = params.get_float("taper", default=0.0)
    reject = params.get_bool("reject", default=False)
    time_axis = params.get_int("time_axis", default=params.get_int("axis", default=1))
    space_axis = params.get_int("space_axis", default=params.get_int("xaxis", default=2))
    norm = params.get_string("norm", default=None)
    assert input_path is not None
    assert output_path is not None

    try:
        fk_filter(
            input_path,
            output_path,
            vmin=vmin,
            vmax=vmax,
            taper=taper,
            reject=reject,
            time_axis=time_axis,
            space_axis=space_axis,
            norm=norm,
        )
    except (FKError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        fkfilter_command,
        argv,
        prog="pymada-fkfilter",
        description="Apply a centered FK fan velocity filter to a 2D RSF gather.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())

