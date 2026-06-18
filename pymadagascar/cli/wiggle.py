"""CLI for Matplotlib-based RSF wiggle plots."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError, read_rsf
from pymadagascar.plot._common import PlotError, pyplot
from pymadagascar.plot.wiggle import wiggle


HELP_TEXT = """Wiggle plot parameters:
  input.rsf           Input 2D RSF file.
  out=figure.png      Output .png or .pdf figure.
  title=              Optional title.
  clip=               Symmetric data clip.
  pclip=98            Percentile clip.
  transp=yes/no       Swap display axes.
  scale=0.75          Wiggle trace scale relative to trace spacing.
"""


def wiggle_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output = params.output_path(required=True)
    assert input_path is not None
    assert output is not None

    try:
        rsf = read_rsf(input_path)
        fig = wiggle(
            rsf.data,
            rsf.header,
            output_path=output,
            title=params.get_string("title", default=None),
            clip=params.get_float("clip", default=None),
            pclip=params.get_float("pclip", default=98.0),
            transpose=_get_transpose(params),
            scale=params.get_float("scale", default=0.75),
            fill=params.get_bool("fill", default=True),
        )
        pyplot().close(fig)
    except (PlotError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        wiggle_command,
        argv,
        prog="pymada-wiggle",
        description="Render a 2D RSF panel as wiggle traces with Matplotlib.",
        help_text=HELP_TEXT,
    )


def _get_transpose(params: RSFParams) -> bool:
    if params.has("transp"):
        return params.get_bool("transp")
    return params.get_bool("transpose", default=False)


if __name__ == "__main__":
    sys.exit(main())
