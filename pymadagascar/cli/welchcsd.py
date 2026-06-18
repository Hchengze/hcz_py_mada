"""Module-only CLI for Welch cross spectral density."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.cli.convolve import _input_pair
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.signal.spectral import SpectralQCError, welchcsd_rsf


HELP_TEXT = """Welch CSD parameters:
  a.rsf b.rsf             Shape-compatible real-valued input RSF files.
  out=welchcsd.rsf        Complex cross-spectrum output.
  axis=1                  1-based RSF transform axis.
  nperseg=128             Segment length.
  noverlap=               Segment overlap; default half a segment.
  nfft=                   Optional FFT length, at least nperseg.
  window=hann             Standard window kind.
  scaling=density         density or spectrum.
  average=y               Average over all non-frequency axes.
"""


def welchcsd_command(params: RSFParams) -> int:
    inputs = _input_pair(params, "welchcsd")
    output_path = params.output_path(required=True)
    assert output_path is not None
    try:
        welchcsd_rsf(
            inputs[0],
            inputs[1],
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
        welchcsd_command,
        argv,
        prog="python -m pymadagascar.cli.welchcsd",
        description="Compute an overlapping-segment Welch CSD.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
