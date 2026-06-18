"""Normal moveout correction for RSF CMP gathers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from pymadagascar.core.hypercube import Hypercube
from pymadagascar.io.rsf import RSFArray, read_rsf, write_rsf

from ._utils import numpy_axis, real_output_dtype, validate_rsf_axis


class NMOError(ValueError):
    """Raised when NMO inputs or parameters are invalid."""


VelocityInput = str | Path | float | int | np.ndarray


def nmo_correct(
    input_path: str | Path,
    velocity: VelocityInput,
    output_path: str | Path,
    *,
    axis: int = 1,
    offset_axis: int = 2,
    offset: str | Path | np.ndarray | None = None,
    half: bool = True,
    h0: float = 0.0,
    stretch: float | None = 0.5,
) -> RSFArray:
    """Apply forward NMO correction to a 2D CMP gather or gather volume."""

    rsf = read_rsf(input_path)
    result = _apply_nmo_rsf(
        rsf,
        velocity,
        axis=axis,
        offset_axis=offset_axis,
        offset=offset,
        half=half,
        h0=h0,
        stretch=stretch,
        inverse=False,
    )
    return write_rsf(output_path, result.data, result.header)


def inverse_nmo(
    input_path: str | Path,
    velocity: VelocityInput,
    output_path: str | Path,
    *,
    axis: int = 1,
    offset_axis: int = 2,
    offset: str | Path | np.ndarray | None = None,
    half: bool = True,
    h0: float = 0.0,
    stretch: float | None = 0.5,
) -> RSFArray:
    """Apply inverse NMO, mapping a corrected gather back to offset time."""

    rsf = read_rsf(input_path)
    result = _apply_nmo_rsf(
        rsf,
        velocity,
        axis=axis,
        offset_axis=offset_axis,
        offset=offset,
        half=half,
        h0=h0,
        stretch=stretch,
        inverse=True,
    )
    return write_rsf(output_path, result.data, result.header)


def _apply_nmo_rsf(
    rsf: RSFArray,
    velocity: VelocityInput,
    *,
    axis: int,
    offset_axis: int,
    offset: str | Path | np.ndarray | None,
    half: bool,
    h0: float,
    stretch: float | None,
    inverse: bool,
) -> RSFArray:
    cube = Hypercube.from_header(rsf.header)
    axis = validate_rsf_axis(axis, cube.ndim)
    offset_axis = validate_rsf_axis(offset_axis, cube.ndim)
    if axis == offset_axis:
        raise NMOError("time axis and offset axis must be different")
    if rsf.data.ndim < 2:
        raise NMOError("NMO requires at least a 2D gather")
    if not bool(np.all(np.isfinite(rsf.data))):
        raise NMOError("input gather must contain only finite samples")

    time_axis = cube.axis(axis)
    if not np.isfinite(time_axis.o):
        raise NMOError(f"o{axis}= must be finite")
    if not np.isfinite(time_axis.d) or time_axis.d <= 0.0:
        raise NMOError(f"d{axis}= must be positive")
    if time_axis.n < 2:
        raise NMOError("NMO requires at least two time samples")
    if offset is None:
        regular_offset_axis = cube.axis(offset_axis)
        if not np.isfinite(regular_offset_axis.o):
            raise NMOError(f"o{offset_axis}= must be finite")
        if not np.isfinite(regular_offset_axis.d) or regular_offset_axis.d <= 0.0:
            raise NMOError(
                f"d{offset_axis}= must be positive when offset= is not provided"
            )

    h0_value = _finite_scalar(h0, "h0")
    stretch_value = None
    if stretch is not None:
        stretch_value = _finite_scalar(stretch, "stretch")
        if stretch_value < 0.0:
            raise NMOError("stretch= must be non-negative")

    dtype = real_output_dtype(rsf.data)
    moved, restore_axes = _move_to_offset_time(np.asarray(rsf.data, dtype=dtype), axis, offset_axis)
    gather_shape = moved.shape[:-2]
    nh, nt = moved.shape[-2:]
    gather_count = int(np.prod(gather_shape, dtype=np.int64)) if gather_shape else 1
    gathers = moved.reshape((gather_count, nh, nt))
    time = cube.axis(axis).coordinates()
    offsets = _prepare_offsets(offset, rsf.header, nh, gather_count, offset_axis)
    velocities = _prepare_velocities(velocity, nt, gather_count)

    output = np.empty_like(gathers, dtype=dtype)
    for igather in range(gather_count):
        output[igather] = _apply_nmo_gather(
            gathers[igather],
            time,
            velocities[igather],
            offsets[igather],
            half=half,
            h0=h0_value,
            stretch=stretch_value,
            inverse=inverse,
        )

    moved_output = output.reshape(gather_shape + (nh, nt))
    restored = _restore_from_offset_time(moved_output, restore_axes)
    header = rsf.header.copy()
    header["nmo_half"] = "y" if half else "n"
    header["nmo_h0"] = h0_value
    header["nmo_stretch"] = 0.0 if stretch_value is None else stretch_value
    header["nmo_direction"] = "inverse" if inverse else "forward"
    header["nmo_interpolation"] = "linear"
    header["nmo_offset_source"] = "axis" if offset is None else "explicit"
    return RSFArray(np.ascontiguousarray(restored.astype(dtype, copy=False)), header)


def _apply_nmo_gather(
    gather: np.ndarray,
    time: np.ndarray,
    velocity: np.ndarray,
    offsets: np.ndarray,
    *,
    half: bool,
    h0: float,
    stretch: float | None,
    inverse: bool,
) -> np.ndarray:
    output = np.empty_like(gather)
    for itrace, trace in enumerate(gather):
        if inverse:
            output[itrace] = _inverse_nmo_trace(trace, time, velocity, offsets[itrace], half=half, h0=h0, stretch=stretch)
        else:
            output[itrace] = _nmo_trace(trace, time, velocity, offsets[itrace], half=half, h0=h0, stretch=stretch)
    return output


def _nmo_trace(
    trace: np.ndarray,
    time: np.ndarray,
    velocity: np.ndarray,
    offset: float,
    *,
    half: bool,
    h0: float,
    stretch: float | None,
) -> np.ndarray:
    mapped_time = _nmo_mapped_time(time, velocity, offset, half=half, h0=h0)
    valid = _valid_mapped_time(mapped_time, time)
    valid &= _stretch_mask(mapped_time, time, stretch)
    samples = _interp_trace(trace, time, mapped_time)
    samples[~valid] = 0.0
    return samples.astype(trace.dtype, copy=False)


def _inverse_nmo_trace(
    trace: np.ndarray,
    time: np.ndarray,
    velocity: np.ndarray,
    offset: float,
    *,
    half: bool,
    h0: float,
    stretch: float | None,
) -> np.ndarray:
    mapped_time = _nmo_mapped_time(time, velocity, offset, half=half, h0=h0)
    valid = _valid_mapped_time(mapped_time, time)
    valid &= _stretch_mask(mapped_time, time, stretch)
    if np.count_nonzero(valid) < 2:
        return np.zeros_like(trace)

    coords = mapped_time[valid]
    values = np.asarray(trace, dtype=np.float64)[valid]
    order = np.argsort(coords)
    coords = coords[order]
    values = values[order]
    unique, unique_index = np.unique(coords, return_index=True)
    if unique.size < 2:
        return np.zeros_like(trace)
    restored = np.interp(time, unique, values[unique_index], left=0.0, right=0.0)
    return restored.astype(trace.dtype, copy=False)


def _nmo_mapped_time(
    time: np.ndarray,
    velocity: np.ndarray,
    offset: float,
    *,
    half: bool,
    h0: float,
) -> np.ndarray:
    effective_offset = abs(float(offset)) * (2.0 if half else 1.0)
    reference_offset = abs(float(h0)) * (2.0 if half else 1.0)
    h2 = effective_offset * effective_offset - reference_offset * reference_offset
    if np.any(velocity <= 0.0):
        raise NMOError("velocity values must be positive")
    argument = time * time + h2 / (velocity * velocity)
    mapped = np.full_like(time, np.nan, dtype=np.float64)
    live = argument >= 0.0
    mapped[live] = np.sqrt(argument[live])
    return mapped


def _interp_trace(trace: np.ndarray, time: np.ndarray, mapped_time: np.ndarray) -> np.ndarray:
    safe = np.where(np.isfinite(mapped_time), mapped_time, time[0] - abs(time[1] - time[0]))
    return np.interp(safe, time, np.asarray(trace, dtype=np.float64), left=0.0, right=0.0)


def _valid_mapped_time(mapped_time: np.ndarray, time: np.ndarray) -> np.ndarray:
    return np.isfinite(mapped_time) & (mapped_time >= time[0]) & (mapped_time <= time[-1])


def _stretch_mask(mapped_time: np.ndarray, time: np.ndarray, stretch: float | None) -> np.ndarray:
    if stretch is None or stretch == 0.0:
        return np.ones(mapped_time.shape, dtype=bool)
    sample_coord = (mapped_time - time[0]) / (time[1] - time[0])
    mask = np.ones(sample_coord.shape, dtype=bool)
    delta = np.abs(np.diff(sample_coord))
    previous_live = np.isfinite(sample_coord[:-1]) & (sample_coord[:-1] > 0.0)
    mask[1:] &= ~(previous_live & (delta < stretch))
    return mask


def _move_to_offset_time(data: np.ndarray, axis: int, offset_axis: int) -> tuple[np.ndarray, tuple[int, int]]:
    ndim = data.ndim
    time_np = numpy_axis(axis, ndim)
    offset_np = numpy_axis(offset_axis, ndim)
    moved = np.moveaxis(data, [offset_np, time_np], [-2, -1])
    return moved, (offset_np, time_np)


def _restore_from_offset_time(data: np.ndarray, restore_axes: tuple[int, int]) -> np.ndarray:
    offset_np, time_np = restore_axes
    return np.moveaxis(data, [-2, -1], [offset_np, time_np])


def _prepare_offsets(
    offset: str | Path | np.ndarray | None,
    header: Any,
    nh: int,
    gather_count: int,
    offset_axis: int,
) -> np.ndarray:
    if offset is None:
        values = Hypercube.from_header(header).axis(offset_axis).coordinates()
    elif isinstance(offset, np.ndarray):
        values = np.asarray(offset, dtype=np.float64)
    else:
        values = np.asarray(read_rsf(offset).data, dtype=np.float64)
    reshaped = _reshape_per_gather(values, nh, gather_count, "offset")
    if not bool(np.all(np.isfinite(reshaped))):
        raise NMOError("offset values must be finite")
    return reshaped


def _prepare_velocities(velocity: VelocityInput, nt: int, gather_count: int) -> np.ndarray:
    values: np.ndarray
    if isinstance(velocity, np.ndarray):
        values = np.asarray(velocity, dtype=np.float64)
    elif isinstance(velocity, (int, float)):
        values = np.asarray([float(velocity)], dtype=np.float64)
    else:
        try:
            values = np.asarray([float(str(velocity))], dtype=np.float64)
        except ValueError:
            values = np.asarray(read_rsf(velocity).data, dtype=np.float64)
    reshaped = _reshape_per_gather(values, nt, gather_count, "velocity")
    if not bool(np.all(np.isfinite(reshaped))):
        raise NMOError("velocity values must be finite")
    if bool(np.any(reshaped <= 0.0)):
        raise NMOError("velocity values must be positive")
    return reshaped


def _reshape_per_gather(values: np.ndarray, length: int, gather_count: int, name: str) -> np.ndarray:
    flat = np.asarray(values, dtype=np.float64).reshape(-1)
    if flat.size == 1:
        return np.broadcast_to(np.full(length, flat.item(), dtype=np.float64), (gather_count, length)).copy()
    if flat.size == length:
        return np.broadcast_to(flat, (gather_count, length)).copy()
    if flat.size == gather_count * length:
        return flat.reshape((gather_count, length)).copy()
    raise NMOError(f"{name} data has {flat.size} samples, expected 1, {length}, or {gather_count * length}")


def _finite_scalar(value: float, name: str) -> float:
    result = float(value)
    if not np.isfinite(result):
        raise NMOError(f"{name}= must be finite")
    return result
