"""CLI for Matplotlib-based RSF grey plots."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError, read_rsf
from pymadagascar.plot._common import PlotError, pyplot
from pymadagascar.plot.grey import grey


HELP_TEXT = """Grey plot parameters:
  input.rsf           Input RSF file.
  out=figure.png      Output .png or .pdf figure.
  title=              Optional title.
  clip=               Symmetric data clip.
  pclip=99            Percentile clip.
  transp=yes/no       Transpose display axes.
  cmap=gray           Matplotlib colormap.
"""


def grey_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output = params.output_path(required=True)
    assert input_path is not None
    assert output is not None

    try:
        rsf = read_rsf(input_path)
        fig = grey(
            rsf.data,
            rsf.header,
            output_path=output,
            title=params.get_string("title", default=None),
            clip=params.get_float("clip", default=None),
            pclip=params.get_float("pclip", default=99.0),
            transpose=_get_transpose(params),
            cmap=params.get_string("cmap", default="gray"),
        )
        pyplot().close(fig)
    except (PlotError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        grey_command,
        argv,
        prog="pymada-grey",
        description="Render a 2D RSF panel with Matplotlib.",
        help_text=HELP_TEXT,
    )


def _get_transpose(params: RSFParams) -> bool:
    if params.has("transp"):
        return params.get_bool("transp")
    return params.get_bool("transpose", default=False)


if __name__ == "__main__":
    sys.exit(main())
