"""CLI for small-scale linear/parabolic Radon adjoint transforms."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.seismic.radon import RadonError, linear_radon, parabolic_radon


HELP_TEXT = """Radon parameters:
  input.rsf           2D gather input.
  out=radon.rsf       Output Radon panel.
  pmin= pmax= dp=     Linear slowness axis.
  axis=1              1-based RSF time/tau axis.
  offset_axis=2       1-based RSF offset axis.
  offset=offset.rsf   Optional explicit offset vector.
  parab=no            If yes, use parabolic moveout.
  x0=1                Reference offset for parabolic moveout.
  normalize=no        Divide adjoint output by number of offsets.

This command writes the adjoint transform A^T d, not a sparse or LS inverse.
"""


def radon_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    pmin = params.get_float("pmin")
    pmax = params.get_float("pmax")
    dp = params.get_float("dp")
    axis = params.get_int("axis", default=1)
    offset_axis = params.get_int("offset_axis", default=params.get_int("xaxis", default=2))
    offset = params.params.get("offset")
    parabolic = params.get_bool("parab", default=params.get_string("kind", default="linear").lower() == "parabolic")
    x0 = params.get_float("x0", default=1.0)
    normalize = params.get_bool("normalize", default=False)
    least_squares = params.get_bool("least_squares", default=params.get_bool("ls", default=False))
    assert input_path is not None
    assert output_path is not None

    try:
        if parabolic:
            parabolic_radon(
                input_path,
                output_path,
                qmin=pmin,
                qmax=pmax,
                dq=dp,
                axis=axis,
                offset_axis=offset_axis,
                offset=offset,
                x0=x0,
                least_squares=least_squares,
                normalize=normalize,
            )
        else:
            linear_radon(
                input_path,
                output_path,
                pmin=pmin,
                pmax=pmax,
                dp=dp,
                axis=axis,
                offset_axis=offset_axis,
                offset=offset,
                least_squares=least_squares,
                normalize=normalize,
            )
    except (RadonError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        radon_command,
        argv,
        prog="pymada-radon",
        description="Compute a small-scale adjoint Radon transform of a 2D RSF gather.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())

