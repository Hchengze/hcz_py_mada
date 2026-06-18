"""Madagascar-style CLI for RSF windowing."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import MissingParameterError, ParameterParseError, RSFParams
from pymadagascar.generic.window import WindowError, window_rsf
from pymadagascar.io.rsf import RSFError, read_rsf, write_rsf


HELP_TEXT = """Window parameters:
  input.rsf           Input RSF file.
  out=output.rsf      Output RSF header path.
  f#=                 Zero-based first sample on axis #. Negative values count from the end.
  n#=                 Output sample count on axis #.
  j#=                 Stride on axis #; defaults to 1.
  min#= max#=         Coordinate-based window bounds.
  squeeze=            If yes, move singleton axes to the end. Defaults to yes.
"""


def window_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    if input_path in {None, "", "-", "stdin"} or output_path in {None, "", "-", "stdout"}:
        raise ParameterParseError("pymada-window currently requires file-backed input and out=")

    try:
        rsf = read_rsf(input_path)
        result = window_rsf(rsf, params)
        write_rsf(output_path, result.data, result.header)
    except (WindowError, ValueError, RSFError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        window_command,
        argv,
        prog="pymada-window",
        description="Window and decimate file-backed RSF datasets.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
