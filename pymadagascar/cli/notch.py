"""Module-only CLI for narrow zero-phase notch filtering."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import MissingParameterError, ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.signal.qc import SignalQCError, notch_rsf


HELP_TEXT = """Notch parameters:
  input.rsf           Real-valued input RSF file.
  out=notch.rsf       Output RSF header path.
  f0=                 Notch center frequency.
  width=              Total stop-band width.
  q=                  Alternative quality factor, width=f0/q.
  axis=1              1-based RSF axis.
  taper=0             Cosine transition width in frequency units.
"""


def notch_command(params: RSFParams) -> int:
    if not params.has("f0"):
        raise MissingParameterError("f0")
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        notch_rsf(
            input_path,
            output_path,
            f0=params.get_float("f0"),
            width=params.get_float("width") if params.has("width") else None,
            q=params.get_float("q") if params.has("q") else None,
            axis=params.get_int("axis", 1),
            taper=params.get_float("taper", 0.0),
        )
    except (SignalQCError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        notch_command,
        argv,
        prog="python -m pymadagascar.cli.notch",
        description="Apply a narrow zero-phase FFT notch filter.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
