"""CLI for bounded regular CMP-to-shot gather reorganization."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.seismic.gather import GatherError, cmp2shot_rsf


HELP_TEXT = """CMP2Shot parameters:
  input.rsf               Regular 3D CMP gather, axes n1=time, n2=offset, n3=CMP.
  out=output.rsf          Output shot gather RSF header path.
  positive=y              Initial offset orientation.

This bounded sfcmp2shot subset performs regular 2-D geometry trace
reorganization only. It does not read SEG-Y trace headers or irregular
survey geometry tables.
"""


def cmp2shot_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        cmp2shot_rsf(input_path, output_path, positive=params.get_bool("positive", True))
    except (GatherError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        cmp2shot_command,
        argv,
        prog="pymada-cmp2shot",
        description="Apply bounded sfcmp2shot regular gather reorganization.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
