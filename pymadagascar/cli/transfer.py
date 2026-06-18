"""Module-only CLI for H1/H2 transfer-function estimation."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.cli.convolve import _input_pair
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.signal.spectral import SpectralQCError, transfer_rsf


HELP_TEXT = """Transfer-function parameters:
  source.rsf response.rsf Shape-compatible real-valued source and response.
  out=transfer.rsf        Complex frequency-response output.
  axis=1                  1-based RSF transform axis.
  nperseg=128             Segment length.
  noverlap=               Segment overlap; default half a segment.
  nfft=                   Optional FFT length, at least nperseg.
  window=hann             Standard window kind.
  method=H1               H1=Pxy/Pxx or H2=Pyy/Pyx.
  eps=1e-12               Positive denominator floor.
"""


def transfer_command(params: RSFParams) -> int:
    inputs = _input_pair(params, "transfer")
    output_path = params.output_path(required=True)
    assert output_path is not None
    try:
        transfer_rsf(
            inputs[0],
            inputs[1],
            output_path,
            axis=params.get_int("axis", 1),
            nperseg=params.get_int("nperseg", 128),
            noverlap=params.get_int("noverlap") if params.has("noverlap") else None,
            window=params.get_string("window", "hann"),
            nfft=params.get_int("nfft") if params.has("nfft") else None,
            method=params.get_string("method", "H1"),
            eps=params.get_float("eps", 1e-12),
        )
    except (SpectralQCError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        transfer_command,
        argv,
        prog="python -m pymadagascar.cli.transfer",
        description="Estimate an H1 or H2 transfer function.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
