"""CLI for the 2D acoustic finite-difference modeling prototype."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import MissingParameterError, ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.modeling.acoustic2d import Acoustic2DError, acoustic2d_forward


HELP_TEXT = """Acoustic 2D prototype parameters:
  vel.rsf             2D velocity model, n1=z and n2=x.
  out=shot.rsf        Output shot gather.
  nt= dt=             Number of time samples and time sampling.
  sx= sz=             Source indices in (x,z) sample coordinates.
  fpeak=25            Ricker peak frequency.
  t0=                 Optional Ricker delay; default is 1/fpeak.
  rx=0,1,2            Optional receiver x-index list. Default: all x samples.
  rz=                 Receiver z-index scalar/list. Default: sz.
  nb=20               Simple sponge boundary width.
  snap=snap.rsf       Optional wavefield snapshot output.
  jsnap=10            Snapshot interval in time steps.

This is a teaching/prototype scalar acoustic FD code, not an industrial
high-performance modeling engine.
"""


def acoustic2d_command(params: RSFParams) -> int:
    velocity_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    if velocity_path is None:
        raise MissingParameterError("in")
    if output_path is None:
        raise MissingParameterError("out")
    nt = params.get_int("nt")
    dt = params.get_float("dt")
    sx = params.get_int("sx")
    sz = params.get_int("sz")
    fpeak = params.get_float("fpeak", default=25.0)
    t0 = params.get_float("t0", default=None)
    nb = params.get_int("nb", default=20)
    boundary_strength = params.get_float("boundary_strength", default=0.015)
    snapshot_path = params.params.get("snap") or params.params.get("wfl")
    snapshot_interval = params.get_int("jsnap", default=None) if snapshot_path is not None else None
    receivers = _receiver_argument(params, default_z=sz)

    try:
        acoustic2d_forward(
            velocity_path,
            output_path,
            nt=nt,
            dt=dt,
            sx=sx,
            sz=sz,
            receivers=receivers,
            fpeak=fpeak,
            t0=t0,
            nb=nb,
            boundary_strength=boundary_strength,
            snapshot_interval=snapshot_interval,
            snapshot_path=snapshot_path,
        )
    except (Acoustic2DError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        acoustic2d_command,
        argv,
        prog="pymada-acoustic2d",
        description="Run a small 2D acoustic finite-difference forward model.",
        help_text=HELP_TEXT,
    )


def _receiver_argument(params: RSFParams, *, default_z: int):
    if not params.has("rx"):
        return None
    rx = params.get_list("rx", item_type=int)
    rz = params.get_list("rz", item_type=int, default=[default_z])
    if len(rz) == 1:
        rz = rz * len(rx)
    if len(rx) != len(rz):
        raise ParameterParseError("rx= and rz= must have the same length, or rz= may be a scalar")
    return list(zip(rx, rz))


if __name__ == "__main__":
    sys.exit(main())

