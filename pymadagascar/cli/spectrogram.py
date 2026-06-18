"""Module-only CLI for axis-1 short-time spectra."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.signal.spectral import SpectralQCError, spectrogram_rsf


HELP_TEXT = """Spectrogram parameters:
  input.rsf               Real-valued 1D signal or trace panel.
  out=spectrogram.rsf     Output RSF header path.
  axis=1                  This subset currently requires RSF axis 1.
  nperseg=64              Segment length in samples.
  noverlap=               Overlap, default half a segment.
  window=hann             Standard window kind.
  mode=power              magnitude or power.

Output RSF axis 1 is frequency and axis 2 is window-center time.
"""


def spectrogram_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        spectrogram_rsf(
            input_path,
            output_path,
            axis=params.get_int("axis", 1),
            nperseg=params.get_int("nperseg", 64),
            noverlap=params.get_int("noverlap") if params.has("noverlap") else None,
            window=params.get_string("window", "hann"),
            mode=params.get_string("mode", "power"),
        )
    except (SpectralQCError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        spectrogram_command,
        argv,
        prog="python -m pymadagascar.cli.spectrogram",
        description="Compute an axis-1 STFT magnitude or power spectrogram.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
