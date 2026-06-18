"""Module-only CLI for envelope correlation."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.signal.convolution import ConvolutionError, envcorr_rsf

from .convolve import _input_pair


HELP_TEXT = """Envelope correlation parameters:
  a.rsf b.rsf             Input RSF files; b may be a 1D template.
  out=envcorr.rsf         Output RSF header path.
  axis=1                  1-based RSF axis.
  mode=same               same or full.
  normalize=y             Divide by envelope norms.
  method=auto             auto, direct, or fft.

This computes envelopes first and then cross-correlates them. It is not the
upstream local smoothing/iteration sfenvcorr implementation.
"""


def envcorr_command(params: RSFParams) -> int:
    inputs = _input_pair(params, "envcorr")
    output_path = params.output_path(required=True)
    assert output_path is not None
    try:
        envcorr_rsf(
            inputs[0],
            inputs[1],
            output_path,
            axis=params.get_int("axis", 1),
            mode=params.get_string("mode", "same"),
            normalize=params.get_bool("normalize", True),
            method=params.get_string("method", "auto"),
        )
    except (ConvolutionError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        envcorr_command,
        argv,
        prog="python -m pymadagascar.cli.envcorr",
        description="Correlate analytic-signal envelopes for RSF data.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
