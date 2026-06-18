"""Madagascar-style CLI for RSF axis transposition."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import MissingParameterError, ParameterParseError, RSFParams
from pymadagascar.generic.transp import TransposeError, transpose_rsf
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """Transpose parameters:
  input.rsf           Input RSF file.
  out=output.rsf      Output RSF header path.
  order=2,1           1-based RSF output axis order.

For example, order=2,1 swaps n1 and n2. RSF n1 is the fastest axis and maps
to the last NumPy dimension internally.
"""


def transp_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.params.get("out") or params.params.get("--out") or params.params.get("output")
    if output_path in {None, "", "-", "stdout"}:
        raise MissingParameterError("out")
    if not params.has("order"):
        raise MissingParameterError("order")
    order = params.get_list("order", item_type=int)
    assert input_path is not None

    try:
        transpose_rsf(input_path, output_path, order)
    except (TransposeError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        transp_command,
        argv,
        prog="pymada-transp",
        description="Transpose RSF axes using a full 1-based axis order.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
