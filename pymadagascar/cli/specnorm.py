"""Module-only CLI for frequency-band spectral normalization."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.signal.spectral import SpectralQCError, specnorm_rsf


HELP_TEXT = """Spectral-normalization parameters:
  input.rsf               Real-valued input RSF file.
  out=norm.rsf            Normalized output.
  axis=1                  1-based RSF transform axis.
  mode=unit_rms           unit_rms or unit_max.
  fmin=                   Optional lower frequency bound.
  fmax=                   Optional upper frequency bound.
  eps=1e-12               Positive normalization floor.
"""


def specnorm_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        specnorm_rsf(
            input_path,
            output_path,
            axis=params.get_int("axis", 1),
            mode=params.get_string("mode", "unit_rms"),
            fmin=params.get_float("fmin") if params.has("fmin") else None,
            fmax=params.get_float("fmax") if params.has("fmax") else None,
            eps=params.get_float("eps", 1e-12),
        )
    except (SpectralQCError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        specnorm_command,
        argv,
        prog="python -m pymadagascar.cli.specnorm",
        description="Normalize spectral amplitude in a selected band.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
