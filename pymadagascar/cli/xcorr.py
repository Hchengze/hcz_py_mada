"""CLI for trace autocorrelation."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.signal.convolution import ConvolutionError, xcorr_rsf


HELP_TEXT = """Autocorrelation parameters:
  input.rsf        Input RSF file.
  out=output.rsf   Output RSF header path.
  mode=full        full, same, or valid.
  axis=1           1-based RSF axis to autocorrelate.
  method=auto      auto, direct, or fft.
"""


def xcorr_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output = params.output_path(required=True)
    axis = params.get_int("axis", default=1)
    mode = params.get_string("mode", default="full")
    method = params.get_string("method", default="auto")
    assert input_path is not None
    assert output is not None

    try:
        xcorr_rsf(input_path, output, mode=mode, axis=axis, method=method)
    except (ConvolutionError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        xcorr_command,
        argv,
        prog="pymada-xcorr",
        description="Autocorrelate file-backed RSF traces along a selected axis.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
