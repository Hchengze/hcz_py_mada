"""Module-only CLI for magnitude-squared spectral coherence."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.cli.convolve import _input_pair
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.signal.spectral import SpectralQCError, coherence_rsf


HELP_TEXT = """Coherence parameters:
  a.rsf b.rsf             Shape-compatible real-valued input RSF files.
  out=coherence.rsf       Magnitude-squared coherence output.
  axis=1                  1-based RSF transform axis.
  nperseg=                Segment length; default min(256, axis length).
  noverlap=               Segment overlap; default half a segment.
  nfft=                   Optional FFT length, at least nperseg.
  window=hann             Standard window kind.
  eps=1e-12               Positive denominator floor.

This is spectral coherence, not the upstream user/chen local coherence cube.
"""


def coherence_command(params: RSFParams) -> int:
    inputs = _input_pair(params, "coherence")
    output_path = params.output_path(required=True)
    assert output_path is not None
    try:
        coherence_rsf(
            inputs[0],
            inputs[1],
            output_path,
            axis=params.get_int("axis", 1),
            nfft=params.get_int("nfft") if params.has("nfft") else None,
            window=params.get_string("window", "hann"),
            eps=params.get_float("eps", 1e-12),
            nperseg=params.get_int("nperseg") if params.has("nperseg") else None,
            noverlap=params.get_int("noverlap") if params.has("noverlap") else None,
        )
    except (SpectralQCError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        coherence_command,
        argv,
        prog="python -m pymadagascar.cli.coherence",
        description="Compute short-segment magnitude-squared coherence.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
