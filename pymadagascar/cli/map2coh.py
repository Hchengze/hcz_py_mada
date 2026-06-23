"""CLI for bounded map-to-coherence velocity-panel accumulation."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import MissingParameterError, ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.seismic.map2coh import Map2CohError, map2coh_rsf


HELP_TEXT = """Map2Coh parameters:
  input.rsf               Semblance-like ordinate panel.
  map=map.rsf             Parameter map with the same shape as input.
  out=output.rsf          Output velocity/coherence panel path.
  nv=                     Number of output velocity samples.
  v0=                     Velocity-axis origin.
  dv=                     Velocity-axis sampling.
  axis_time=1             1-based RSF time axis.
  axis_map=2              1-based RSF map/slope axis to replace with velocity.
  min2/max2=              Optional input map-axis coordinate window.
"""


def map2coh_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    map_path = params.params.get("map")
    if map_path in {None, "", "-", "stdin"}:
        raise MissingParameterError("map")
    for required in ("nv", "v0", "dv"):
        if not params.has(required):
            raise MissingParameterError(required)
    assert input_path is not None
    assert output_path is not None
    try:
        map2coh_rsf(
            input_path,
            str(map_path),
            output_path,
            nv=params.get_int("nv"),
            v0=params.get_float("v0"),
            dv=params.get_float("dv"),
            axis_time=params.get_int("axis_time", default=params.get_int("time_axis", default=1)),
            axis_map=params.get_int("axis_map", default=params.get_int("map_axis", default=2)),
            min2=params.get_float("min2") if params.has("min2") else None,
            max2=params.get_float("max2") if params.has("max2") else None,
        )
    except (Map2CohError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        map2coh_command,
        argv,
        prog="pymada-map2coh",
        description="Apply bounded sfmap2coh velocity-axis accumulation.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
