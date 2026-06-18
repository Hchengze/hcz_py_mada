"""Module-only CLI for Welch power spectral density."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.signal.spectral import SpectralQCError, welch_rsf


HELP_TEXT = """Welch PSD parameters:
  input.rsf               Real-valued input RSF file.
  out=welch.rsf           Output RSF header path.
  axis=1                  1-based RSF transform axis.
  nperseg=128             Segment length.
  noverlap=               Segment overlap; default half a segment.
  nfft=                   Optional FFT length, at least nperseg.
  window=hann             Standard window kind.
  scaling=density         density or spectrum.
  average=y               Average over all non-frequency axes.
"""


def welch_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        welch_rsf(
            input_path,
            output_path,
            axis=params.get_int("axis", 1),
            nperseg=params.get_int("nperseg", 128),
            noverlap=params.get_int("noverlap") if params.has("noverlap") else None,
            window=params.get_string("window", "hann"),
            nfft=params.get_int("nfft") if params.has("nfft") else None,
            scaling=params.get_string("scaling", "density"),
            average=params.get_bool("average", True),
        )
    except (SpectralQCError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        welch_command,
        argv,
        prog="python -m pymadagascar.cli.welch",
        description="Compute an overlapping-segment Welch PSD.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
