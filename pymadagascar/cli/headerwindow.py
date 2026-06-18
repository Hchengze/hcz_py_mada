"""Module-only CLI for mask-driven RSF headerwindow subset."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import MissingParameterError, ParameterParseError, RSFParams
from pymadagascar.generic.header_mask import HeaderMaskError, header_window_rsf
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """Headerwindow parameters:
  input.rsf mask.rsf      Input RSF data and one-dimensional mask/header RSF.
  mask=mask.rsf           Mask path alias. header= is also accepted.
  axis=2                  1-based RSF axis selected by the mask.
  keep_nonzero=y          Keep nonzero mask samples; no keeps zero samples.
  out=output.rsf          Output RSF header path.

This module-only command is a Python mask subset of sfheaderwindow, not a full
Madagascar header table clone. Non-contiguous selections raise an error.
"""


def headerwindow_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output = params.output_path(required=True)
    assert input_path is not None
    assert output is not None
    mask = _mask_path(params)
    axis = params.get_int("axis", 2)
    keep_nonzero = params.get_bool("keep_nonzero", True)

    try:
        header_window_rsf(input_path, mask, output, axis=axis, keep_nonzero=keep_nonzero)
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
        headerwindow_command,
        argv,
        prog="python -m pymadagascar.cli.headerwindow",
        description="Window an RSF dataset using a one-dimensional mask/header RSF.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
