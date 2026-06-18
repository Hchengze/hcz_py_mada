"""Module-only CLI for explicit RSF convolution."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.signal.convolution import ConvolutionError, convolve_rsf


HELP_TEXT = """Convolve parameters:
  data.rsf kernel.rsf     Input data and 1D or compatible kernel.
  out=conv.rsf            Output RSF header path.
  axis=1                  1-based RSF axis.
  mode=same               full, same, or valid.
  method=auto             auto, direct, or fft.

This wraps the existing pymadagascar convolution subset under the clearer
sfconvolve-style module name.
"""


def convolve_command(params: RSFParams) -> int:
    inputs = _input_pair(params, "convolve")
    output_path = params.output_path(required=True)
    assert output_path is not None
    try:
        convolve_rsf(
            inputs[0],
            inputs[1],
            output_path,
            axis=params.get_int("axis", 1),
            mode=params.get_string("mode", "same"),
            method=params.get_string("method", "auto"),
        )
    except (ConvolutionError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        convolve_command,
        argv,
        prog="python -m pymadagascar.cli.convolve",
        description="Convolve file-backed RSF traces along a selected axis.",
        help_text=HELP_TEXT,
    )


def _input_pair(params: RSFParams, name: str) -> list[str]:
    inputs: list[str] = []
    input_path = params.params.get("in") or params.params.get("input")
    if input_path not in {None, "", "-", "stdin"}:
        inputs.append(input_path)  # type: ignore[arg-type]
    kernel_path = params.params.get("kernel") or params.params.get("filter") or params.params.get("filt")
    inputs.extend(params.positionals)
    if kernel_path not in {None, "", "-", "stdin"}:
        inputs.append(kernel_path)  # type: ignore[arg-type]
    if len(inputs) < 2:
        raise ParameterParseError(f"{name} requires data and kernel RSF files")
    if len(inputs) > 2:
        raise ParameterParseError(f"{name} accepts exactly two input RSF files")
    return inputs


if __name__ == "__main__":
    sys.exit(main())
