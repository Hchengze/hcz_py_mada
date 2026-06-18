"""Module-only CLI for sample-window RMS SNR."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.signal.spectral import SpectralQCError, snr_rsf


HELP_TEXT = """SNR parameters:
  input.rsf               Input RSF signal or trace panel.
  out=snr.rsf             Global or per-trace SNR output.
  axis=1                  1-based RSF sample axis.
  signal=40:120           Optional half-open signal sample window.
  noise=0:30              Half-open noise sample window.
  mode=rms                This subset supports RMS only.
  unit=db                 db or ratio.
  eps=1e-12               Positive noise floor.

If signal= is omitted, the full axis is used as signal. If noise= is omitted,
the complement of signal= is used. At least one window must be supplied.
"""


def snr_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        snr_rsf(
            input_path,
            output_path,
            signal_window=_parse_window(params.get_string("signal")) if params.has("signal") else None,
            noise_window=_parse_window(params.get_string("noise")) if params.has("noise") else None,
            axis=params.get_int("axis", 1),
            mode=params.get_string("mode", "rms"),
            unit=params.get_string("unit", "db"),
            eps=params.get_float("eps", 1e-12),
        )
    except (SpectralQCError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def _parse_window(value: str) -> tuple[int, int]:
    parts = value.split(":")
    if len(parts) != 2:
        raise ParameterParseError("sample windows must use start:stop")
    try:
        return int(parts[0]), int(parts[1])
    except ValueError as exc:
        raise ParameterParseError("sample windows must use integer start:stop") from exc


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        snr_command,
        argv,
        prog="python -m pymadagascar.cli.snr",
        description="Compute sample-window RMS signal-to-noise ratio.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
