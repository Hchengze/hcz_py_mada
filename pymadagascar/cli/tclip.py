"""CLI for bounded threshold clipping."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.generic.tclip import TClipError, tclip_rsf
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """TClip parameters:
  input.rsf               Real input RSF file.
  out=output.rsf          Output RSF header path.
  lowercut=0.2            Samples below this value are set to 0.
  uppercut=0.8            Samples above this value are set to 1.

This bounded sftclip subset follows ../src-master/system/generic/Mtclip.c and
leaves samples inside [lowercut, uppercut] unchanged.
"""


def tclip_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        tclip_rsf(
            input_path,
            output_path,
            lowercut=params.get_float("lowercut", 0.2),
            uppercut=params.get_float("uppercut", 0.8),
        )
    except (TClipError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        tclip_command,
        argv,
        prog="pymada-tclip",
        description="Apply bounded sftclip lower/upper threshold clipping.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
