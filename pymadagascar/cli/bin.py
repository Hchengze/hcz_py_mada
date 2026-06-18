"""Module-only CLI for small table-to-grid binning."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import MissingParameterError, ParameterParseError, RSFParams
from pymadagascar.generic.sampling import SamplingError, bin_rsf
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """Bin parameters:
  points.rsf              2-D table input, one point per row, columns last.
  out=grid.rsf            Output 2-D grid RSF header path.
  x=0 y=1 value=2         Zero-based table column indices.
  n1=50 o1=0 d1=1         X/output axis 1 grid.
  n2=40 o2=0 d2=1         Y/output axis 2 grid.
  statistic=mean          mean, sum, or count.
  fill=0.0                Empty-bin value.

This subset bins small in-memory point tables. It does not implement upstream
sfbin's separate head= file, fold= output, median, or interpolation modes.
"""


def bin_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    for key in ("n1", "o1", "d1", "n2", "o2", "d2"):
        if not params.has(key):
            raise MissingParameterError(key)
    try:
        bin_rsf(
            input_path,
            output_path,
            x=params.get_int("x", 0),
            y=params.get_int("y", 1),
            value=params.get_int("value", 2),
            n1=params.get_int("n1"),
            o1=params.get_float("o1"),
            d1=params.get_float("d1"),
            n2=params.get_int("n2"),
            o2=params.get_float("o2"),
            d2=params.get_float("d2"),
            statistic=params.get_string("statistic", "mean"),
            fill=params.get_float("fill", 0.0),
        )
    except (SamplingError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        bin_command,
        argv,
        prog="python -m pymadagascar.cli.bin",
        description="Bin a small point table into a 2-D RSF grid.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
