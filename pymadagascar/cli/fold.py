"""CLI for bounded numeric-header foldplot histograms."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.seismic.fold import FoldError, fold_rsf


HELP_TEXT = """Fold parameters:
  input.rsf               2D numeric trace-header table.
  out=output.rsf          Output foldplot RSF header path.
  n1= n2= n3=             Output bin counts.
  o1= o2= o3=             Output bin origins.
  d1= d2= d3=             Output bin spacings.
  col1=0 col2=1 col3=2    Zero-based input table columns.
  label1=offset label2=cdp label3=iline

This bounded sffold subset builds a 3D histogram from numeric header-table
columns. It does not implement Madagascar's SEG-Y header-key lookup layer.
"""


def fold_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        fold_rsf(
            input_path,
            output_path,
            columns=(
                params.get_int("col1", 0),
                params.get_int("col2", 1),
                params.get_int("col3", 2),
            ),
            n=(params.get_int("n1"), params.get_int("n2"), params.get_int("n3")),
            o=(params.get_float("o1"), params.get_float("o2"), params.get_float("o3")),
            d=(params.get_float("d1"), params.get_float("d2"), params.get_float("d3")),
            labels=(
                params.get_string("label1", "offset"),
                params.get_string("label2", "cdp"),
                params.get_string("label3", "iline"),
            ),
        )
    except (FoldError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        fold_command,
        argv,
        prog="pymada-fold",
        description="Build a bounded numeric-header sffold histogram.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
