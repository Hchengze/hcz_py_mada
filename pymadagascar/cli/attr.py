"""Madagascar-style CLI for RSF attribute statistics."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.generic.attr import attr_rsf, format_attr
from pymadagascar.io.rsf import RSFError


def attr_command(params: RSFParams) -> str:
    path = params.input_path(required=True)
    assert path is not None
    try:
        return format_attr(attr_rsf(path))
    except (OSError, RSFError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        attr_command,
        argv,
        prog="pymada-attr",
        description="Display basic RSF data statistics.",
    )


if __name__ == "__main__":
    sys.exit(main())
