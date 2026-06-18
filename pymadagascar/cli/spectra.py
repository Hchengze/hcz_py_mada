"""Module-only CLI for simple one-sided spectra."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.signal.preprocessing import PreprocessingError, spectra_rsf


HELP_TEXT = """Spectra parameters:
  input.rsf               Real-valued input RSF file.
  out=spectra.rsf         Output RSF header path.
  axis=1                  1-based RSF axis for RFFT.
  mode=amplitude          amplitude or power.
  average=y               Average over all non-frequency axes.

This is a simple NumPy RFFT spectrum for QC. It is not a multi-window spectral
estimator and does not plot the result.
"""


def spectra_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        spectra_rsf(
            input_path,
            output_path,
            axis=params.get_int("axis", 1),
            mode=params.get_string("mode", "amplitude"),
            average=params.get_bool("average", True),
        )
    except (PreprocessingError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        spectra_command,
        argv,
        prog="python -m pymadagascar.cli.spectra",
        description="Compute a simple one-sided RSF spectrum.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
