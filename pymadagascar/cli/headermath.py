"""Module-only CLI for safe expressions on minimal RSF header tables."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import MissingParameterError, ParameterParseError, RSFParams
from pymadagascar.generic.header_table import HeaderTableError, header_table_math
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """Headermath parameters:
  headers.rsf             Minimal RSF header table.
  out=output.rsf          Output header table path.
  expr=offset*offset      Safe expression using header key variables.
  out_key=offset2         New key name. output= and key= are accepted aliases.
  overwrite=n             Refuse to replace an existing key by default.

Supported expression syntax is the pymadagascar safe math subset: numeric
constants, key variables, + - * / ** (^), parentheses, sin/cos/tan/exp/log/sqrt
and abs. This is not the full Madagascar sfheadermath expression language.
"""


def headermath_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = _output_path(params)
    expression = _expression(params)
    out_key = _out_key(params)
    overwrite = params.get_bool("overwrite", False)
    assert input_path is not None

    try:
        header_table_math(
            input_path,
            output_path,
            expression,
            out_key=out_key,
            overwrite=overwrite,
        )
    except (HeaderTableError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        headermath_command,
        argv,
        prog="python -m pymadagascar.cli.headermath",
        description="Compute a header table key from a safe expression.",
        help_text=HELP_TEXT,
    )


def _output_path(params: RSFParams) -> str:
    value = params.params.get("out") or params.params.get("--out")
    if value is None and len(params.positionals) >= 2:
        value = params.positionals[1]
    if value in {None, "", "-", "stdout"}:
        raise MissingParameterError("out")
    return str(value)


def _expression(params: RSFParams) -> str:
    if params.has("expr"):
        return params.get_string("expr")
    if params.has("expression"):
        return params.get_string("expression")
    raise MissingParameterError("expr")


def _out_key(params: RSFParams) -> str:
    value = (
        params.params.get("out_key")
        or params.params.get("output")
        or params.params.get("key")
    )
    if value in {None, ""}:
        raise MissingParameterError("out_key")
    return str(value)


if __name__ == "__main__":
    sys.exit(main())
