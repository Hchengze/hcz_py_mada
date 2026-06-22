"""CLI for finite-difference Laplacian RSF datasets."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.generic.laplac import LaplacError, laplac_rsf
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """Laplacian parameters:
  input.rsf           Real-valued input RSF file.
  out=output.rsf      Output RSF header path.
  axis=1,2            Optional comma-separated RSF axes. Default: all axes.
  spacing_from_header=y
                      Use selected d# values as finite-difference spacing.
  boundary=edge       Source-aligned existing-neighbor boundary behavior.

The sign follows Madagascar laplac2_lop: each selected axis contributes
center - neighbor for existing adjacent samples. Shape and header are preserved.
"""


def laplac_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output = params.output_path(required=True)
    assert input_path is not None
    assert output is not None

    try:
        laplac_rsf(
            input_path,
            output,
            axes=_axes_from_params(params),
            spacing_from_header=params.get_bool("spacing_from_header", True),
            boundary=params.get_string("boundary", "edge"),
        )
    except (LaplacError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def _axes_from_params(params: RSFParams) -> list[int] | None:
    if params.has("axis"):
        return params.get_list("axis", item_type=int)
    if params.has("axes"):
        return params.get_list("axes", item_type=int)
    return None


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        laplac_command,
        argv,
        prog="pymada-laplac",
        description="Apply a bounded finite-difference Laplacian to RSF data.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
