"""Madagascar-style CLI for converting real RSF data to complex RSF data."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.generic.complex_tools import ComplexToolError, rtoc_rsf
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """sfrtoc-compatible subset:
  input.rsf           Real RSF input.
  out=complex.rsf     Complex RSF output with zero imaginary part.

The original command also supports pair=y for packing adjacent real samples as
complex values. That mode is intentionally deferred in this Python subset.
"""


def rtoc_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        rtoc_rsf(input_path, output_path)
    except (ComplexToolError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        rtoc_command,
        argv,
        prog="pymada-rtoc",
        description="Convert real RSF data to complex RSF data.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
