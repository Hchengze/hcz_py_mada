"""Module-only CLI for centered sliding RMS."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import MissingParameterError, ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.signal.qc import SignalQCError, localrms_rsf


HELP_TEXT = """Local-RMS parameters:
  input.rsf           Numeric input RSF file.
  out=localrms.rsf    Output RSF header path.
  rect=               Positive centered window length in samples.
  axis=1              1-based RSF axis.

Boundary windows use only available samples, so shape and axis metadata remain
unchanged.
"""


def localrms_command(params: RSFParams) -> int:
    if not params.has("rect"):
        raise MissingParameterError("rect")
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        localrms_rsf(
            input_path,
            output_path,
            rect=params.get_int("rect"),
            axis=params.get_int("axis", 1),
        )
    except (SignalQCError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        localrms_command,
        argv,
        prog="python -m pymadagascar.cli.localrms",
        description="Compute a centered sliding RMS attribute.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
