"""CLI for bounded 3-D smooth Sobel gradient subsets."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.generic.edge import EdgeError, grad3_rsf
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """Grad3 parameters:
  input.rsf               Real input RSF file with at least axes n1,n2,n3.
  out=output.rsf          Output RSF header path.
  dim=0                   0 for gradient squared, or 1/2/3 for one component.

This bounded sfgrad3 subset follows ../src-master/system/generic/Mgrad3.c
and ../src-master/api/c/edge.c. It computes the fixed 3-D Sobel stencil on
each n1,n2,n3 block and zeroes edge samples.
"""


def grad3_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        grad3_rsf(input_path, output_path, dim=params.get_int("dim", 0))
    except (EdgeError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        grad3_command,
        argv,
        prog="pymada-grad3",
        description="Compute bounded sfgrad3 Sobel gradient subset.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
