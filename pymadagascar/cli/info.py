"""Example RSF info command."""

from __future__ import annotations

from collections.abc import Sequence

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.generic.info import format_info, info_rsf
from pymadagascar.io.rsf import RSFError


def info_command(params: RSFParams) -> str:
    path_text = params.input_path(required=True)
    assert path_text is not None
    try:
        return format_info(info_rsf(path_text))
    except (OSError, RSFError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        info_command,
        argv,
        prog="pymada-info",
        description="Display basic information from an RSF header.",
    )


if __name__ == "__main__":
    raise SystemExit(main())
