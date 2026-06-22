"""CLI for a bounded source-aligned time-squared warp subset."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.generic.remap import RemapError, t2warp_rsf
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """T2warp parameters:
  input.rsf               Input RSF file.
  out=output.rsf          Output RSF header path.
  axis=1                  1-based RSF axis to warp.
  inv=n                   If y, map squared-time samples back to time.
  pad=                    Output sample count for forward warp.
  fill_value=0.0          Value outside the input coordinate range.

This bounded sft2warp subset uses one-axis linear interpolation for t -> t^2
and inverse t^2 -> t coordinate maps. It does not implement adjoint modes,
stretch regularization, logwarp, streaming, or byte-identical sf_stretch4
behavior.
"""


def t2warp_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        t2warp_rsf(
            input_path,
            output_path,
            axis=params.get_int("axis", 1),
            inverse=params.get_bool("inv", False),
            pad=params.get_int("pad") if params.has("pad") else None,
            fill_value=_fill_value(params),
        )
    except (RemapError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        t2warp_command,
        argv,
        prog="pymada-t2warp",
        description="Apply a bounded one-axis time-squared warp.",
        help_text=HELP_TEXT,
    )


def _fill_value(params: RSFParams) -> float:
    if params.has("fill_value"):
        return params.get_float("fill_value")
    return params.get_float("fill", 0.0)


if __name__ == "__main__":
    sys.exit(main())
