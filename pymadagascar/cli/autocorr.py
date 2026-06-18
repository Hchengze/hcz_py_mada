"""Module-only CLI for trace autocorrelation."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.signal.convolution import ConvolutionError, autocorr_rsf


HELP_TEXT = """Autocorr parameters:
  input.rsf               Input RSF file.
  out=autocorr.rsf        Output RSF header path.
  axis=1                  1-based RSF axis.
  mode=full               full or same.
  normalize=n             Divide by zero-lag autocorrelation.
  max_lag=50              Optional nonnegative maximum lag in samples.
  method=auto             auto, direct, or fft.

This is an in-memory trace autocorrelation subset, not the upstream helix-filter
sfautocorr lag-file tool.
"""


def autocorr_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        autocorr_rsf(
            input_path,
            output_path,
            axis=params.get_int("axis", 1),
            mode=params.get_string("mode", "full"),
            normalize=params.get_bool("normalize", False),
            max_lag=params.get_int("max_lag") if params.has("max_lag") else None,
            method=params.get_string("method", "auto"),
        )
    except (ConvolutionError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        autocorr_command,
        argv,
        prog="python -m pymadagascar.cli.autocorr",
        description="Autocorrelate RSF traces along a selected axis.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
