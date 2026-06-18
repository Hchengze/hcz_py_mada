"""Module-only CLI for mask-driven RSF headercut subset."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import MissingParameterError, ParameterParseError, RSFParams
from pymadagascar.generic.header_mask import HeaderMaskError, header_cut_rsf
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """Headercut parameters:
  input.rsf mask.rsf      Input RSF data and one-dimensional mask/header RSF.
  mask=mask.rsf           Mask path alias. header= is also accepted.
  axis=2                  1-based RSF axis selected by the mask.
  cut_nonzero=y           Zero nonzero mask samples; no zeroes zero samples.
  out=output.rsf          Output RSF header path.

This module-only command is a Python mask subset of sfheadercut, not a full
Madagascar header table clone. The output shape and header are preserved.
"""


def headercut_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output = params.output_path(required=True)
    assert input_path is not None
    assert output is not None
    mask = _mask_path(params)
    axis = params.get_int("axis", 2)
    cut_nonzero = params.get_bool("cut_nonzero", True)

    try:
        header_cut_rsf(input_path, mask, output, axis=axis, cut_nonzero=cut_nonzero)
    except (HeaderMaskError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def _mask_path(params: RSFParams) -> str:
    value = params.params.get("mask") or params.params.get("header") or params.params.get("head")
    if value in {None, "", "-", "stdin"}:
        if len(params.positionals) >= 2:
            value = params.positionals[1]
    if value in {None, "", "-", "stdin"}:
        raise MissingParameterError("mask")
    return str(value)


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        headercut_command,
        argv,
        prog="python -m pymadagascar.cli.headercut",
        description="Zero samples in an RSF dataset using a one-dimensional mask/header RSF.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
