"""Module-only CLI for standard window generation and application."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.signal.spectral import SpectralQCError, windowfunc_rsf


HELP_TEXT = """Window-function parameters:
  out=window.rsf          Output RSF header path.
  n1=128                  Length when generating a 1D window.
  kind=hann               hann, hamming, blackman, bartlett, boxcar, or cosine.
  periodic=n              Generate a periodic window by dropping the last sample.

Application mode:
  input.rsf               Input RSF file.
  apply=y                 Apply the window instead of generating one.
  axis=1                  1-based RSF axis.
  normalize=n             Divide by window mean to preserve coherent gain.
"""


def windowfunc_command(params: RSFParams) -> int:
    input_path = params.input_path()
    output_path = params.output_path(required=True)
    assert output_path is not None
    try:
        windowfunc_rsf(
            input_path,
            output_path,
            n=params.get_int("n1") if params.has("n1") else (
                params.get_int("n") if params.has("n") else None
            ),
            kind=params.get_string("kind", "hann"),
            axis=params.get_int("axis", 1),
            apply=params.get_bool("apply", False),
            periodic=params.get_bool("periodic", False),
            normalize=params.get_bool("normalize", False),
        )
    except (SpectralQCError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        windowfunc_command,
        argv,
        prog="python -m pymadagascar.cli.windowfunc",
        description="Generate or apply a standard NumPy window function.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
