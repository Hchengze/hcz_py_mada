"""Module-only CLI for windowed-sinc FIR design."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.signal.fir import FIRFilterError, firwin_rsf


HELP_TEXT = """FIR design parameters:
  out=fir.rsf             Output 1D coefficient RSF.
  numtaps=101             Positive tap count.
  cutoff=20               One cutoff, or cutoff=5,40 for a band.
  fs=250                  Sampling frequency; omit for Nyquist-normalized cutoffs.
  pass_zero=y             Low/band-stop when y; high/band-pass when n.
  window=hann             hann, hamming, blackman, bartlett, or boxcar.
  scale=y                 Normalize gain in the first pass band.
"""


def firwin_command(params: RSFParams) -> int:
    output_path = params.output_path(required=True)
    assert output_path is not None
    try:
        cutoff = params.get_list("cutoff", item_type=float)
        firwin_rsf(
            output_path,
            numtaps=params.get_int("numtaps", 101),
            cutoff=cutoff[0] if len(cutoff) == 1 else cutoff,
            fs=params.get_float("fs") if params.has("fs") else None,
            pass_zero=params.get_bool("pass_zero", True),
            window=params.get_string("window", "hann"),
            scale=params.get_bool("scale", True),
        )
    except (FIRFilterError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        firwin_command,
        argv,
        prog="python -m pymadagascar.cli.firwin",
        description="Design a small windowed-sinc FIR filter.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
