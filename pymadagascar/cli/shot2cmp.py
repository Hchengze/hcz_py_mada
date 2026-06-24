"""CLI for bounded regular shot-to-CMP gather reorganization."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.seismic.gather import GatherError, shot2cmp_rsf


HELP_TEXT = """Shot2CMP parameters:
  input.rsf               Regular 3D shot gather, axes n1=time, n2=offset, n3=shot.
  out=output.rsf          Output CMP gather RSF header path.
  positive=y              Initial offset orientation.
  half=y                  Half-offset input; only the source-aligned default is supported.

This bounded sfshot2cmp subset performs regular 2-D geometry trace
reorganization only. It does not write a mask side output, read SEG-Y trace
headers, or reconstruct irregular survey geometry tables.
"""


def shot2cmp_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        shot2cmp_rsf(
            input_path,
            output_path,
            positive=params.get_bool("positive", True),
            half=params.get_bool("half", True),
        )
    except (GatherError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        shot2cmp_command,
        argv,
        prog="pymada-shot2cmp",
        description="Apply bounded sfshot2cmp regular gather reorganization.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
