"""Madagascar-style CLI for safe RSF header+sidecar removal."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import MissingParameterError, ParameterParseError, RSFParams
from pymadagascar.generic.file_ops import FileToolError, remove_rsf_dataset
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """rm parameters:
  input.rsf            RSF header path. Multiple positional files are accepted.
  dry_run=y            Report files by default without deleting them.
  confirm=n            Actual deletion requires confirm=y.
  missing_ok=n         Ignore missing header paths.

Use confirm=y to delete. Unix -f/-i/-v flags, directories, recursion, root
paths, and current-directory removal are intentionally unsupported.
"""


def rm_command(params: RSFParams) -> str:
    targets = _targets(params)
    dry_run = params.get_bool("dry_run", default=not params.get_bool("confirm", default=False))
    confirm = params.get_bool("confirm", default=False)
    missing_ok = params.get_bool("missing_ok", default=False)

    lines: list[str] = []
    try:
        for target in targets:
            result = remove_rsf_dataset(
                target,
                dry_run=dry_run,
                confirm=confirm,
                missing_ok=missing_ok,
            )
            verb = "would_remove" if result.dry_run else "removed"
            for path in result.paths:
                lines.append(f"{verb}={path}")
            for path in result.missing:
                lines.append(f"missing={path}")
    except (FileToolError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return "\n".join(lines) if lines else "nothing_selected"


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        rm_command,
        argv,
        prog="pymada-rm",
        description="Remove an RSF header and sidecar with explicit confirmation.",
        help_text=HELP_TEXT,
    )


def _targets(params: RSFParams) -> list[str]:
    targets = list(params.positionals)
    if not targets:
        value = params.params.get("in") or params.params.get("input")
        if value:
            targets.append(value)
    if not targets:
        raise MissingParameterError("in")
    for target in targets:
        if str(target).startswith("-"):
            raise ParameterParseError("Unix rm flags are not supported; use dry_run=, confirm=, missing_ok=")
    return targets


if __name__ == "__main__":
    sys.exit(main())
