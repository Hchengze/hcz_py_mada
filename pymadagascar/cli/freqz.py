"""Module-only CLI for FIR frequency-response diagnostics."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.signal.fir import FIRFilterError, freqz_rsf


HELP_TEXT = """FIR response parameters:
  taps.rsf               Input 1D FIR coefficients.
  out=response.rsf       Frequency-response output.
  fs=                    Sampling frequency; omit for normalized frequency.
  nfft=512               Response FFT size, at least the tap count.
  mode=complex           complex, amplitude, or power.
"""


def freqz_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        freqz_rsf(
            input_path,
            output_path,
            fs=params.get_float("fs") if params.has("fs") else None,
            nfft=params.get_int("nfft", 512),
            mode=params.get_string("mode", "complex"),
        )
    except (FIRFilterError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        freqz_command,
        argv,
        prog="python -m pymadagascar.cli.freqz",
        description="Compute a one-sided FIR frequency response.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
