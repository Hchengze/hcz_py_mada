"""CLI for bounded inverse-cosine stack-panel to angle transform."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.seismic.angle import AngleTransformError, cos2ang_rsf


HELP_TEXT = """Cos2Ang parameters:
  input.rsf               Stack panel with an inverse-cosine transform axis.
  out=output.rsf          Output angle-panel RSF header path.
  axis=2                  1-based RSF transform axis to replace with angle.
  na=n_axis               Number of output angles.
  a0=0                    Angle origin in degrees.
  da=90/(n_axis-1)        Angle sampling in degrees.
  fill=0                  Out-of-range fill value.
"""


def cos2ang_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        cos2ang_rsf(
            input_path,
            output_path,
            transform_axis=params.get_int("axis", default=params.get_int("transform_axis", default=2)),
            na=params.get_int("na") if params.has("na") else None,
            a0=params.get_float("a0", 0.0),
            da=params.get_float("da") if params.has("da") else None,
            fill_value=params.get_float("fill", default=params.get_float("fill_value", default=0.0)),
        )
    except (AngleTransformError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        cos2ang_command,
        argv,
        prog="pymada-cos2ang",
        description="Apply bounded sfcos2ang angle-axis resampling.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
