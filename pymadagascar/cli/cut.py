"""CLI for zeroing selected RSF windows."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.generic.cut import CutError, cut_rsf
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """Cut parameters:
  input.rsf           Input RSF file.
  out=output.rsf      Output RSF header path.
  axis=1              RSF axis or comma-separated axes to cut.
  f=0                 Zero-based first sample on selected axis/axes.
  n=                  Number of samples to zero. Defaults to the remaining axis.
  j=1                 Stride.
  f1= n1= j1=         Per-axis aliases for Madagascar-style use.

The output shape and header are preserved; selected samples are set to zero.
"""


def cut_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output = params.output_path(required=True)
    assert input_path is not None
    assert output is not None

    axes = _axes_from_params(params)
    try:
        cut_rsf(
            input_path,
            output,
            axis=axes,
            f=_values_from_params(params, axes, "f", default=0),
            n=_optional_values_from_params(params, axes, "n"),
            j=_values_from_params(params, axes, "j", default=1),
        )
    except (CutError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def _axes_from_params(params: RSFParams) -> list[int]:
    if params.has("axis"):
        return params.get_list("axis", item_type=int)
    if params.has("axes"):
        return params.get_list("axes", item_type=int)
    numbered_axes = sorted({
        int(key[1:])
        for key in params.params
        if len(key) > 1 and key[0] in {"f", "n", "j"} and key[1:].isdigit()
    })
    return numbered_axes if numbered_axes else [1]


def _values_from_params(
    params: RSFParams,
    axes: list[int],
    name: str,
    *,
    default: int,
) -> int | list[int]:
    if params.has(name):
        values = params.get_list(name, item_type=int)
        return values[0] if len(values) == 1 else values
    values = [params.get_int(f"{name}{axis}", default=default) for axis in axes]
    return values[0] if len(values) == 1 else values


def _optional_values_from_params(
    params: RSFParams,
    axes: list[int],
    name: str,
) -> int | list[int] | None:
    if params.has(name):
        values = params.get_list(name, item_type=int)
        return values[0] if len(values) == 1 else values
    if any(params.has(f"{name}{axis}") for axis in axes):
        values = [params.get_int(f"{name}{axis}") for axis in axes]
        return values[0] if len(values) == 1 else values
    return None


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        cut_command,
        argv,
        prog="pymada-cut",
        description="Zero a selected window of an RSF dataset without changing shape.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
