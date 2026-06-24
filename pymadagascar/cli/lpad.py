"""CLI for bounded trace/plane interleaving."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.generic.lpad import LPadError, lpad_rsf
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """LPad parameters:
  input.rsf               Real input RSF file with at least axes n1,n2.
  out=output.rsf          Output RSF header path.
  jump=2                  Interleave factor; each trace/plane is followed by zeros.
  mask=mask.rsf           Optional integer mask with 1 at retained samples.

This bounded sflpad subset follows ../src-master/system/generic/Mlpad.c.
It interleaves zero traces along axis 2, and zero planes along axis 3 when
present, updating n2/n3 and d2/d3 consistently.
"""


def lpad_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        lpad_rsf(
            input_path,
            output_path,
            jump=params.get_int("jump", 2),
            mask=params.get_string("mask") if params.has("mask") else None,
        )
    except (LPadError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        lpad_command,
        argv,
        prog="pymada-lpad",
        description="Interleave traces and planes with zeros using bounded sflpad.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
