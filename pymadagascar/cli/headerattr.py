"""Module-only CLI for minimal RSF header table statistics."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.generic.header_table import (
    HeaderTableError,
    format_header_table_attr,
    header_table_attr,
)
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """Headerattr parameters:
  headers.rsf             Minimal RSF header table.
  key=offset              Select one key.
  key=offset,cdp          Select multiple keys. keys= is also accepted.

The table is an RSF file with n1=number of keys and n2=number of rows/traces.
Key names come from key1/key2/... or header_keys=. This is not a SEG-Y trace
header reader and does not reproduce the full sfheaderattr text format.
"""


def headerattr_command(params: RSFParams) -> str:
    path = params.input_path(required=True)
    assert path is not None
    keys = params.params.get("key") or params.params.get("keys")
    try:
        return format_header_table_attr(header_table_attr(path, keys=keys))
    except (HeaderTableError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        headerattr_command,
        argv,
        prog="python -m pymadagascar.cli.headerattr",
        description="Display statistics for a minimal RSF header table.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
