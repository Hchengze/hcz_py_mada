"""Madagascar-style CLI for normalizing RSF datasets."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.generic.array_math import ArrayMathError, normalize_rsf
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """Normalize parameters:
  input.rsf           Input RSF file.
  mode=max            max or rms normalization. Defaults to max.
  out=output.rsf      Output RSF header path.

The normalization scale ignores NaN samples. Existing NaN samples are preserved
in the output.
"""


def normalize_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output = params.output_path(required=True)
    mode = params.get_string("mode", default="max")
    assert input_path is not None
    assert output is not None

    try:
        normalize_rsf(input_path, output, mode=mode)
    except (ArrayMathError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        normalize_command,
        argv,
        prog="pymada-normalize",
        description="Normalize a file-backed RSF dataset.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
