"""Madagascar-style CLI for extracting the imaginary part of complex RSF data."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.generic.complex_tools import ComplexToolError, imag_rsf
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """sfimag-compatible subset:
  input.rsf           Complex RSF input.
  out=imag.rsf        Real-valued RSF output.

sfimag is an alias of sfreal in original Madagascar; this Python command keeps
it as an explicit module for script-friendly use.
"""


def imag_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        imag_rsf(input_path, output_path)
    except (ComplexToolError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        imag_command,
        argv,
        prog="pymada-imag",
        description="Extract the imaginary component of complex RSF data.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
