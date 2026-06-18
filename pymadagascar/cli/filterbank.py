"""Module-only CLI for a small FIR band-pass filter bank."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.signal.fir import FIRFilterError, filterbank_rsf


HELP_TEXT = """FIR filter-bank parameters:
  input.rsf              Real-valued input RSF.
  out=bank.rsf           Output with a new highest RSF band axis.
  axis=1                 1-based RSF filtering axis.
  bands=5:15,15:30       Comma-separated low:high frequency bands.
  numtaps=101            Tap count per band-pass filter.
  window=hann            FIR design window.
"""


def filterbank_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        filterbank_rsf(
            input_path,
            output_path,
            bands=params.get_string("bands"),
            axis=params.get_int("axis", 1),
            numtaps=params.get_int("numtaps", 101),
            window=params.get_string("window", "hann"),
        )
    except (FIRFilterError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        filterbank_command,
        argv,
        prog="python -m pymadagascar.cli.filterbank",
        description="Apply a small windowed-sinc FIR band-pass bank.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
