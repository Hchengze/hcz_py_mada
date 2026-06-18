"""Module-only CLI for one- or two-sided amplitude clipping."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.signal.conditioning import ConditioningError, clip2_rsf


HELP_TEXT = """Clip2 parameters:
  input.rsf               Input RSF file.
  out=clip.rsf            Output RSF header path.
  min=-1 max=1            Optional lower/upper bounds.
  lower=-1 upper=1        Upstream-style aliases.
  pclip=99                Keep the central percentile range.
  symmetric=n             Use symmetric absolute-amplitude limits.

pclip= cannot be combined with explicit bounds. Complex input is rejected.
"""


def clip2_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    min_value = _optional_float(params, "min", "lower")
    max_value = _optional_float(params, "max", "upper")
    pclip = params.get_float("pclip") if params.has("pclip") else None
    try:
        clip2_rsf(
            input_path,
            output_path,
            min_value=min_value,
            max_value=max_value,
            pclip=pclip,
            symmetric=params.get_bool("symmetric", False),
        )
    except (ConditioningError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        clip2_command,
        argv,
        prog="python -m pymadagascar.cli.clip2",
        description="Clip RSF amplitudes with explicit or percentile bounds.",
        help_text=HELP_TEXT,
    )


def _optional_float(params: RSFParams, primary: str, alias: str) -> float | None:
    if params.has(primary):
        return params.get_float(primary)
    if params.has(alias):
        return params.get_float(alias)
    return None


if __name__ == "__main__":
    sys.exit(main())
