"""CLI for bounded 3-D integer-key trace binning."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import MissingParameterError, ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.seismic.gather import GatherError, intbin3_rsf


HELP_TEXT = """IntBin3 parameters:
  input.rsf                         2D trace table with axes n1=time, n2=trace.
  head=headers.rsf                  Numeric integer-valued header table.
  out=output.rsf                    Output 4D binned RSF header path.
  xkey=0 ykey=1 zkey=2              Zero-based numeric header columns.
  xmin/xmax/ymin/ymax/zmin/zmax=    Optional integer output bounds.

This bounded sfintbin3 subset sorts traces by numeric integer header columns.
It does not implement SEG-Y key-name lookup, mask outputs, or production 3D
survey binning.
"""


def intbin3_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    header_path = params.params.get("head") or params.params.get("headers")
    if header_path in {None, "", "-", "stdin"}:
        raise MissingParameterError("head")
    assert input_path is not None
    assert output_path is not None
    try:
        intbin3_rsf(
            input_path,
            str(header_path),
            output_path,
            xkey=params.get_int("xkey", 0),
            ykey=params.get_int("ykey", 1),
            zkey=params.get_int("zkey", 2),
            xmin=params.get_int("xmin") if params.has("xmin") else None,
            xmax=params.get_int("xmax") if params.has("xmax") else None,
            ymin=params.get_int("ymin") if params.has("ymin") else None,
            ymax=params.get_int("ymax") if params.has("ymax") else None,
            zmin=params.get_int("zmin") if params.has("zmin") else None,
            zmax=params.get_int("zmax") if params.has("zmax") else None,
        )
    except (GatherError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        intbin3_command,
        argv,
        prog="pymada-intbin3",
        description="Apply bounded sfintbin3 integer-key trace sorting.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
