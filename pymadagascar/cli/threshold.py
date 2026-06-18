"""Module-only CLI for hard and soft thresholding."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import MissingParameterError, ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.signal.preprocessing import PreprocessingError, threshold_rsf


HELP_TEXT = """Threshold parameters:
  input.rsf               Input RSF file.
  out=output.rsf          Output RSF header path.
  value=0.1               Nonnegative threshold value.
  mode=hard               hard or soft.
  substitute=0.0          Replacement for samples below threshold.

Complex data are thresholded by magnitude. This subset uses explicit value=
instead of the upstream pclip-only sfthreshold interface.
"""


def threshold_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    if not params.has("value"):
        raise MissingParameterError("value")
    assert input_path is not None
    assert output_path is not None

    try:
        threshold_rsf(
            input_path,
            output_path,
            value=params.get_float("value"),
            mode=params.get_string("mode", "hard"),
            substitute=params.get_float("substitute", 0.0),
        )
    except (PreprocessingError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        threshold_command,
        argv,
        prog="python -m pymadagascar.cli.threshold",
        description="Apply hard or soft thresholding to RSF data.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
