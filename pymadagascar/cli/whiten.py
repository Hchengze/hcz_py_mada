"""Module-only CLI for phase-preserving spectral whitening."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.signal.spectral import SpectralQCError, whiten_rsf


HELP_TEXT = """Spectral-whitening parameters:
  input.rsf               Real-valued input RSF file.
  out=white.rsf           Whitened output.
  axis=1                  1-based RSF transform axis.
  floor=1e-6              Relative spectral-amplitude floor.
  smooth=0                Moving-average spectrum width; 0 disables smoothing.
  phase=preserve          This subset supports phase preservation only.
"""


def whiten_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        whiten_rsf(
            input_path,
            output_path,
            axis=params.get_int("axis", 1),
            floor=params.get_float("floor", 1e-6),
            smooth=params.get_int("smooth", 0),
            phase=params.get_string("phase", "preserve"),
        )
    except (SpectralQCError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        whiten_command,
        argv,
        prog="python -m pymadagascar.cli.whiten",
        description="Apply phase-preserving spectral whitening.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
