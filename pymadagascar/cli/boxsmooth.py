"""CLI for box smoothing RSF datasets."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.cli.smooth import smooth_rsf_command
from pymadagascar.core.params import RSFParams


HELP_TEXT = """Box smooth parameters:
  input.rsf           Input real-valued RSF file.
  out=output.rsf      Output RSF header path.
  rect=3              Default smoothing radius for all axes.
  rect1=3 rect2=5     Per-axis smoothing radius. rect#=1 is a no-op.
  axis=1,2            Optional comma-separated RSF axes to smooth.
  repeat=1            Number of repeated passes per selected axis.

This Python subset uses centered normalized box kernels of width 2*rect-1 and
edge padding. Shape and header axes are preserved.
"""


def boxsmooth_command(params: RSFParams) -> int:
    return smooth_rsf_command(params, kind="box")


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        boxsmooth_command,
        argv,
        prog="pymada-boxsmooth",
        description="Apply centered box smoothing to a real-valued RSF dataset.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
