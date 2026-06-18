"""Madagascar-style CLI for combining real and imaginary RSF data."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import MissingParameterError, ParameterParseError, RSFParams
from pymadagascar.generic.complex_tools import ComplexToolError, cmplx_rsf
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """sfcmplx-compatible subset:
  real.rsf imag.rsf   Real and imaginary RSF inputs.
  out=complex.rsf     Complex RSF output.

Inputs must be real numeric RSF files with identical shapes. The output header
inherits axis metadata from the real input and writes native_complex data.
"""


def cmplx_command(params: RSFParams) -> int:
    real_path = _real_path(params)
    imag_path = _imag_path(params)
    output_path = _output_path(params)
    try:
        cmplx_rsf(real_path, imag_path, output_path)
    except (ComplexToolError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        cmplx_command,
        argv,
        prog="pymada-cmplx",
        description="Create complex RSF data from real and imaginary parts.",
        help_text=HELP_TEXT,
    )


def _real_path(params: RSFParams) -> str:
    value = params.params.get("real") or params.params.get("in") or params.params.get("input")
    if value is None and params.positionals:
        value = params.positionals[0]
    if value in {None, "", "-", "stdin"}:
        raise MissingParameterError("real")
    return value


def _imag_path(params: RSFParams) -> str:
    value = params.params.get("imag") or params.params.get("imaginary")
    if value is None and len(params.positionals) >= 2:
        value = params.positionals[1]
    if value in {None, "", "-", "stdin"}:
        raise MissingParameterError("imag")
    return value


def _output_path(params: RSFParams) -> str:
    value = params.params.get("out") or params.params.get("--out") or params.params.get("output")
    if value is None and len(params.positionals) >= 3:
        value = params.positionals[2]
    if value in {None, "", "-", "stdout"}:
        raise MissingParameterError("out")
    return value


if __name__ == "__main__":
    sys.exit(main())
