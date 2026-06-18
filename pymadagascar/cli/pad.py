"""Madagascar-style CLI for padding RSF datasets."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.generic.pad import PadError, pad_rsf
from pymadagascar.io.rsf import RSFError, SF_MAX_DIM


HELP_TEXT = """Pad parameters:
  input.rsf           Input RSF file.
  out=output.rsf      Output RSF header path.
  beg1= end1=         Samples to add before/after axis 1.
  n1= or n1out=       Requested output length for axis 1.
  value=0             Constant fill value. Defaults to zero.

beg#, end#, n#, and n#out use 1-based RSF axis numbers. If n# is provided,
the trailing padding is computed from n#, input n#, and beg#.
"""


def pad_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output = params.output_path(required=True)
    assert input_path is not None
    assert output is not None

    beg: dict[int, int] = {}
    end: dict[int, int] = {}
    n: dict[int, int] = {}
    for axis in range(1, SF_MAX_DIM + 1):
        if params.has(f"beg{axis}"):
            beg[axis] = params.get_int(f"beg{axis}")
        if params.has(f"end{axis}"):
            end[axis] = params.get_int(f"end{axis}")
        if params.has(f"n{axis}out"):
            n[axis] = params.get_int(f"n{axis}out")
        if params.has(f"n{axis}"):
            n[axis] = params.get_int(f"n{axis}")
    value = params.get_float("value", default=0.0)

    try:
        pad_rsf(input_path, output, n=n, beg=beg, end=end, value=value)
    except (PadError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        pad_command,
        argv,
        prog="pymada-pad",
        description="Pad a file-backed RSF dataset with a constant value.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
