"""Module-only CLI for circular convolution."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.signal.convolution import ConvolutionError, cconv_rsf

from .convolve import _input_pair


HELP_TEXT = """Circular convolution parameters:
  data.rsf kernel.rsf     Input data and 1D kernel.
  out=cconv.rsf           Output RSF header path.
  axis=1                  1-based RSF axis.

The output shape and header follow the input data. Complex input is supported
through NumPy FFTs; this is not the full upstream internal complex-filter
operator.
"""


def cconv_command(params: RSFParams) -> int:
    inputs = _input_pair(params, "cconv")
    output_path = params.output_path(required=True)
    assert output_path is not None
    try:
        cconv_rsf(inputs[0], inputs[1], output_path, axis=params.get_int("axis", 1))
    except (ConvolutionError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        cconv_command,
        argv,
        prog="python -m pymadagascar.cli.cconv",
        description="Circularly convolve RSF traces along a selected axis.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
