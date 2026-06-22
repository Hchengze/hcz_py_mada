"""CLI for acoustic impedance to reflectivity conversion."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.seismic.ai2refl import AI2ReflError, ai2refl_rsf


HELP_TEXT = """AI2Refl parameters:
  input.rsf               Acoustic impedance RSF data.
  out=output.rsf          Output reflectivity RSF header path.
  axis=1                  1-based RSF axis for the impedance sequence.
  eps=float32_eps         Denominator stabilizer; defaults to FLT_EPSILON.

This bounded sfai2refl subset computes (ai[i+1]-ai[i])/(ai[i+1]+ai[i]+eps)
along one in-memory RSF axis and sets the last sample on that axis to zero.
"""


def ai2refl_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        ai2refl_rsf(
            input_path,
            output_path,
            axis=params.get_int("axis", 1),
            eps=params.get_float("eps") if params.has("eps") else None,
        )
    except (AI2ReflError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        ai2refl_command,
        argv,
        prog="pymada-ai2refl",
        description="Convert acoustic impedance to bounded sfai2refl reflectivity.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
