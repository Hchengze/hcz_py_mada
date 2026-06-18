"""Madagascar-style CLI for clipping RSF datasets."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import MissingParameterError, ParameterParseError, RSFParams
from pymadagascar.generic.array_math import ArrayMathError, clip_rsf
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """Clip parameters:
  input.rsf           Input RSF file.
  clip=1.0            Symmetric clipping threshold.
  out=output.rsf      Output RSF header path.

Values above clip are set to clip and values below -clip are set to -clip.
NaN values are preserved.
"""


def clip_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output = params.output_path(required=True)
    assert input_path is not None
    assert output is not None

    if not params.has("clip"):
        raise MissingParameterError("clip")
    clip = params.get_float("clip")

    try:
        clip_rsf(input_path, output, clip)
    except (ArrayMathError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        clip_command,
        argv,
        prog="pymada-clip",
        description="Symmetrically clip a file-backed RSF dataset.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
