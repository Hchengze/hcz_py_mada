"""Power and exponential gain for RSF seismic gathers."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from pymadagascar.core.hypercube import Hypercube
from pymadagascar.io.rsf import RSFArray, read_rsf, write_rsf

from ._utils import broadcast_axis_values, output_dtype, validate_rsf_axis


class GainError(ValueError):
    """Raised when gain parameters are invalid."""


def gain_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    power: float = 1.0,
    axis: int = 1,
    scale: float = 1.0,
    exp: float = 0.0,
) -> RSFArray:
    """Apply ``scale * (o + (i+1)*d)**power * exp(exp*t)`` gain along an RSF axis."""

    rsf = read_rsf(input_path)
    cube = Hypercube.from_header(rsf.header)
    axis = validate_rsf_axis(axis, cube.ndim)
    axis_obj = cube.axis(axis)
    dtype = output_dtype(rsf.data)
    coordinates = axis_obj.o + axis_obj.d * (np.arange(axis_obj.n, dtype=np.float64) + 1.0)

    if power != 0.0:
        if _has_fractional_power(power) and np.any(coordinates < 0.0):
            raise GainError("fractional power gain is undefined for negative axis coordinates")
        gain = np.power(coordinates, power).astype(np.float64, copy=False)
    else:
        gain = np.ones(axis_obj.n, dtype=np.float64)
    if exp != 0.0:
        gain *= np.exp(exp * coordinates)
    gain *= scale

    result = np.asarray(rsf.data, dtype=dtype) * broadcast_axis_values(gain, axis=axis, ndim=cube.ndim)
    return write_rsf(output_path, np.ascontiguousarray(result.astype(dtype, copy=False)), rsf.header.copy())


def _has_fractional_power(power: float) -> bool:
    return not np.isclose(power, round(power), rtol=0.0, atol=1e-12)
