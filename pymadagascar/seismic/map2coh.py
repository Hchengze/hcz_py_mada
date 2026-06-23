"""Map parameter attributes into coherence-like velocity panels."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from pymadagascar.core.hypercube import Hypercube
from pymadagascar.io.rsf import RSFArray, read_rsf, write_rsf
from pymadagascar.seismic._utils import numpy_axis, real_output_dtype, validate_rsf_axis


class Map2CohError(ValueError):
    """Raised when a map-to-coherence request is invalid."""


def map2coh(
    data: Any,
    parameter_map: Any,
    *,
    nv: int,
    v0: float,
    dv: float,
    axis_time: int = 1,
    axis_map: int = 2,
    min2: float | None = None,
    max2: float | None = None,
    o2: float = 0.0,
    d2: float = 1.0,
) -> np.ndarray:
    """Accumulate semblance-like ordinates into a velocity/coherence axis."""

    array = np.asarray(data)
    maps = np.asarray(parameter_map)
    if array.shape != maps.shape:
        raise Map2CohError("input and map arrays must have the same shape")
    if array.ndim < 2:
        raise Map2CohError("map2coh requires at least two dimensions")
    if np.iscomplexobj(array) or np.iscomplexobj(maps):
        raise Map2CohError("map2coh requires real-valued input and map data")
    if not np.issubdtype(array.dtype, np.number) or not np.issubdtype(maps.dtype, np.number):
        raise Map2CohError("map2coh input and map data must be numeric")
    if not np.all(np.isfinite(array)) or not np.all(np.isfinite(maps)):
        raise Map2CohError("map2coh input and map data must be finite")
    time_axis = validate_rsf_axis(axis_time, array.ndim)
    map_axis = validate_rsf_axis(axis_map, array.ndim)
    if time_axis == map_axis:
        raise Map2CohError("axis_time and axis_map must be different")
    velocity_count = int(nv)
    if velocity_count <= 0:
        raise Map2CohError("nv= must be positive")
    velocity_origin = _finite_float(v0, "v0")
    velocity_sampling = _positive_float(dv, "dv")
    map_origin = _finite_float(o2, "o2")
    map_sampling = _positive_float(d2, "d2")

    np_time = numpy_axis(time_axis, array.ndim)
    np_map = numpy_axis(map_axis, array.ndim)
    nt = array.shape[np_time]
    nmap = array.shape[np_map]
    lo = map_origin if min2 is None else max(_finite_float(min2, "min2"), map_origin)
    hi = map_origin + map_sampling * (nmap - 1) if max2 is None else min(
        _finite_float(max2, "max2"),
        map_origin + map_sampling * (nmap - 1),
    )
    if lo > hi:
        raise Map2CohError("min2= must be less than or equal to max2=")
    first = max(0, int(np.floor((lo - map_origin) / map_sampling)))
    last = min(nmap - 1, int(np.ceil((hi - map_origin) / map_sampling)))

    dtype = real_output_dtype(array)
    moved_data = np.moveaxis(np.asarray(array, dtype=np.float64), [np_map, np_time], [-2, -1])
    moved_map = np.moveaxis(np.asarray(maps, dtype=np.float64), [np_map, np_time], [-2, -1])
    leading = moved_data.shape[:-2]
    flat_data = moved_data.reshape((-1, nmap, nt))
    flat_map = moved_map.reshape((-1, nmap, nt))
    output = np.zeros((flat_data.shape[0], velocity_count, nt), dtype=np.float64)

    for panel in range(flat_data.shape[0]):
        for imap in range(first, last + 1):
            velocity_coord = (flat_map[panel, imap] - velocity_origin) / velocity_sampling
            lower = np.floor(velocity_coord).astype(np.int64)
            frac = velocity_coord - lower
            live_lower = (lower >= 0) & (lower < velocity_count)
            t_index = np.arange(nt)
            output[panel, lower[live_lower], t_index[live_lower]] += (
                flat_data[panel, imap, live_lower] * (1.0 - frac[live_lower])
            )
            upper = lower + 1
            live_upper = (upper >= 0) & (upper < velocity_count)
            output[panel, upper[live_upper], t_index[live_upper]] += (
                flat_data[panel, imap, live_upper] * frac[live_upper]
            )

    reshaped = output.reshape(leading + (velocity_count, nt))
    restored = np.moveaxis(reshaped, [-2, -1], [np_map, np_time])
    return np.ascontiguousarray(restored.astype(dtype, copy=False))


def map2coh_rsf(
    input_path: str | Path,
    map_path: str | Path,
    output_path: str | Path,
    *,
    nv: int,
    v0: float,
    dv: float,
    axis_time: int = 1,
    axis_map: int = 2,
    min2: float | None = None,
    max2: float | None = None,
) -> RSFArray:
    """Apply the bounded ``sfmap2coh`` subset to RSF files."""

    rsf = read_rsf(input_path)
    map_rsf = read_rsf(map_path)
    cube = Hypercube.from_header(rsf.header)
    map_axis = validate_rsf_axis(axis_map, cube.ndim)
    axis2 = cube.axis(map_axis)
    result = map2coh(
        rsf.data,
        map_rsf.data,
        nv=nv,
        v0=v0,
        dv=dv,
        axis_time=axis_time,
        axis_map=axis_map,
        min2=min2,
        max2=max2,
        o2=axis2.o,
        d2=axis2.d,
    )
    header = rsf.header.copy()
    header[f"n{map_axis}"] = int(nv)
    header[f"o{map_axis}"] = float(v0)
    header[f"d{map_axis}"] = float(dv)
    header[f"label{map_axis}"] = "Velocity"
    header["map2coh_axis_time"] = axis_time
    header["map2coh_axis_map"] = axis_map
    header["map2coh_source"] = "../src-master/system/seismic/Mmap2coh.c"
    header["map2coh_subset"] = "linear-velocity-axis-accumulator"
    header["map2coh_min2"] = axis2.o if min2 is None else float(min2)
    header["map2coh_max2"] = axis2.o + axis2.d * (axis2.n - 1) if max2 is None else float(max2)
    return write_rsf(output_path, result, header)


def _finite_float(value: float, name: str) -> float:
    result = float(value)
    if not np.isfinite(result):
        raise Map2CohError(f"{name}= must be finite")
    return result


def _positive_float(value: float, name: str) -> float:
    result = _finite_float(value, name)
    if result <= 0.0:
        raise Map2CohError(f"{name}= must be positive")
    return result


__all__ = ["Map2CohError", "map2coh", "map2coh_rsf"]
