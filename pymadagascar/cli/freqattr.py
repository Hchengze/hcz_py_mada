"""Module-only CLI for dominant, centroid, and bandwidth attributes."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.params import ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFError
from pymadagascar.signal.spectral import SpectralQCError, freqattr_rsf


HELP_TEXT = """Frequency-attribute parameters:
  input.rsf               Real signal or PSD input.
  out=freqattr.rsf        Attribute-table output.
  axis=1                  1-based sample or frequency axis.
  input_kind=signal       signal or psd.
  attrs=dominant,centroid,bandwidth
                           Ordered attribute names.
  fmin=                   Optional lower frequency bound.
  fmax=                   Optional upper frequency bound.

Bandwidth is the PSD-weighted standard deviation around the centroid.
"""


def freqattr_command(params: RSFParams) -> int:
    input_path = params.input_path(required=True)
    output_path = params.output_path(required=True)
    assert input_path is not None
    assert output_path is not None
    try:
        freqattr_rsf(
            input_path,
            output_path,
            axis=params.get_int("axis", 1),
            input_kind=params.get_string("input_kind", "signal"),
            attrs=_parse_attrs(
                params.get_string("attrs", "dominant,centroid,bandwidth")
            ),
            fmin=params.get_float("fmin") if params.has("fmin") else None,
            fmax=params.get_float("fmax") if params.has("fmax") else None,
        )
    except (SpectralQCError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def _parse_attrs(value: str) -> tuple[str, ...]:
    attrs = tuple(item.strip() for item in value.split(",") if item.strip())
    if not attrs:
        raise ParameterParseError("attrs must contain at least one name")
    return attrs


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        freqattr_command,
        argv,
        prog="python -m pymadagascar.cli.freqattr",
        description="Compute compact frequency attributes.",
        help_text=HELP_TEXT,
    )


if __name__ == "__main__":
    sys.exit(main())
