"""Module-only CLI for integer axis decimation."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import MissingParameterError, ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.signal.qc import SignalQCError, decimate_rsf


HELP_TEXT = """Decimate parameters:
  input.rsf               Numeric input RSF file.
  out=decimated.rsf       Output RSF header path.
  factor=                 Positive integer downsampling factor.
  axis=1                  1-based RSF axis.
  anti_alias=y            Apply a centered moving-average prefilter.
  filter=moving_average   moving_average or none.
"""


def decimate_command(params: RSFParams) -> int:
    if not params.has("factor"):
        raise MissingParameterError("factor")
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        decimate_rsf(
            input_path,
            output_path,
            factor=params.get_int("factor"),
            axis=params.get_int("axis", 1),
            anti_alias=params.get_bool("anti_alias", True),
            filter=params.get_string("filter", "moving_average"),
        )
    except (SignalQCError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        decimate_command,
        argv,
        prog="python -m pymadagascar.cli.decimate",
        description="Downsample one RSF axis by an integer factor.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
