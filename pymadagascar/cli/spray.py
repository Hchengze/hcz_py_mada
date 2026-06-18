"""Madagascar-style CLI for spraying RSF datasets along a new axis."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import MissingParameterError, ParameterParseError, RSFParams
from pymadagascar.generic.spray import SprayError, spray_rsf
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """Spray parameters:
  input.rsf           Input RSF file.
  out=output.rsf      Output RSF header path.
  axis=2              1-based RSF position for the new axis.
  n=                  Size of the newly created axis.
  o=0 d=1             Origin and sampling for the new axis.
  label= unit=        Optional label and unit for the new axis.
"""


def spray_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output = params.output_path(required=True)
    if not params.has("n"):
        raise MissingParameterError("n")
    axis = params.get_int("axis", default=2)
    n = params.get_int("n")
    o = params.get_float("o", default=0.0)
    d = params.get_float("d", default=1.0)
    label = params.get_string("label", default=None)
    unit = params.get_string("unit", default=None)
    assert input_path is not None
    assert output is not None

    try:
        spray_rsf(input_path, output, axis=axis, n=n, o=o, d=d, label=label, unit=unit)
    except (SprayError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        spray_command,
        argv,
        prog="pymada-spray",
        description="Insert a new RSF axis and duplicate samples along it.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
