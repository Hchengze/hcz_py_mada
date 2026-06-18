"""CLI for zero-phase frequency-domain RSF highpass filtering."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import MissingParameterError, ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.signal.filter import FilterError, highpass_rsf


HELP_TEXT = """Highpass parameters:
  input.rsf           Real-valued input RSF file.
  out=output.rsf      Output RSF header path.
  fcut=               Frequency pass edge in cycles per d1 unit.
  axis=1              1-based RSF axis to filter.
  taper=0             Cosine taper width in the same frequency unit.
"""


def highpass_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output = params.output_path(required=True)
    if not params.has("fcut"):
        raise MissingParameterError("fcut")
    axis = params.get_int("axis", default=1)
    taper = params.get_float("taper", default=0.0)
    fcut = params.get_float("fcut")
    assert input_path is not None
    assert output is not None

    try:
        highpass_rsf(input_path, output, fcut=fcut, axis=axis, taper=taper)
    except (FilterError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        highpass_command,
        argv,
        prog="pymada-highpass",
        description="Apply a zero-phase FFT highpass filter to RSF data.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
