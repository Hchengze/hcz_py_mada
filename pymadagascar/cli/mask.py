"""CLI for creating 0/1 RSF masks."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.generic.mask import MaskError, mask_rsf
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """Mask parameters:
  input.rsf           Input real-valued RSF file.
  out=mask.rsf        Output RSF header path.
  min=                Inclusive lower bound. Defaults to -inf.
  max=                Inclusive upper bound. Defaults to +inf.

The output is RSF native_int with samples 1 inside [min,max] and 0 outside.
"""


def mask_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output = params.output_path(required=True)
    assert input_path is not None
    assert output is not None

    try:
        mask_rsf(
            input_path,
            output,
            min_value=params.get_float("min", default=None),
            max_value=params.get_float("max", default=None),
        )
    except (MaskError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        mask_command,
        argv,
        prog="pymada-mask",
        description="Create an integer 0/1 mask from a real-valued RSF dataset.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
