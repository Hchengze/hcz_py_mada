"""Madagascar-style CLI for generating a Ricker wavelet RSF."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import MissingParameterError, ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError, dtype_from_format
from pymadagascar.signal.wavelet import WaveletError, ricker_rsf


HELP_TEXT = """Ricker wavelet parameters:
  out=wavelet.rsf      Output RSF header path. Required.
  f=25                Peak frequency in Hz. frequency= and freq= are aliases.
  dt=0.001            Time sample interval in seconds.
  nt=256              Number of output time samples.
  peak_time=          Time of the central peak in seconds. t0= is an alias.
  amplitude=1         Peak amplitude when peak_time aligns with a sample.
  dtype=float32       NumPy dtype; default float32.
  data_format=        RSF data_format alternative to dtype=.

This is a direct time-domain Ricker generator for local synthetic workflows.
Original Madagascar sfricker estimates a Ricker spectrum from input data, and
sfricker1 convolves traces with a Ricker filter; this command is not a
byte-for-byte replacement for those programs.
"""


def ricker_command(params: RSFParams) -> int:
    output_path = params.output_path(required=True)
    assert output_path is not None

    try:
        ricker_rsf(
            output_path,
            frequency=_parse_frequency(params),
            dt=params.get_float("dt"),
            nt=params.get_int("nt"),
            t0=params.get_float("t0", None),
            peak_time=params.get_float("peak_time", None),
            amplitude=_parse_amplitude(params),
            dtype=_parse_dtype(params),
        )
    except (WaveletError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        ricker_command,
        argv,
        prog="pymada-ricker",
        description="Generate a 1D Ricker wavelet RSF.",
        help_text=HELP_TEXT,
    )


def _parse_frequency(params: RSFParams) -> float:
    for key in ("f", "frequency", "freq"):
        if params.has(key):
            return params.get_float(key)
    raise MissingParameterError("f")


def _parse_amplitude(params: RSFParams) -> float:
    if params.has("amplitude"):
        return params.get_float("amplitude")
    return params.get_float("amp", 1.0)


def _parse_dtype(params: RSFParams) -> str:
    if params.has("data_format"):
        return str(dtype_from_format(params.get_string("data_format")))
    return params.get_string("dtype", "float32")


if __name__ == "__main__":
    sys.exit(main())
