"""CLI for Otsu threshold estimation from integer histograms."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.generic.otsu import OtsuError, otsu_rsf
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """Otsu parameters:
  hist.rsf                Integer 1D histogram RSF file.

Prints threshold=<value> using the source-aligned Otsu between-class variance
criterion from ../src-master/system/generic/Motsu.c.
"""


def otsu_command(params: RSFParams) -> str:
    input_path = params.input_path(required=True)
    assert input_path is not None
    try:
        threshold = otsu_rsf(input_path)
    except (OtsuError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return f"threshold={threshold:g}\n"


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        otsu_command,
        argv,
        prog="pymada-otsu",
        description="Estimate an Otsu threshold from a 1D integer RSF histogram.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
