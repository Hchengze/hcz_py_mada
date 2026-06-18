"""Module-only CLI for shape-preserving cosine tapers."""

from __future__ import annotations

from collections.abc import Sequence
import re
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import MissingParameterError, ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.signal.preprocessing import PreprocessingError, costaper_rsf


HELP_TEXT = """Costaper parameters:
  input.rsf               Input RSF file.
  out=output.rsf          Output RSF header path.
  width1=5 width2=3       Taper widths by 1-based RSF axis.
  nw1=5 nw2=3             Upstream-style aliases for width#.
  axis=1 width=5          Apply one scalar width to one axis.
  axes=1,2 widths=5,3     Apply widths to selected axes.

width=0 is a no-op for that axis. This is an in-memory 1D/2D/3D subset and
does not stream large datasets.
"""


def costaper_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        costaper_rsf(input_path, output_path, widths=_widths(params), axes=_axes(params))
    except (PreprocessingError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        costaper_command,
        argv,
        prog="python -m pymadagascar.cli.costaper",
        description="Apply a cosine taper around RSF data boundaries.",
        help_text=HELP_TEXT,
    )


def _axes(params: RSFParams) -> tuple[int, ...] | int | None:
    if params.has("axis"):
        return params.get_int("axis")
    if params.has("axes"):
        return tuple(params.get_list("axes", item_type=int))
    return None


def _widths(params: RSFParams) -> int | tuple[int, ...] | dict[int, int]:
    axis_widths: dict[int, int] = {}
    for key, value in params.params.items():
        match = re.fullmatch(r"(?:width|nw)(\d+)", key)
        if match:
            axis_widths[int(match.group(1))] = int(value)
    if axis_widths:
        return axis_widths
    if params.has("width"):
        return params.get_int("width")
    if params.has("widths"):
        return tuple(params.get_list("widths", item_type=int))
    raise MissingParameterError("width1")


if __name__ == "__main__":
    sys.exit(main())
