"""CLI for reversing RSF axes."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.generic.reverse import ReverseError, reverse_rsf
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """Reverse parameters:
  input.rsf           Input RSF file.
  out=output.rsf      Output RSF header path.
  axis=1              RSF axis or comma-separated axes to reverse.
  update_header=yes   Update o#/d# so coordinates follow reversed samples.
  opt=i               Madagascar-style alias for update_header=no.

Axis numbers are 1-based RSF axes. Axis 1 is the last NumPy dimension.
"""


def reverse_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output = params.output_path(required=True)
    assert input_path is not None
    assert output is not None

    try:
        reverse_rsf(
            input_path,
            output,
            axis=_axes_from_params(params),
            update_header=_update_header_from_params(params),
        )
    except (ReverseError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def _axes_from_params(params: RSFParams) -> list[int]:
    if params.has("axis"):
        return params.get_list("axis", item_type=int)
    if params.has("axes"):
        return params.get_list("axes", item_type=int)
    if params.has("which"):
        which = params.get_int("which")
        if which < 0:
            raise ParameterParseError("which= bitmask is only supported for non-negative values")
        axes: list[int] = []
        bit = 1
        axis = 1
        while bit <= which:
            if which & bit:
                axes.append(axis)
            bit <<= 1
            axis += 1
        return axes
    return [1]


def _update_header_from_params(params: RSFParams) -> bool:
    if params.has("opt"):
        opt = params.get_string("opt").strip().lower()
        if opt in {"i", "ignore", "noupdate"}:
            return False
        if opt in {"y", "yes", "update"}:
            return True
        raise ParameterParseError("opt= must be y or i in this Python subset")
    return params.get_bool("update_header", default=True)


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        reverse_command,
        argv,
        prog="pymada-reverse",
        description="Reverse one or more axes of an RSF dataset.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
