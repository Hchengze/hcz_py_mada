"""Module-only CLI for zero-phase FFT band-stop filtering."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import MissingParameterError, ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.signal.qc import SignalQCError, bandstop_rsf


HELP_TEXT = """Band-stop parameters:
  input.rsf           Real-valued input RSF file.
  out=bandstop.rsf    Output RSF header path.
  fmin=               Lower stop-band edge in cycles per d# unit.
  fmax=               Upper stop-band edge in cycles per d# unit.
  axis=1              1-based RSF axis.
  taper=0             Cosine transition width in frequency units.
"""


def bandstop_command(params: RSFParams) -> int:
    if not params.has("fmin"):
        raise MissingParameterError("fmin")
    if not params.has("fmax"):
        raise MissingParameterError("fmax")
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        bandstop_rsf(
            input_path,
            output_path,
            fmin=params.get_float("fmin"),
            fmax=params.get_float("fmax"),
            axis=params.get_int("axis", 1),
            taper=params.get_float("taper", 0.0),
        )
    except (SignalQCError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        bandstop_command,
        argv,
        prog="python -m pymadagascar.cli.bandstop",
        description="Apply a zero-phase FFT band-stop filter.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
