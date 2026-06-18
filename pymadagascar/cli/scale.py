"""Madagascar-style CLI for scaling RSF datasets."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import MissingParameterError, ParameterParseError, RSFParams
from pymadagascar.generic.array_math import ArrayMathError, scale_rsf
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """Scale parameters:
  input.rsf           Input RSF file.
  scale=2.0           Scalar multiplier. dscale= is accepted as an alias.
  out=output.rsf      Output RSF header path.

Integer input is promoted to float32. Float and complex input keep their
corresponding floating dtype.
"""


def scale_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output = params.output_path(required=True)
    assert input_path is not None
    assert output is not None

    if params.has("scale"):
        scale = params.get_float("scale")
    elif params.has("dscale"):
        scale = params.get_float("dscale")
    else:
        raise MissingParameterError("scale")

    try:
        scale_rsf(input_path, output, scale)
    except (ArrayMathError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        scale_command,
        argv,
        prog="pymada-scale",
        description="Scale a file-backed RSF dataset by a scalar.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
