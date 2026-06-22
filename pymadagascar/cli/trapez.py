"""CLI for trapezoidal frequency-domain RSF filtering."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.signal.trapez import TrapezError, trapez_rsf


HELP_TEXT = """Trapezoidal filter parameters:
  input.rsf           Real-valued input RSF file.
  out=output.rsf      Output RSF header path.
  axis=1              1-based RSF axis to filter.
  frequency=f1,f2,f3,f4
                      Four frequency corners in cycles per d# unit.
  f1= f2= f3= f4=    Equivalent explicit corner parameters.
  dt=                 Optional sampling interval override; default d#.

The response is zero below f1, sin-squared ramp-up to f2, passband to f3,
sin-squared ramp-down to f4, and zero above f4. Shape/header are preserved.
"""


def trapez_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output = params.output_path(required=True)
    assert input_path is not None
    assert output is not None

    try:
        trapez_rsf(
            input_path,
            output,
            axis=params.get_int("axis", 1),
            frequency=_frequency_from_params(params),
            f1=params.get_float("f1", None),
            f2=params.get_float("f2", None),
            f3=params.get_float("f3", None),
            f4=params.get_float("f4", None),
            dt=params.get_float("dt", None),
        )
    except (TrapezError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def _frequency_from_params(params: RSFParams) -> list[float] | None:
    if not params.has("frequency"):
        return None
    return params.get_list("frequency", item_type=float, count=4)


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        trapez_command,
        argv,
        prog="pymada-trapez",
        description="Apply a bounded trapezoidal frequency filter to RSF data.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
