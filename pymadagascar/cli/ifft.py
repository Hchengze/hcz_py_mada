"""CLI for NumPy-based inverse RSF FFT transforms."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.signal.fft import FFTError, ifft_rsf


HELP_TEXT = """Inverse FFT parameters:
  input.rsf           Complex input RSF file.
  out=output.rsf      Output RSF header path.
  axis=1              1-based RSF axis to invert.
  norm=               backward, forward, or ortho. Omit for NumPy default.

Input is assumed to use the centered full frequency layout written by
pymada-fft.
"""


def ifft_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output = params.output_path(required=True)
    axis = params.get_int("axis", default=1)
    norm = params.get_string("norm", default=None)
    assert input_path is not None
    assert output is not None

    try:
        ifft_rsf(input_path, output, axis=axis, norm=norm)
    except (FFTError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        ifft_command,
        argv,
        prog="pymada-ifft",
        description="Invert a centered complex FFT of a file-backed RSF dataset.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
