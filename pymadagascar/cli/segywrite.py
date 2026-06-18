"""CLI for converting RSF files to SEG-Y."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.io.segy import SegyError, rsf_to_segy


HELP_TEXT = """segywrite parameters:
  input.rsf          Input RSF file.
  out=output.sgy     Output SEG-Y path.
  endian=big         big, little, or native.
  format=5           SEG-Y sample format: 1, 2, 3, 5, 7, or 8.
  headers=file.csv   Optional CSV input for trace headers.
  textual=file.txt   Optional textual header file or inline text.
"""


def segywrite_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    endian = params.get_string("endian", default="big")
    format_value = params.params.get("format") or params.params.get("sample_format")
    headers = params.params.get("headers") or params.params.get("trace_headers") or params.params.get("tfile")
    textual = params.params.get("textual") or params.params.get("hfile")
    assert input_path is not None
    assert output_path is not None

    try:
        rsf_to_segy(
            input_path,
            output_path,
            endian=endian,
            sample_format=int(format_value) if format_value is not None else None,
            trace_headers=headers,
            textual_header=textual,
        )
    except (SegyError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        segywrite_command,
        argv,
        prog="pymada-segywrite",
        description="Convert an RSF dataset to fixed-length 2D SEG-Y.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
