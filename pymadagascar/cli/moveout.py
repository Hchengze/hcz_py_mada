"""CLI for spike traces from arbitrary moveout-time tables."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import MissingParameterError, ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.seismic.moveout import MoveoutError, moveout_rsf


HELP_TEXT = """Moveout parameters:
  input.rsf               Moveout-time table.
  out=output.rsf          Output spike-trace RSF header path.
  n1=                     Required output time-sample count.
  o1=0                    Output time origin.
  d1=1                    Output time sampling.
  eps=0.1                 Recorded stretch regularization metadata.
  nw=10                   Recorded wavelet half-length metadata.
  interp=linear           Bounded spike placement: linear or nearest.
"""


def moveout_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    if not params.has("n1"):
        raise MissingParameterError("n1")
    assert input_path is not None
    assert output_path is not None
    try:
        moveout_rsf(
            input_path,
            output_path,
            n1=params.get_int("n1"),
            o1=params.get_float("o1", 0.0),
            d1=params.get_float("d1", 1.0),
            eps=params.get_float("eps", 0.1),
            nw=params.get_int("nw", 10),
            interpolation=params.params.get("interp", params.params.get("interpolation", "linear")),
        )
    except (MoveoutError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        moveout_command,
        argv,
        prog="pymada-moveout",
        description="Generate bounded sfmoveout spike traces from moveout times.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
