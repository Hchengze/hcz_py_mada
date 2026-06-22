"""CLI for bounded real matching filtering."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.generic.array_algebra import ArrayAlgebraError, match_rsf
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """Match parameters:
  input.rsf other.rsf     Forward mode: input is filter, other is noise/data grid.
  out=output.rsf          Output RSF header path.
  adj=n                   If y, input is data and output is a filter.
  nf=5                    Required filter size in adjoint mode.

This bounded sfmatch subset implements the source symmetric zero-boundary
matching-filter loop for real in-memory arrays. It is not a shaping-filter or
solver framework.
"""


def match_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    other_path = _other_path(params)
    assert input_path is not None
    assert output_path is not None
    try:
        match_rsf(
            input_path,
            other_path,
            output_path,
            adj=params.get_bool("adj", False),
            nf=params.get_int("nf") if params.has("nf") else None,
        )
    except (ArrayAlgebraError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def _other_path(params: RSFParams) -> str:
    value = params.params.get("other")
    if value not in {None, "", "-", "stdin"}:
        return str(value)
    if len(params.positionals) >= 2:
        return params.positionals[1]
    raise ParameterParseError("match requires other= or a second positional RSF file")


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        match_command,
        argv,
        prog="pymada-match",
        description="Apply bounded real sfmatch symmetric matching filtering.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
