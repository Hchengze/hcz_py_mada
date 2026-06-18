"""CLI for zero-phase frequency-domain RSF bandpass filtering."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import MissingParameterError, ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.signal.filter import FilterError, bandpass_rsf


HELP_TEXT = """Bandpass parameters:
  input.rsf           Real-valued input RSF file.
  out=output.rsf      Output RSF header path.
  flo=                Low frequency pass edge in cycles per d1 unit.
  fhi=                High frequency pass edge in cycles per d1 unit.
  axis=1              1-based RSF axis to filter.
  taper=0             Cosine taper width in the same frequency unit.
"""


def bandpass_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output = params.output_path(required=True)
    if not params.has("flo"):
        raise MissingParameterError("flo")
    if not params.has("fhi"):
        raise MissingParameterError("fhi")
    axis = params.get_int("axis", default=1)
    taper = params.get_float("taper", default=0.0)
    flo = params.get_float("flo")
    fhi = params.get_float("fhi")
    assert input_path is not None
    assert output is not None

    try:
        bandpass_rsf(input_path, output, flo=flo, fhi=fhi, axis=axis, taper=taper)
    except (FilterError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        bandpass_command,
        argv,
        prog="pymada-bandpass",
        description="Apply a zero-phase FFT bandpass filter to RSF data.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
