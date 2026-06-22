"""CLI for bounded real matrix-vector multiplication."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.generic.array_algebra import ArrayAlgebraError, matmult_rsf
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """Matmult parameters:
  input.rsf mat.rsf       Input vector and 2D matrix RSF files.
  out=output.rsf          Output vector RSF header path.
  adj=n                   If y, apply the adjoint/transposed matrix.

This bounded sfmatmult subset supports real-valued in-memory matrix-vector
multiplication. It does not implement complex, sparse, batched, solver, or
out-of-core behavior.
"""


def matmult_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    mat_path = _matrix_path(params)
    assert input_path is not None
    assert output_path is not None
    try:
        matmult_rsf(
            input_path,
            mat_path,
            output_path,
            adj=params.get_bool("adj", False),
        )
    except (ArrayAlgebraError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def _matrix_path(params: RSFParams) -> str:
    value = params.params.get("mat") or params.params.get("matrix")
    if value not in {None, "", "-", "stdin"}:
        return str(value)
    if len(params.positionals) >= 2:
        return params.positionals[1]
    raise ParameterParseError("matmult requires mat= or a second positional matrix RSF file")


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        matmult_command,
        argv,
        prog="pymada-matmult",
        description="Apply bounded real sfmatmult matrix-vector multiplication.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
