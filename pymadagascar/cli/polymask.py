"""CLI for bounded source-aligned polygon masks."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.generic.polymask import PolyMaskError, polymask_rsf
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """PolyMask parameters:
  input.rsf               Input 2D RSF grid defining n1/n2/o1/o2/d1/d2.
  poly=vertices.rsf       Float RSF table of polygon vertices, n1=2, n2=nv.
  out=mask.rsf            Output native_int 0/1 mask.

This bounded sfpolymask subset follows ../src-master/system/generic/Mpolymask.c
for regular 2D grids. It does not implement multi-dimensional masks, polygon
repair, plotting, or non-RSF vertex formats.
"""


def polymask_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        polymask_rsf(input_path, params.get_string("poly"), output_path)
    except (PolyMaskError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        polymask_command,
        argv,
        prog="pymada-polymask",
        description="Create a source-aligned 2D polygon mask.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
