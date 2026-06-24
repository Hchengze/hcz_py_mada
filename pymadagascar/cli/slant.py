"""CLI for a bounded sfslant-style adjoint slant stack."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.seismic.radon import RadonError, linear_radon


HELP_TEXT = """Slant parameters:
  input.rsf           2D gather input.
  out=slant.rsf       Output tau-p panel.
  np= p0= dp=         Madagascar-style p-axis definition.
  pmin= pmax= dp=     Alternative p-axis definition.
  axis=1              1-based RSF time/tau axis.
  offset_axis=2       1-based RSF offset axis.
  offset=offset.rsf   Optional explicit offset vector.
  normalize=no        Divide adjoint output by number of offsets.

This command is a bounded source-aligned subset of sfslant
(../src-master/system/seismic/Mslant.c). It applies A^T d only; it does not
implement rho filtering, anti-alias stretch, reference slope p1, or the
modeling direction.
"""


def slant_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    p0 = params.get_float("p0", default=params.get_float("pmin", default=None))
    dp = params.get_float("dp")
    np_count = params.get_int("np", default=None)
    if p0 is None:
        raise ParameterParseError("Missing required parameter: p0= or pmin=")
    if np_count is None:
        pmax = params.get_float("pmax")
    else:
        if np_count <= 0:
            raise ParameterParseError("np= must be positive")
        pmax = p0 + (np_count - 1) * dp
    axis = params.get_int("axis", default=1)
    offset_axis = params.get_int("offset_axis", default=params.get_int("xaxis", default=2))
    offset = params.params.get("offset")
    normalize = params.get_bool("normalize", default=False)
    assert input_path is not None
    assert output_path is not None

    try:
        linear_radon(
            input_path,
            output_path,
            pmin=p0,
            pmax=pmax,
            dp=dp,
            axis=axis,
            offset_axis=offset_axis,
            offset=offset,
            normalize=normalize,
        )
    except (RadonError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        slant_command,
        argv,
        prog="pymada-slant",
        description="Apply a bounded sfslant-style adjoint slant stack.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
