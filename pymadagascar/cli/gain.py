"""CLI for seismic power gain."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import MissingParameterError, ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.seismic.gain import GainError, gain_rsf


HELP_TEXT = """Gain parameters:
  input.rsf        Input RSF gather.
  out=output.rsf   Output RSF header path.
  power=1.0        Power gain along the selected axis. tpow= is an alias.
  axis=1           1-based RSF axis, usually time.
  scale=1.0        Constant multiplier.
  exp=0.0          Optional exponential gain exp(exp*t). epow= is an alias.
"""


def gain_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None

    if params.has("power"):
        power = params.get_float("power")
    elif params.has("tpow"):
        power = params.get_float("tpow")
    else:
        raise MissingParameterError("power")
    exp = params.get_float("exp", default=params.get_float("epow", default=0.0))
    scale = params.get_float("scale", default=1.0)
    axis = params.get_int("axis", default=1)

    try:
        gain_rsf(input_path, output_path, power=power, axis=axis, scale=scale, exp=exp)
    except (GainError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        gain_command,
        argv,
        prog="pymada-gain",
        description="Apply power/exponential gain to RSF seismic gathers.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
