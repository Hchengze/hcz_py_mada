"""Module-only CLI for sorting minimal RSF header tables."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.generic.header_table import HeaderTableError, header_table_sort
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """Headersort parameters:
  headers.rsf             Minimal RSF header table.
  out=sorted.rsf          Output header table path.
  key=offset              Sort rows by one key.
  reverse=n               Sort descending when y.
  stable=y                Use a stable sort by default.

This sorts the header table itself. It does not reorder a separate seismic data
volume and does not handle SEG-Y trace headers.
"""


def headersort_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    key = params.get_string("key")
    reverse = params.get_bool("reverse", False)
    stable = params.get_bool("stable", True)
    assert input_path is not None
    assert output_path is not None

    try:
        header_table_sort(input_path, output_path, key, reverse=reverse, stable=stable)
    except (HeaderTableError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        headersort_command,
        argv,
        prog="python -m pymadagascar.cli.headersort",
        description="Sort a minimal RSF header table by one key.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
