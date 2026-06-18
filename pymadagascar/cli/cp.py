"""Madagascar-style CLI for safe RSF header+sidecar copy."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.generic.file_ops import FileToolError, copy_rsf_dataset
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """cp parameters:
  input.rsf            Input RSF header path.
  out=output.rsf       Output RSF header path.
  overwrite=n          Refuse to replace existing output header or sidecar by default.

This is a file-level sfcp subset: it copies the header and sidecar bytes and
updates in= to the new sidecar. Directories, recursion, streams, and sfmv
removal behavior are not implemented.
"""


def cp_command(params: RSFParams) -> str:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    overwrite = params.get_bool("overwrite", default=False)
    assert input_path is not None
    assert output_path is not None

    try:
        result = copy_rsf_dataset(input_path, output_path, overwrite=overwrite)
    except (FileToolError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc

    return f"header={result.header_path}\nsidecar={result.binary_path}"


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        cp_command,
        argv,
        prog="pymada-cp",
        description="Copy an RSF header and sidecar with a safe Python subset.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
