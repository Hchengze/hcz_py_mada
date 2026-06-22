"""Madagascar-style CLI for cyclically rotating RSF data."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.generic.rotate import RotateError, rotate_rsf
from pymadagascar.io.rsf import RSFError, SF_MAX_DIM


HELP_TEXT = """Rotate parameters:
  input.rsf           Input RSF file.
  out=output.rsf      Output RSF header path.
  rot1=0 rot2=0       Samples from the start of each axis moved to the end.

Axis numbers are 1-based RSF axes. Negative rot# values wrap by n# before
validation, following upstream sfrotate.
"""


def rotate_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output = params.output_path(required=True)
    assert input_path is not None
    assert output is not None

    rotations: dict[int, int] = {}
    for axis in range(1, SF_MAX_DIM + 1):
        key = f"rot{axis}"
        if params.has(key):
            rotations[axis] = params.get_int(key)

    try:
        rotate_rsf(input_path, output, rotations=rotations)
    except (RotateError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        rotate_command,
        argv,
        prog="pymada-rotate",
        description="Cyclically rotate one or more axes of an RSF dataset.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
