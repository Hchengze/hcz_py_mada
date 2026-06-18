"""Module-only CLI for whole-dataset difference metrics."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import MissingParameterError, ParameterParseError, RSFParams
from pymadagascar.generic.difference import DifferenceError, diff_rsf
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """Diff parameters:
  input.rsf match.rsf     Two same-shape RSF datasets.
  out=diff.rsf            One-sample output RSF.
  metric=sum_square       sum_square, rms, or max_abs.

The upstream user/chenyk sfdiff writes the sum of squared differences. The
additional metrics are small pymadagascar QC extensions.
"""


def diff_command(params: RSFParams) -> int:
    if not (params.has("out") or params.has("output") or params.has("--out")):
        raise MissingParameterError("out")
    inputs = _input_pair(params)
    output_path = params.output_path(required=True)
    assert output_path is not None
    try:
        diff_rsf(
            inputs[0],
            inputs[1],
            output_path,
            metric=params.get_string("metric", "sum_square"),
        )
    except (DifferenceError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        diff_command,
        argv,
        prog="python -m pymadagascar.cli.diff",
        description="Compute a scalar difference metric for two RSF datasets.",
        help_text=HELP_TEXT,
    )


def _input_pair(params: RSFParams) -> list[str]:
    inputs: list[str] = []
    input_path = params.params.get("in") or params.params.get("input")
    match_path = params.params.get("match")
    if input_path not in {None, "", "-", "stdin"}:
        inputs.append(str(input_path))
    inputs.extend(params.positionals)
    if match_path not in {None, "", "-", "stdin"}:
        inputs.append(str(match_path))
    if len(inputs) != 2:
        raise ParameterParseError("diff requires exactly two input RSF files")
    return inputs


if __name__ == "__main__":
    sys.exit(main())
