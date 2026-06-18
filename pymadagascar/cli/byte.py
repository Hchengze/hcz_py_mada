"""CLI for Python byte-scaling RSF datasets."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.generic.byte import ByteScaleError, byte_rsf
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """Byte scaling parameters:
  input.rsf           Input real-valued RSF file.
  out=byte.rsf        Output RSF header path.
  clip=1.0            Explicit clip. Signed mode uses [-clip, clip].
  pclip=99            Percentile clip based on finite samples.
  bias=0              Center value for signed mode or lower value for allpos.
  allpos=yes/no       Scale from bias/0 to a positive upper limit.

The output stores integer levels 0..255 as RSF native_int (int32). NaN and
Inf samples do not affect scaling limits and are written as 0.
"""


def byte_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output = params.output_path(required=True)
    assert input_path is not None
    assert output is not None

    try:
        byte_rsf(
            input_path,
            output,
            clip=params.get_float("clip", default=None),
            pclip=params.get_float("pclip", default=None),
            bias=params.get_float("bias", default=None),
            allpos=params.get_bool("allpos", default=False),
        )
    except (ByteScaleError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        byte_command,
        argv,
        prog="pymada-byte",
        description="Scale real RSF amplitudes to integer byte levels.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
