"""CLI for RSF cross-correlation."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.signal.convolution import ConvolutionError, correlate_rsf


HELP_TEXT = """Correlation parameters:
  input1.rsf input2.rsf   Input RSF files.
  out=output.rsf          Output RSF header path.
  mode=full               full, same, or valid.
  axis=1                  1-based RSF axis to correlate.
  method=auto             auto, direct, or fft.
"""


def corr_command(params: RSFParams) -> int:
    inputs = _input_pair(params)
    output = params.output_path(required=True)
    axis = params.get_int("axis", default=1)
    mode = params.get_string("mode", default="full")
    method = params.get_string("method", default="auto")
    assert output is not None

    try:
        correlate_rsf(inputs[0], inputs[1], output, mode=mode, axis=axis, method=method)
    except (ConvolutionError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        corr_command,
        argv,
        prog="pymada-corr",
        description="Cross-correlate file-backed RSF traces along a selected axis.",
        help_text=HELP_TEXT,
    )


def _input_pair(params: RSFParams) -> list[str]:
    inputs: list[str] = []
    input_path = params.params.get("in") or params.params.get("input")
    if input_path not in {None, "", "-", "stdin"}:
        inputs.append(input_path)  # type: ignore[arg-type]
    other = params.params.get("other") or params.params.get("filter") or params.params.get("filt")
    inputs.extend(params.positionals)
    if other not in {None, "", "-", "stdin"}:
        inputs.append(other)  # type: ignore[arg-type]
    if len(inputs) < 2:
        raise ParameterParseError("pymada-corr requires two input RSF files")
    if len(inputs) > 2:
        raise ParameterParseError("pymada-corr accepts exactly two input RSF files")
    return inputs


if __name__ == "__main__":
    sys.exit(main())
