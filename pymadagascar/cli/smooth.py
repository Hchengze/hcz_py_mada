"""CLI for triangle smoothing RSF datasets."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError, read_header
from pymadagascar.signal.smooth import SmoothError, SmoothKind, smooth_rsf


HELP_TEXT = """Smooth parameters:
  input.rsf           Input real-valued RSF file.
  out=output.rsf      Output RSF header path.
  rect=3              Default smoothing radius for all axes.
  rect1=3 rect2=5     Per-axis smoothing radius. rect#=1 is a no-op.
  axis=1,2            Optional comma-separated RSF axes to smooth.
  repeat=1            Number of repeated passes per selected axis.

This Python subset uses centered normalized triangle kernels and edge padding.
Shape and header axes are preserved.
"""


def smooth_command(params: RSFParams) -> int:
    return smooth_rsf_command(params, kind="triangle")


def smooth_rsf_command(params: RSFParams, *, kind: SmoothKind) -> int:
    input_path = params.input_path(required=True)
    output = params.output_path(required=True)
    assert input_path is not None
    assert output is not None

    try:
        rects = _rects_from_params(params, input_path)
        axes = _axes_from_params(params)
        smooth_rsf(
            input_path,
            output,
            rect=rects,
            axes=axes,
            repeat=params.get_int("repeat", default=1),
            kind=kind,
        )
    except (SmoothError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def _rects_from_params(params: RSFParams, input_path: str) -> dict[int, int]:
    ndim = len(read_header(input_path).dimensions)
    default = params.get_int("rect", default=1)
    rects = {axis: default for axis in range(1, ndim + 1)}
    for axis in range(1, ndim + 1):
        key = f"rect{axis}"
        if params.has(key):
            rects[axis] = params.get_int(key)
    return rects


def _axes_from_params(params: RSFParams) -> list[int] | None:
    if params.has("axis"):
        return params.get_list("axis", item_type=int)
    if params.has("axes"):
        return params.get_list("axes", item_type=int)
    return None


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        smooth_command,
        argv,
        prog="pymada-smooth",
        description="Apply triangle smoothing to a real-valued RSF dataset.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
