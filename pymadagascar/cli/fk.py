"""CLI for 2D FK spectrum analysis."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.seismic.fk import FKError, fk_spectrum


HELP_TEXT = """FK spectrum parameters:
  input.rsf           2D shot gather input RSF file.
  out=fk.rsf          Output RSF header path.
  time_axis=1         1-based RSF time axis.
  space_axis=2        1-based RSF space/offset axis.
  amplitude=yes       Write amplitude spectrum. Use no for complex64 spectrum.
  complex=no          Alias that sets amplitude=no when true.
  norm=               backward, forward, or ortho. Omit for NumPy default.
"""


def fk_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    time_axis = params.get_int("time_axis", default=params.get_int("axis", default=1))
    space_axis = params.get_int("space_axis", default=params.get_int("xaxis", default=2))
    complex_output = params.get_bool("complex", default=False)
    amplitude = params.get_bool("amplitude", default=not complex_output)
    norm = params.get_string("norm", default=None)
    assert input_path is not None
    assert output_path is not None

    try:
        fk_spectrum(
            input_path,
            output_path,
            time_axis=time_axis,
            space_axis=space_axis,
            amplitude=amplitude and not complex_output,
            norm=norm,
        )
    except (FKError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        fk_command,
        argv,
        prog="pymada-fk",
        description="Compute a centered frequency-wavenumber spectrum for a 2D RSF gather.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())

