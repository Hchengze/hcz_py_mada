"""CLI for NumPy-based real-to-complex RSF FFT transforms."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.signal.fft import FFTError, rfft_rsf


HELP_TEXT = """Real FFT parameters:
  input.rsf           Real-valued input RSF file.
  out=output.rsf      Output RSF header path.
  axis=1              1-based RSF axis to transform.
  norm=               backward, forward, or ortho. Omit for NumPy default.

The output is complex64 and stores non-negative frequencies only.
"""


def rfft_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output = params.output_path(required=True)
    axis = params.get_int("axis", default=1)
    norm = params.get_string("norm", default=None)
    assert input_path is not None
    assert output is not None

    try:
        rfft_rsf(input_path, output, axis=axis, norm=norm)
    except (FFTError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        rfft_command,
        argv,
        prog="pymada-rfft",
        description="Compute a real-to-complex FFT of a file-backed RSF dataset.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
