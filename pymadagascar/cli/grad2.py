"""CLI for bounded 2-D smooth Sobel gradient squared."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.generic.edge import EdgeError, grad2_rsf
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """Grad2 parameters:
  input.rsf               Real input RSF file with at least axes n1,n2.
  out=output.rsf          Output RSF header path.

This bounded sfgrad2 subset follows ../src-master/system/generic/Mgrad2.c
and ../src-master/api/c/edge.c. It computes Sobel gradient squared on each
2-D n1,n2 slice and zeroes the outer edge samples.
"""


def grad2_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        grad2_rsf(input_path, output_path)
    except (EdgeError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        grad2_command,
        argv,
        prog="pymada-grad2",
        description="Compute bounded sfgrad2 Sobel gradient squared.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
