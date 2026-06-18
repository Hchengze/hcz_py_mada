"""Module-only CLI for fixed-index RSF slicing."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.generic.sampling import SamplingError, slice_rsf
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """Slice parameters:
  input.rsf               Input RSF file.
  out=slice.rsf           Output RSF header path.
  axis=3                  1-based RSF axis to remove.
  index=0                 Zero-based Python sample index on that axis.

This is a fixed-index slicing subset. It is not the upstream sfslice picked
surface interpolation tool and does not use a pick= file.
"""


def slice_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        slice_rsf(
            input_path,
            output_path,
            axis=params.get_int("axis", 3),
            index=params.get_int("index", 0),
        )
    except (SamplingError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        slice_command,
        argv,
        prog="python -m pymadagascar.cli.slice",
        description="Extract a fixed-index slice and remove that RSF axis.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
