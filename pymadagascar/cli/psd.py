"""Module-only CLI for periodogram power spectral density."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.signal.spectral import SpectralQCError, psd_rsf


HELP_TEXT = """PSD parameters:
  input.rsf               Real-valued input RSF file.
  out=psd.rsf             Output RSF header path.
  axis=1                  1-based RSF transform axis.
  nfft=                   Optional FFT length, at least the input axis length.
  window=hann             Standard window kind.
  average=n               Average over all non-frequency axes.
  scaling=density         density or spectrum.

This is a single-periodogram estimator, not Welch multi-segment averaging.
"""


def psd_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        psd_rsf(
            input_path,
            output_path,
            axis=params.get_int("axis", 1),
            nfft=params.get_int("nfft") if params.has("nfft") else None,
            window=params.get_string("window", "hann"),
            average=params.get_bool("average", False),
            scaling=params.get_string("scaling", "density"),
        )
    except (SpectralQCError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        psd_command,
        argv,
        prog="python -m pymadagascar.cli.psd",
        description="Compute a one-sided periodogram PSD.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
