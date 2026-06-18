"""Madagascar-style CLI for RSF dimension reshaping."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import MissingParameterError, ParameterParseError, RSFParams
from pymadagascar.generic.transp import TransposeError, reshape_rsf
from pymadagascar.io.rsf import RSFError, SF_MAX_DIM


HELP_TEXT = """Reshape parameters:
  input.rsf           Input RSF file.
  out=output.rsf      Output RSF header path.
  n1= n2= ...         New RSF dimensions. Total sample count must not change.
"""


def reshape_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.params.get("out") or params.params.get("--out") or params.params.get("output")
    if output_path in {None, "", "-", "stdout"}:
        raise MissingParameterError("out")
    shape = _parse_shape(params)
    assert input_path is not None

    try:
        reshape_rsf(input_path, output_path, shape)
    except (TransposeError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        reshape_command,
        argv,
        prog="pymada-reshape",
        description="Reshape RSF dimensions without changing sample count.",
        help_text=HELP_TEXT,
    )


def _parse_shape(params: RSFParams) -> tuple[int, ...]:
    shape: list[int] = []
    for axis in range(1, SF_MAX_DIM + 1):
        key = f"n{axis}"
        if not params.has(key):
            break
        value = params.get_int(key)
        if value < 1:
            raise ParameterParseError(f"{key}= must be positive")
        shape.append(value)
    if not shape:
        raise MissingParameterError("n1")
    return tuple(shape)


if __name__ == "__main__":
    sys.exit(main())
