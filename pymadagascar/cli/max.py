"""Madagascar-style CLI for RSF maximum statistics."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.generic.stats import StatError, format_stat, max_rsf
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """max parameters:
  input.rsf            Input RSF header path.
  axis=0               Global maximum. Use 1-based RSF axis for axis-wise values.
  nan_policy=propagate propagate or omit.
  complex_policy=reject reject complex input or use abs magnitudes.

Output is deterministic key=value text. Global index is a 0-based NumPy index.
"""


def max_command(params: RSFParams) -> str:
    path = params.input_path(required=True)
    axis = params.get_int("axis", default=0)
    nan_policy = params.params.get("nan_policy") or params.params.get("nan") or "propagate"
    complex_policy = params.get_string("complex_policy", default="reject")
    assert path is not None

    try:
        return format_stat(
            max_rsf(
                path,
                axis=axis,
                nan_policy=nan_policy,
                complex_policy=complex_policy,
            )
        )
    except (StatError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        max_command,
        argv,
        prog="pymada-max",
        description="Report maximum values from an RSF dataset.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
