"""Module-only CLI for two-input cross spectral density."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.cli.convolve import _input_pair
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.signal.spectral import SpectralQCError, csd_rsf


HELP_TEXT = """CSD parameters:
  a.rsf b.rsf             Shape-compatible real-valued input RSF files.
  out=csd.rsf             Complex cross-spectrum output.
  axis=1                  1-based RSF transform axis.
  nfft=                   Optional FFT length.
  window=hann             Standard window kind.
  scaling=density         density or spectrum.

The output convention is conj(FFT(a)) * FFT(b).
"""


def csd_command(params: RSFParams) -> int:
    inputs = _input_pair(params, "csd")
    output_path = params.output_path(required=True)
    assert output_path is not None
    try:
        csd_rsf(
            inputs[0],
            inputs[1],
            output_path,
            axis=params.get_int("axis", 1),
            nfft=params.get_int("nfft") if params.has("nfft") else None,
            window=params.get_string("window", "hann"),
            scaling=params.get_string("scaling", "density"),
        )
    except (SpectralQCError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        csd_command,
        argv,
        prog="python -m pymadagascar.cli.csd",
        description="Compute a two-input cross spectral density.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
