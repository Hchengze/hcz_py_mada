"""Madagascar-style CLI for concatenating RSF files."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import MissingParameterError, ParameterParseError, RSFParams
from pymadagascar.generic.cat import CatError, cat_rsf
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """Cat parameters:
  input1.rsf input2.rsf ...   Input RSF files.
  axis=                       1-based RSF axis to concatenate; defaults to 3.
  out=output.rsf              Output RSF header path.

Non-concatenated axes must have matching n#, o#, and d# metadata.
"""


def cat_command(params: RSFParams) -> int:
    inputs: list[str] = []
    input_path = params.params.get("in") or params.params.get("input")
    if input_path not in {None, "", "-", "stdin"}:
        inputs.append(input_path)  # type: ignore[arg-type]
    inputs.extend(params.positionals)
    if len(inputs) < 2:
        raise ParameterParseError("pymada-cat requires at least two input RSF files")

    output = params.params.get("out") or params.params.get("--out") or params.params.get("output")
    if output in {None, "", "-", "stdout"}:
        raise MissingParameterError("out")
    axis = params.get_int("axis", 3)

    try:
        cat_rsf(inputs, output, axis=axis)
    except (CatError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        cat_command,
        argv,
        prog="pymada-cat",
        description="Concatenate compatible file-backed RSF datasets.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
