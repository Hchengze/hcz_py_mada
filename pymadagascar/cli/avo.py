"""CLI for bounded AVO intercept/gradient least-squares fitting."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.seismic.avo import AVOError, avo_rsf


HELP_TEXT = """AVO parameters:
  input.rsf               Input CMP gather with n1=time and n2=offset.
  out=output.rsf          Output RSF header path.
  half=y                  Treat axis 2 as half-offset when offset= is absent.
  offset=offset.rsf       Optional 1D or per-gather offset RSF file.

This bounded sfavo subset computes intercept and gradient by ordinary least
squares along RSF axis 2. It does not implement irregular SEG-Y gather
handling, CDPtype shifts, or production AVO attribute workflows.
"""


def avo_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        avo_rsf(
            input_path,
            output_path,
            offset_path=params.get_string("offset") if params.has("offset") else None,
            half=params.get_bool("half", True),
        )
    except (AVOError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        avo_command,
        argv,
        prog="pymada-avo",
        description="Compute bounded sfavo intercept and gradient attributes.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
