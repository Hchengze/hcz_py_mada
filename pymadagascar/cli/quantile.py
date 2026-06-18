"""Module-only CLI for global or axis-wise quantiles."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import MissingParameterError, ParameterParseError, RSFParams
from pymadagascar.generic.unary import UnaryMathError, quantile_rsf
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """Quantile parameters:
  input.rsf               Real input RSF file.
  out=quantile.rsf        Output RSF header path.
  q=0.05,0.5,0.95        Required quantiles between 0 and 1.
  axis=0                  0/global or a 1-based RSF axis.
  nan_policy=propagate    propagate or omit.

Global output is 1D. Axis-wise output replaces the selected axis with the q
axis and records exact q values in quantiles= metadata.
"""


def quantile_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    if not params.has("q"):
        raise MissingParameterError("q")
    axis = params.get_int("axis", 0)
    assert input_path is not None
    assert output_path is not None
    try:
        quantile_rsf(
            input_path,
            output_path,
            q=params.get_list("q", item_type=float),
            axis=None if axis == 0 else axis,
            nan_policy=params.get_string("nan_policy", "propagate"),
        )
    except (UnaryMathError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        quantile_command,
        argv,
        prog="python -m pymadagascar.cli.quantile",
        description="Write global or axis-wise RSF quantiles.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
