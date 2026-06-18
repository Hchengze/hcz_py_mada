"""Module-only CLI for explicit frequency-band energy QC."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.signal.fir import FIRFilterError, bandenergy_rsf


HELP_TEXT = """Band-energy parameters:
  input.rsf              Real-valued input RSF.
  out=bandenergy.rsf     Frequency-band statistic output.
  axis=1                 1-based RSF sample axis.
  bands=5:15,15:30       Comma-separated low:high frequency bands.
  mode=rms               energy, power, or rms.
  average=y              Average statistics over remaining axes.
"""


def bandenergy_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        bandenergy_rsf(
            input_path,
            output_path,
            bands=params.get_string("bands"),
            axis=params.get_int("axis", 1),
            mode=params.get_string("mode", "rms"),
            average=params.get_bool("average", True),
        )
    except (FIRFilterError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        bandenergy_command,
        argv,
        prog="python -m pymadagascar.cli.bandenergy",
        description="Compute explicit frequency-band energy, power, or RMS.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
