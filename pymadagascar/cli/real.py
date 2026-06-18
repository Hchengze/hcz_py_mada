"""Madagascar-style CLI for extracting the real part of complex RSF data."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.generic.complex_tools import ComplexToolError, real_rsf
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """sfreal-compatible subset:
  input.rsf           Complex RSF input.
  out=real.rsf        Real-valued RSF output.

The header axes are inherited from the input; data_format changes from
native_complex to native_float for the current file-backed implementation.
"""


def real_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        real_rsf(input_path, output_path)
    except (ComplexToolError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        real_command,
        argv,
        prog="pymada-real",
        description="Extract the real component of complex RSF data.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
