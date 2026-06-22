"""CLI for bounded two-dimensional amplitude spectra."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.signal.transforms import TransformError, spectra2_rsf


HELP_TEXT = """Spectra2 parameters:
  input.rsf               Real-valued input RSF file.
  out=output.rsf          Output RSF header path.
  axes=1,2                Time/frequency axis followed by space/wavenumber axis.
  mode=amplitude          amplitude or power.
  all=n                   If y, average spectra over remaining planes.

This bounded sfspectra2 subset computes an in-memory 2-D RFFT/FFT amplitude or
power spectrum. It does not implement streaming, FFTW optimal padding, plotting,
or byte-identical Madagascar FFT rounding.
"""


def spectra2_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        spectra2_rsf(
            input_path,
            output_path,
            axes=tuple(params.get_list("axes", item_type=int, default=[1, 2], count=2)),
            mode=params.get_string("mode", "amplitude"),
            average=params.get_bool("all", False),
        )
    except (TransformError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        spectra2_command,
        argv,
        prog="pymada-spectra2",
        description="Compute a bounded two-dimensional RSF amplitude spectrum.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
