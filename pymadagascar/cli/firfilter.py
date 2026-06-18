"""Module-only CLI for one-dimensional FIR filtering."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.cli.convolve import _input_pair
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.signal.fir import FIRFilterError, firfilter_rsf


HELP_TEXT = """FIR filter parameters:
  input.rsf taps.rsf      Input data and 1D FIR coefficient RSF.
  out=filtered.rsf        Shape-preserving output.
  axis=1                  1-based RSF filtering axis.
  mode=same               Current subset supports same only.
"""


def firfilter_command(params: RSFParams) -> int:
    inputs = _input_pair(params, "firfilter")
    output_path = params.output_path(required=True)
    assert output_path is not None
    try:
        firfilter_rsf(
            inputs[0],
            inputs[1],
            output_path,
            axis=params.get_int("axis", 1),
            mode=params.get_string("mode", "same"),
        )
    except (FIRFilterError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        firfilter_command,
        argv,
        prog="python -m pymadagascar.cli.firfilter",
        description="Apply a one-dimensional FIR along an RSF axis.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
