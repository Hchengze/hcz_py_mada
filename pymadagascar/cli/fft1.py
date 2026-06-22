"""CLI for the source-aligned one-axis real/complex FFT subset."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.signal.fft import FFTError
from pymadagascar.signal.transforms import TransformError, fft1_rsf


HELP_TEXT = """FFT1 parameters:
  input.rsf               Input RSF file.
  out=output.rsf          Output RSF header path.
  axis=1                  1-based RSF axis to transform.
  inv=n                   If y, invert complex one-sided spectra to real data.
  norm=                   backward, forward, or ortho. Omit for NumPy default.

This bounded sffft1 subset maps real input to one-sided complex spectra, or
complex one-sided spectra back to real samples when inv=y. It is in-memory and
does not implement streaming, FFTW planning, opt= padding, ot= shift files, or
symmetric Madagascar scaling.
"""


def fft1_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        fft1_rsf(
            input_path,
            output_path,
            axis=params.get_int("axis", 1),
            inverse=params.get_bool("inv", False),
            norm=params.get_string("norm", None),
        )
    except (TransformError, FFTError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        fft1_command,
        argv,
        prog="pymada-fft1",
        description="Run a bounded source-aligned one-axis real/complex FFT.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
