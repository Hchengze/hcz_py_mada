"""Module-only CLI for analytic-signal envelopes."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.signal.preprocessing import PreprocessingError, envelope_rsf


HELP_TEXT = """Envelope parameters:
  input.rsf               Real-valued input RSF file.
  out=envelope.rsf        Output RSF header path.
  axis=1                  1-based RSF axis for the Hilbert transform.

This NumPy FFT Hilbert-transform subset outputs envelope amplitude only. It
does not implement upstream hilb=/phase=/order=/ref= phase-rotation modes.
"""


def envelope_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        envelope_rsf(input_path, output_path, axis=params.get_int("axis", 1))
    except (PreprocessingError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        envelope_command,
        argv,
        prog="python -m pymadagascar.cli.envelope",
        description="Compute an analytic-signal envelope for RSF data.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
