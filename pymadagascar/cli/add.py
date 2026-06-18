"""Madagascar-style CLI for adding RSF datasets."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import MissingParameterError, ParameterParseError, RSFParams
from pymadagascar.generic.array_math import ArrayMathError, add_rsf
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """Add parameters:
  input1.rsf input2.rsf ...   Compatible input RSF files.
  out=output.rsf              Output RSF header path.

All inputs must have matching shape and RSF n# dimensions. The output inherits
geometry metadata from the first input.
"""


def add_command(params: RSFParams) -> int:
    inputs: list[str] = []
    input_path = params.params.get("in") or params.params.get("input")
    if input_path not in {None, "", "-", "stdin"}:
        inputs.append(input_path)  # type: ignore[arg-type]
    inputs.extend(params.positionals)
    if len(inputs) < 2:
        raise ParameterParseError("pymada-add requires at least two input RSF files")

    output = params.params.get("out") or params.params.get("--out") or params.params.get("output")
    if output in {None, "", "-", "stdout"}:
        raise MissingParameterError("out")

    try:
        add_rsf(inputs, output)
    except (ArrayMathError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        add_command,
        argv,
        prog="pymada-add",
        description="Add compatible file-backed RSF datasets.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
