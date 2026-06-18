"""Module-only CLI for causal cumulative integration."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.signal.calculus import CalculusError, causint_rsf


HELP_TEXT = """Causint parameters:
  input.rsf               Input RSF file.
  out=integrated.rsf      Output RSF header path.
  axis=1                  1-based RSF axis.
  scale_by_d=n            Multiply cumulative sums by input header d#.

This subset implements forward causal integration only. Upstream adj=y
anti-causal adjoint integration is not included.
"""


def causint_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        causint_rsf(
            input_path,
            output_path,
            axis=params.get_int("axis", 1),
            scale_by_d=params.get_bool("scale_by_d", False),
        )
    except (CalculusError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        causint_command,
        argv,
        prog="python -m pymadagascar.cli.causint",
        description="Causally integrate RSF data along one regular axis.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
