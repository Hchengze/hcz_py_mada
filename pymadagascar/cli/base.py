"""Reusable command runner for Madagascar-style Python commands."""

from __future__ import annotations

from collections.abc import Callable, Sequence
import sys
from typing import Any

from pymadagascar.core.params import ParameterParseError, RSFParams


Command = Callable[[RSFParams], Any]


def open_input(params: RSFParams, *args: Any, **kwargs: Any) -> Any:
    """Proxy for ``RSFParams.open_input`` for command modules."""

    return params.open_input(*args, **kwargs)


def open_output(params: RSFParams, *args: Any, **kwargs: Any) -> Any:
    """Proxy for ``RSFParams.open_output`` for command modules."""

    return params.open_output(*args, **kwargs)


def run_rsf_command(
    command: Command,
    argv: Sequence[str] | None = None,
    *,
    prog: str | None = None,
    description: str | None = None,
    help_text: str | None = None,
    stdin: Any | None = None,
    stdout: Any | None = None,
    stderr: Any | None = None,
) -> int:
    """Run a command with RSF-style parameters and standard error handling."""

    params = RSFParams(
        list(argv) if argv is not None else sys.argv[1:],
        prog=prog,
        stdin=stdin,
        stdout=stdout,
        stderr=stderr,
    )

    if params.help_requested:
        print(params.format_help(description, help_text), file=params.stdout)
        return 0

    try:
        result = command(params)
    except ParameterParseError as exc:
        print(f"{params.prog}: {exc}", file=params.stderr)
        return 2

    if isinstance(result, int):
        return result
    if isinstance(result, bytes):
        stream = getattr(params.stdout, "buffer", params.stdout)
        stream.write(result)
        return 0
    if isinstance(result, str):
        print(result, file=params.stdout)
        return 0
    return 0

