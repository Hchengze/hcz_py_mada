"""CLI for RSF convolution."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.signal.convolution import ConvolutionError, convolve_rsf


HELP_TEXT = """Convolution parameters:
  input.rsf filter.rsf   Input signal and convolution kernel.
  out=output.rsf         Output RSF header path.
  mode=same              full, same, or valid.
  axis=1                 1-based RSF axis to convolve.
  method=auto            auto, direct, or fft.
"""


def conv_command(params: RSFParams) -> int:
    inputs = _input_pair(params, "pymada-conv")
    output = params.output_path(required=True)
    axis = params.get_int("axis", default=1)
    mode = params.get_string("mode", default="same")
    method = params.get_string("method", default="auto")
    assert output is not None

    try:
        convolve_rsf(inputs[0], inputs[1], output, mode=mode, axis=axis, method=method)
    except (ConvolutionError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        conv_command,
        argv,
        prog="pymada-conv",
        description="Convolve file-backed RSF traces along a selected axis.",
        help_text=HELP_TEXT,
    )


def _input_pair(params: RSFParams, prog: str) -> list[str]:
    inputs: list[str] = []
    input_path = params.params.get("in") or params.params.get("input")
    if input_path not in {None, "", "-", "stdin"}:
        inputs.append(input_path)  # type: ignore[arg-type]
    filter_path = params.params.get("filter") or params.params.get("filt") or params.params.get("kernel")
    inputs.extend(params.positionals)
    if filter_path not in {None, "", "-", "stdin"}:
        inputs.append(filter_path)  # type: ignore[arg-type]
    if len(inputs) < 2:
        raise ParameterParseError(f"{prog} requires input and filter RSF files")
    if len(inputs) > 2:
        raise ParameterParseError(f"{prog} accepts exactly two input RSF files")
    return inputs


if __name__ == "__main__":
    sys.exit(main())
