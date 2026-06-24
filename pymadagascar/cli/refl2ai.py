"""CLI for reflectivity to acoustic impedance conversion."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import MissingParameterError, ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.seismic.ai2refl import AI2ReflError, refl2ai_rsf


HELP_TEXT = """Refl2AI parameters:
  input.rsf               Reflectivity RSF data.
  out=output.rsf          Output acoustic impedance RSF header path.
  a0=surface.rsf          One-sample-per-trace surface impedance RSF file.
  axis=1                  1-based RSF axis for the reflectivity sequence.

This bounded sfrefl2ai subset follows ../src-master/system/seismic/Mrefl2ai.c:
for each trace, output the current impedance and update a *= (1+r)/(1-r).
"""


def refl2ai_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    if not params.has("a0"):
        raise MissingParameterError("a0")
    assert input_path is not None
    assert output_path is not None
    try:
        refl2ai_rsf(
            input_path,
            params.get_string("a0"),
            output_path,
            axis=params.get_int("axis", 1),
        )
    except (AI2ReflError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        refl2ai_command,
        argv,
        prog="pymada-refl2ai",
        description="Convert reflectivity to acoustic impedance with a0 samples.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
