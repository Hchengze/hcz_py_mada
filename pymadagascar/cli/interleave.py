"""Module-only Madagascar-style CLI for interleaving RSF datasets."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import MissingParameterError, ParameterParseError, RSFParams
from pymadagascar.generic.interleave import InterleaveError, interleave_rsf
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """Interleave parameters:
  input1.rsf input2.rsf ...   Compatible input RSF files.
  axis=1                      1-based RSF axis to interleave.
  out=output.rsf              Output RSF header path.

All inputs must have matching dimensions in this Python subset.
"""


def interleave_command(params: RSFParams) -> int:
    inputs: list[str] = []
    input_path = params.params.get("in") or params.params.get("input")
    if input_path not in {None, "", "-", "stdin"}:
        inputs.append(input_path)  # type: ignore[arg-type]
    inputs.extend(params.positionals)
    if len(inputs) < 2:
        raise ParameterParseError("interleave requires at least two input RSF files")

    output = params.params.get("out") or params.params.get("--out") or params.params.get("output")
    if output in {None, "", "-", "stdout"}:
        raise MissingParameterError("out")
    axis = params.get_int("axis", 1)

    try:
        interleave_rsf(inputs, output, axis=axis)
    except (InterleaveError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        interleave_command,
        argv,
        prog="python -m pymadagascar.cli.interleave",
        description="Interleave compatible file-backed RSF datasets.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
