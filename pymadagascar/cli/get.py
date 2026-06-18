"""Madagascar-style CLI for querying RSF header keys."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import MissingParameterError, ParameterParseError, RSFParams
from pymadagascar.generic.info import (
    HeaderCastError,
    HeaderKeyError,
    format_header_values,
    get_header_values,
)
from pymadagascar.io.rsf import RSFError


_VALID_FORMATS = {"raw", "string", "int", "float"}


def get_command(params: RSFParams) -> str:
    path = params.input_path(required=True)
    assert path is not None

    keys: list[str] = []
    if params.has("key"):
        keys.extend(params.get_list("key"))
    if params.has("keys"):
        keys.extend(params.get_list("keys"))
    if len(params.positionals) > 1:
        keys.extend(params.positionals[1:])
    if not keys:
        raise MissingParameterError("key")

    output_format = params.get_string("format", None)
    if output_format is None:
        output_format = params.get_string("cast", "raw")
    output_format = output_format.strip().lower()
    if output_format not in _VALID_FORMATS:
        raise ParameterParseError(
            "format= must be one of raw, string, int, or float"
        )
    parform = params.get_bool("parform", True)

    try:
        if params.has("default"):
            values = get_header_values(
                path,
                keys,
                default=params.get_string("default"),
                cast=output_format,
            )
        else:
            values = get_header_values(path, keys, cast=output_format)
    except (OSError, RSFError, HeaderKeyError, HeaderCastError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return format_header_values(values, parform=parform)


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        get_command,
        argv,
        prog="pymada-get",
        description="Query one or more RSF header keys.",
        help_text=(
            "sfget-compatible subset:\n"
            "  key=n1              Query one key.\n"
            "  key=n1,n2,d1        Query multiple keys in order.\n"
            "  default=value       Use value when a key is missing.\n"
            "  format=raw|string|int|float\n"
            "  parform=y|n         Print key=value lines or values only.\n"
            "\n"
            "This Python subset reads file-backed RSF headers by path and does "
            "not implement original sfget all=y or stdin header-table mode."
        ),
    )


if __name__ == "__main__":
    sys.exit(main())
