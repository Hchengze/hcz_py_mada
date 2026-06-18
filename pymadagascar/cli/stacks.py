"""Module-only CLI for small statistical stacks."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.seismic.stack import StackError, stacks_rsf


HELP_TEXT = """Stacks parameters:
  input.rsf               Input RSF file.
  out=stack.rsf           Output RSF header path.
  axis=1                  1-based RSF axis to stack over.
  statistic=sum           sum, mean, rms, or count_nonzero.
  nonzero=n               For mean/rms, count only nonzero samples.

This is a small statistical stack subset. It is not upstream sfstacks'
constant-velocity NMO stack/velocity-scan workflow.
"""


def stacks_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    statistic = params.get_string("statistic", params.get_string("mode", "sum"))
    try:
        stacks_rsf(
            input_path,
            output_path,
            axis=params.get_int("axis", 1),
            statistic=statistic,
            nonzero=params.get_bool("nonzero", False),
        )
    except (StackError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        stacks_command,
        argv,
        prog="python -m pymadagascar.cli.stacks",
        description="Stack over one RSF axis with a small statistic subset.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
