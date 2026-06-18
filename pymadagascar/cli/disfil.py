"""Madagascar-style CLI for dumping small RSF arrays as stable text."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.generic.info import DisfilError, disfil_rsf
from pymadagascar.io.rsf import RSFError


def disfil_command(params: RSFParams) -> str:
    path = params.input_path(required=True)
    assert path is not None

    precision = params.get_int("precision", 6)
    axis_format = params.get_string("axis_format", "flat")
    max_values = _get_max_values(params)

    try:
        return disfil_rsf(
            path,
            max_values=max_values,
            precision=precision,
            axis_format=axis_format,  # type: ignore[arg-type]
        )
    except (OSError, RSFError, DisfilError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        disfil_command,
        argv,
        prog="pymada-disfil",
        description="Dump small RSF arrays as deterministic text.",
        help_text=(
            "sfdisfil-inspired subset:\n"
            "  precision=6          Significant digits for float/complex values.\n"
            "  max=1000             Maximum values to print before truncating.\n"
            "  axis_format=flat     flat, multi, rsf, or none.\n"
            "\n"
            "This Python subset uses a stable one-value-per-line format and "
            "does not reproduce original sfdisfil printf columns byte-for-byte."
        ),
    )


def _get_max_values(params: RSFParams) -> int | None:
    if params.has("max"):
        return params.get_int("max")
    if params.has("max_values"):
        return params.get_int("max_values")
    return None


if __name__ == "__main__":
    sys.exit(main())
