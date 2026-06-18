"""Linear top mute for RSF seismic gathers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from pymadagascar.core.hypercube import Hypercube
from pymadagascar.io.rsf import RSFArray, read_rsf, write_rsf

from ._utils import broadcast_axis_values, output_dtype, validate_rsf_axis


class MuteError(ValueError):
    """Raised when mute parameters are invalid."""


def mute_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    t0: float,
    v: float,
    axis: int = 1,
    offset_axis: int = 2,
    taper: float = 0.0,
) -> RSFArray:
    """Apply a linear top mute ``t_mute = t0 + abs(offset) / v``.

    Samples before ``t_mute`` are zeroed. If ``taper`` is positive, a
    sine-squared ramp is applied from ``t_mute`` to ``t_mute + taper``.
    """

    if v <= 0.0:
        raise MuteError("v= must be positive")
    if taper < 0.0:
        raise MuteError("taper= must be non-negative")

    rsf = read_rsf(input_path)
    cube = Hypercube.from_header(rsf.header)
    axis = validate_rsf_axis(axis, cube.ndim)
    if cube.ndim < 2:
        raise MuteError("mute_rsf requires at least two RSF axes")
    offset_axis = validate_rsf_axis(offset_axis, cube.ndim)
    if axis == offset_axis:
        raise MuteError("time axis and offset axis must be different")

    time = broadcast_axis_values(cube.axis(axis).coordinates(), axis=axis, ndim=cube.ndim)
    offset = broadcast_axis_values(cube.axis(offset_axis).coordinates(), axis=offset_axis, ndim=cube.ndim)
    mute_time = t0 + np.abs(offset) / v
    factor = _mute_factor(time, mute_time, taper)
    dtype = output_dtype(rsf.data)
    result = np.asarray(rsf.data, dtype=dtype) * factor
    return write_rsf(output_path, np.ascontiguousarray(result.astype(dtype, copy=False)), rsf.header.copy())


def mutter(
    data: Any,
    *,
    time_axis: int = 1,
    offset_axis: int = 2,
    v: float,
    t0: float = 0.0,
    side: str = "above",
    taper: int = 0,
    time_o: float = 0.0,
    time_d: float = 1.0,
    offset_o: float = 0.0,
    offset_d: float = 1.0,
) -> np.ndarray:
    """Apply a small linear mute subset to a 2D gather.

    ``side='above'`` mutes times before ``t0 + abs(offset) / v``.
    ``side='below'`` mutes times after that boundary. ``taper`` is a
    nonnegative number of time-axis samples.
    """

    array = np.asarray(data)
    if array.ndim != 2:
        raise MuteError("mutter currently requires a 2D gather")
    if not np.issubdtype(array.dtype, np.number):
        raise MuteError("mutter requires numeric data")
    if v <= 0.0:
        raise MuteError("v= must be positive")
    taper_samples = int(taper)
    if taper_samples < 0:
        raise MuteError("taper= must be a nonnegative sample count")
    normalized_side = str(side).strip().lower()
    if normalized_side not in {"above", "below"}:
        raise MuteError("side= must be above or below")

    time_axis = validate_rsf_axis(time_axis, array.ndim)
    offset_axis = validate_rsf_axis(offset_axis, array.ndim)
    if time_axis == offset_axis:
        raise MuteError("time axis and offset axis must be different")
    if float(time_d) == 0.0 or float(offset_d) == 0.0:
        raise MuteError("time_d and offset_d must be nonzero")

    time_size = array.shape[array.ndim - time_axis]
    offset_size = array.shape[array.ndim - offset_axis]
    time_values = float(time_o) + np.arange(time_size, dtype=np.float64) * float(time_d)
    offset_values = float(offset_o) + np.arange(offset_size, dtype=np.float64) * float(offset_d)
    time = broadcast_axis_values(time_values, axis=time_axis, ndim=array.ndim)
    offset = broadcast_axis_values(offset_values, axis=offset_axis, ndim=array.ndim)
    mute_time = float(t0) + np.abs(offset) / float(v)
    factor = _mutter_factor(
        time,
        mute_time,
        side=normalized_side,
        taper_samples=taper_samples,
        time_d=float(time_d),
    )
    dtype = output_dtype(array)
    result = np.asarray(array, dtype=dtype) * factor
    return np.ascontiguousarray(result.astype(dtype, copy=False))


def mutter_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    time_axis: int = 1,
    offset_axis: int = 2,
    v: float,
    t0: float = 0.0,
    side: str = "above",
    taper: int = 0,
) -> RSFArray:
    """Apply the small linear mute subset using regular RSF axis coordinates."""

    rsf = read_rsf(input_path)
    cube = Hypercube.from_header(rsf.header)
    if cube.ndim != 2:
        raise MuteError("mutter_rsf currently requires a 2D gather")
    time_axis = validate_rsf_axis(time_axis, cube.ndim)
    offset_axis = validate_rsf_axis(offset_axis, cube.ndim)
    time_meta = cube.axis(time_axis)
    offset_meta = cube.axis(offset_axis)
    result = mutter(
        rsf.data,
        time_axis=time_axis,
        offset_axis=offset_axis,
        v=v,
        t0=t0,
        side=side,
        taper=taper,
        time_o=time_meta.o,
        time_d=time_meta.d,
        offset_o=offset_meta.o,
        offset_d=offset_meta.d,
    )
    return write_rsf(output_path, result, rsf.header.copy())


def _mute_factor(time: np.ndarray, mute_time: np.ndarray, taper: float) -> np.ndarray:
    if taper == 0.0:
        return np.where(time < mute_time, 0.0, 1.0)
    normalized = (time - mute_time) / taper
    ramp = np.sin(0.5 * np.pi * np.clip(normalized, 0.0, 1.0)) ** 2
    return np.where(time < mute_time, 0.0, np.where(time >= mute_time + taper, 1.0, ramp))


def _mutter_factor(
    time: np.ndarray,
    mute_time: np.ndarray,
    *,
    side: str,
    taper_samples: int,
    time_d: float,
) -> np.ndarray:
    if taper_samples == 0:
        if side == "above":
            return np.where(time < mute_time, 0.0, 1.0)
        return np.where(time > mute_time, 0.0, 1.0)

    duration = taper_samples * abs(time_d)
    if side == "above":
        normalized = (time - mute_time) / duration
    else:
        normalized = (mute_time - time) / duration
    return np.sin(0.5 * np.pi * np.clip(normalized, 0.0, 1.0)) ** 2


__all__ = ["MuteError", "mute_rsf", "mutter", "mutter_rsf"]
