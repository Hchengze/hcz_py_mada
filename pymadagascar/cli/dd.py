"""Madagascar-style CLI for RSF data copying and format conversion."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import MissingParameterError, ParameterParseError, RSFParams
from pymadagascar.generic.dd import (
    DDError,
    convert_dtype_rsf,
    convert_endian_rsf,
    convert_to_ascii_float_rsf,
    copy_rsf,
)
from pymadagascar.io.rsf import RSFError


HELP_TEXT = """dd parameters:
  input.rsf           Input RSF file.
  out=output.rsf      Output RSF header path.
  type=float32        Convert to float32, float64, int32, or complex64.
  endian=big          Write XDR big-endian binary payload.
  endian=little       Write native little-endian payload on little-endian hosts.
  form=ascii          Write the supported ascii_float sidecar subset.
  form=xdr|native     Madagascar-style alias for endian=big|native.
  trunc=yes           Truncate instead of round when converting float to int32.

stdin/stdout streaming and ASCII forms other than ascii_float are not supported yet.
"""


def dd_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None

    type_name = params.params.get("type") or params.params.get("dtype")
    endian = params.params.get("endian")
    form = params.params.get("form")
    trunc = params.get_bool("trunc", default=False)

    try:
        endian = _endian_from_form(form, endian)
        if _is_ascii_form(form):
            if endian is not None:
                raise ParameterParseError("form=ascii cannot be combined with endian=")
            convert_to_ascii_float_rsf(input_path, output_path, type_name, trunc=trunc)
        elif type_name is not None:
            convert_dtype_rsf(input_path, output_path, type_name, trunc=trunc)
            if endian is not None:
                convert_endian_rsf(output_path, output_path, endian)
        elif endian is not None:
            convert_endian_rsf(input_path, output_path, endian)
        else:
            copy_rsf(input_path, output_path)
    except (DDError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        dd_command,
        argv,
        prog="pymada-dd",
        description="Copy and convert RSF binary data formats.",
        help_text=HELP_TEXT,
    )


def _endian_from_form(form: str | None, endian: str | None) -> str | None:
    if form is None:
        return endian
    normalized = form.strip().lower()
    if normalized.startswith("a"):
        return endian
    if normalized.startswith("x"):
        return endian or "big"
    if normalized.startswith("n"):
        return endian or "native"
    raise ParameterParseError("form= must be ascii, native, or xdr")


def _is_ascii_form(form: str | None) -> bool:
    return form is not None and form.strip().lower().startswith("a")


if __name__ == "__main__":
    sys.exit(main())
