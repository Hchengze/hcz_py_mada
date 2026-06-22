"""CLI for a bounded source-aligned cosine transform subset."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.signal.transforms import TransformError, cosft_rsf


HELP_TEXT = """Cosft parameters:
  input.rsf               Real-valued input RSF file.
  out=output.rsf          Output RSF header path.
  axis=1                  1-based RSF axis to transform.
  inv=n                   If y, run the inverse transform.
  norm=ortho              Orthonormal DCT normalization.

This bounded sfcosft subset applies a one-axis real DCT-II/DCT-III pair. It is
in-memory and does not implement upstream multi-axis sign# dispatch, streaming,
or byte-identical kiss_fft normalization.
"""


def cosft_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        cosft_rsf(
            input_path,
            output_path,
            axis=params.get_int("axis", 1),
            inverse=params.get_bool("inv", False),
            norm=params.get_string("norm", "ortho"),
        )
    except (TransformError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        cosft_command,
        argv,
        prog="pymada-cosft",
        description="Apply a bounded source-aligned cosine transform.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
