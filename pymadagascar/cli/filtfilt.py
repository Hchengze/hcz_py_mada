"""Module-only CLI for forward/reverse FIR filtering."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.cli.convolve import _input_pair
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.signal.fir import FIRFilterError, filtfilt_rsf


HELP_TEXT = """Forward/reverse FIR parameters:
  input.rsf taps.rsf      Input data and 1D FIR coefficient RSF.
  out=zero_phase.rsf      Shape-preserving output.
  axis=1                  1-based RSF filtering axis.
  pad=y                   Use bounded reflection padding.
"""


def filtfilt_command(params: RSFParams) -> int:
    inputs = _input_pair(params, "filtfilt")
    output_path = params.output_path(required=True)
    assert output_path is not None
    try:
        filtfilt_rsf(
            inputs[0],
            inputs[1],
            output_path,
            axis=params.get_int("axis", 1),
            pad=params.get_bool("pad", True),
        )
    except (FIRFilterError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        filtfilt_command,
        argv,
        prog="python -m pymadagascar.cli.filtfilt",
        description="Apply a forward/reverse zero-phase FIR approximation.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
