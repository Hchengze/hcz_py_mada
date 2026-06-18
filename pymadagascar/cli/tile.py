"""CLI for tiling RSF datasets along an existing axis."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import MissingParameterError, ParameterParseError, RSFParams
from pymadagascar.generic.spray import SprayError, tile_rsf
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """Tile parameters:
  input.rsf           Input RSF file.
  out=output.rsf      Output RSF header path.
  axis=2              Existing 1-based RSF axis to tile.
  repeat=             Number of times to repeat the complete axis.
"""


def tile_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output = params.output_path(required=True)
    if not params.has("repeat"):
        raise MissingParameterError("repeat")
    axis = params.get_int("axis", default=2)
    repeat = params.get_int("repeat")
    assert input_path is not None
    assert output is not None

    try:
        tile_rsf(input_path, output, axis=axis, repeat=repeat)
    except (SprayError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        tile_command,
        argv,
        prog="pymada-tile",
        description="Tile a file-backed RSF dataset along an existing axis.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
