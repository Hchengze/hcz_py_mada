"""CLI for small-scale Radon modeling back to offset-time gathers."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError, read_header
from pymadagascar.seismic.radon import RadonError, inverse_linear_radon, inverse_parabolic_radon


HELP_TEXT = """Inverse Radon/modeling parameters:
  input.rsf           Input Radon panel.
  out=output.rsf      Output 2D gather.
  nx= ox= dx=         Output offset axis if not stored in the Radon header.
  offset=offset.rsf   Optional explicit output offset vector.
  axis=1              1-based tau axis.
  p_axis=2            1-based p/q axis.
  parab=no            Force parabolic moveout. Defaults to header radon_kind.
  x0=1                Reference offset for parabolic moveout.
  normalize=no        Divide modeled output by number of p samples.

This command applies A m. It is not a solved least-squares inverse.
"""


def iradon_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    header = read_header(input_path)

    axis = params.get_int("axis", default=1)
    p_axis = params.get_int("p_axis", default=params.get_int("radon_axis", default=2))
    nx = params.get_int("nx", default=None)
    ox = params.get_float("ox", default=None)
    dx = params.get_float("dx", default=None)
    offset = params.params.get("offset")
    if params.has("parab"):
        parabolic = params.get_bool("parab")
    else:
        parabolic = str(header.get("radon_kind", "linear")).lower() == "parabolic"
    x0 = params.get_float("x0", default=float(header.get("radon_x0", 1.0)))
    normalize = params.get_bool("normalize", default=False)
    least_squares = params.get_bool("least_squares", default=params.get_bool("ls", default=False))

    try:
        if parabolic:
            inverse_parabolic_radon(
                input_path,
                output_path,
                nx=nx,
                ox=ox,
                dx=dx,
                offset=offset,
                x0=x0,
                axis=axis,
                p_axis=p_axis,
                least_squares=least_squares,
                normalize=normalize,
            )
        else:
            inverse_linear_radon(
                input_path,
                output_path,
                nx=nx,
                ox=ox,
                dx=dx,
                offset=offset,
                axis=axis,
                p_axis=p_axis,
                least_squares=least_squares,
                normalize=normalize,
            )
    except (RadonError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        iradon_command,
        argv,
        prog="pymada-iradon",
        description="Model a 2D offset-time gather from a Radon panel.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())

