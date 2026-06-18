"""CLI for the 2D post-stack Kirchhoff time-migration prototype."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import MissingParameterError, ParameterParseError, RSFParams
from pymadagascar.imaging.kirchhoff import ImagingError, kirchhoff_time_migration
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """Kirchhoff prototype parameters:
  input.rsf            2D post-stack section.
  out=image.rsf        Output migrated image.
  velocity=2000        Constant velocity or 1D velocity RSF path.
  v0=2000              Alias for velocity=.
  axis=1               1-based RSF time axis.
  x_axis=2             1-based RSF lateral axis.
  aperture=            Optional migration aperture in lateral units.
  normalize=no         Divide each image sample by live trace count.

This is a small prototype and does not reproduce sfkirchnew antialiasing or
half-derivative amplitude behavior.
"""


def kirchhoff_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    velocity = params.params.get("velocity") or params.params.get("vel") or params.params.get("v0")
    if velocity is None:
        raise MissingParameterError("velocity")
    axis = params.get_int("axis", default=1)
    x_axis = params.get_int("x_axis", default=params.get_int("xaxis", default=2))
    aperture = params.get_float("aperture", default=None)
    normalize = params.get_bool("normalize", default=False)
    assert input_path is not None
    assert output_path is not None

    try:
        kirchhoff_time_migration(
            input_path,
            output_path,
            velocity=velocity,
            axis=axis,
            x_axis=x_axis,
            aperture=aperture,
            normalize=normalize,
        )
    except (ImagingError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        kirchhoff_command,
        argv,
        prog="pymada-kirchhoff",
        description="Run a small 2D post-stack Kirchhoff time-migration prototype.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())

