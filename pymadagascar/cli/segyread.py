"""CLI for converting SEG-Y files to RSF."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.segy import SegyError, segy_to_rsf


HELP_TEXT = """segyread parameters:
  input.sgy          Input SEG-Y file.
  out=output.rsf     Output RSF header path.
  endian=auto        auto, big, little, or native.
  format=5           Optional SEG-Y sample format override.
  headers=file.csv   Optional CSV output for trace headers.
"""


def segyread_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    endian = params.get_string("endian", default="auto")
    format_value = params.params.get("format") or params.params.get("sample_format")
    headers = params.params.get("headers") or params.params.get("trace_headers") or params.params.get("csv")
    assert input_path is not None
    assert output_path is not None

    try:
        segy_to_rsf(
            input_path,
            output_path,
            endian=endian,
            sample_format=int(format_value) if format_value is not None else None,
            trace_header_csv=headers,
        )
    except (SegyError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        segyread_command,
        argv,
        prog="pymada-segyread",
        description="Convert a fixed-length 2D SEG-Y file to RSF.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
