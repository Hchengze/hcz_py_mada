"""Madagascar-style CLI for copying RSF files with header updates."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import MissingParameterError, ParameterParseError, RSFParams
from pymadagascar.generic.put import PutHeaderError, put_header
from pymadagascar.io.rsf import RSFError


_CLI_ONLY_KEYS = {"in", "input", "out", "output", "--out"}


def put_command(params: RSFParams) -> str:
    input_path = params.input_path(required=True)
    output_path = params.output_path()
    if output_path in {None, "", "-", "stdout"}:
        raise MissingParameterError("out")
    updates = {
        key: value
        for key, value in params.params.items()
        if key not in _CLI_ONLY_KEYS
    }
    if not updates:
        raise ParameterParseError("Need at least one header key=value update")
    assert input_path is not None

    try:
        result = put_header(input_path, updates, output_path=output_path)
    except (OSError, RSFError, PutHeaderError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return f"wrote: {result.header_path}"


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        put_command,
        argv,
        prog="pymada-put",
        description="Copy an RSF file while updating header key=value parameters.",
    )


if __name__ == "__main__":
    sys.exit(main())
