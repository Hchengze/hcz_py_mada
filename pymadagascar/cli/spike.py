"""Madagascar-style CLI for generating spike RSF datasets."""

from __future__ import annotations

from collections.abc import Sequence
import sys
from typing import Any

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.axis import Axis
from pymadagascar.core.params import MissingParameterError, ParameterParseError, RSFParams
from pymadagascar.generic.spike import spike
from pymadagascar.io.rsf import SF_MAX_DIM, dtype_from_format, write_rsf


HELP_TEXT = """Spike parameters:
  n1= n2= n3=...      Output RSF axis sizes. n1= is required.
  k1= k2= k3=...      1-based spike locations in RSF axis order.
  nsp=                Number of spikes. If omitted, inferred from k#/mag lists.
  mag=                Spike magnitudes; defaults to 1 for each spike.
  o#= d#=             Axis origin and spacing.
  label#= unit#=      Axis label and unit.
  dtype=              NumPy dtype; default float32.
  data_format=        RSF data_format alternative to dtype=.
  out=                Output RSF header path. Required for this file-backed CLI.
"""


def spike_command(params: RSFParams) -> int:
    shape = _parse_shape(params)
    dtype = _parse_dtype(params)
    axes = _parse_axes(params, shape)
    locations, magnitudes = _parse_spikes(params, len(shape))
    output = params.output_path(required=True)

    rsf = spike(
        shape,
        locations=locations,
        magnitudes=magnitudes,
        axes=axes,
        dtype=dtype,
    )
    write_rsf(output, rsf.data, rsf.header)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        spike_command,
        argv,
        prog="pymada-spike",
        description="Generate simple RSF point-spike datasets.",
        help_text=HELP_TEXT,
    )


def _parse_shape(params: RSFParams) -> tuple[int, ...]:
    shape: list[int] = []
    for axis in range(1, SF_MAX_DIM + 1):
        key = f"n{axis}"
        if not params.has(key):
            break
        value = params.get_int(key)
        if value < 1:
            raise ParameterParseError(f"{key}= must be positive")
        shape.append(value)

    if not shape:
        raise MissingParameterError("n1")
    return tuple(shape)


def _parse_dtype(params: RSFParams) -> str:
    if params.has("data_format"):
        return str(dtype_from_format(params.get_string("data_format")))
    return params.get_string("dtype", "float32")


def _parse_axes(params: RSFParams, shape: tuple[int, ...]) -> tuple[Axis, ...]:
    axes: list[Axis] = []
    for index, size in enumerate(shape, start=1):
        axes.append(
            Axis(
                n=size,
                o=params.get_float(f"o{index}", 0.0),
                d=params.get_float(f"d{index}", 0.004 if index == 1 else 0.1),
                label=params.get_string(
                    f"label{index}",
                    "Time" if index == 1 else "Distance",
                ),
                unit=params.get_string(f"unit{index}", "s" if index == 1 else "km"),
                index=index,
            )
        )
    return tuple(axes)


def _parse_spikes(
    params: RSFParams,
    ndim: int,
) -> tuple[list[tuple[int, ...]], list[float] | None]:
    key_lengths = [
        len(params.get_list(f"k{axis}", item_type=int))
        for axis in range(1, ndim + 1)
        if params.has(f"k{axis}")
    ]
    mag_length = len(params.get_list("mag", item_type=float)) if params.has("mag") else 0

    if params.has("nsp"):
        nsp = params.get_int("nsp")
        if nsp < 0:
            raise ParameterParseError("nsp= must be non-negative")
    else:
        nsp = max(key_lengths + ([mag_length] if mag_length else []) + [0])

    if nsp == 0:
        return [], None

    locations_by_axis: list[list[int]] = []
    for axis in range(1, ndim + 1):
        key = f"k{axis}"
        if not params.has(key):
            raise MissingParameterError(key)
        locations_by_axis.append(params.get_list(key, item_type=int, count=nsp))

    locations = [
        tuple(locations_by_axis[axis][spike_index] for axis in range(ndim))
        for spike_index in range(nsp)
    ]
    magnitudes = (
        params.get_list("mag", item_type=float, count=nsp)
        if params.has("mag")
        else None
    )
    return locations, magnitudes


if __name__ == "__main__":
    sys.exit(main())
