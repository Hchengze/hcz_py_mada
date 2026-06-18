"""Semblance velocity analysis for RSF CMP gathers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from pymadagascar.core.axis import Axis
from pymadagascar.core.hypercube import Hypercube
from pymadagascar.io.rsf import RSFArray, read_rsf, write_rsf

from .nmo import (
    NMOError,
    _apply_nmo_gather,
    _move_to_offset_time,
    _prepare_offsets,
)
from ._utils import real_output_dtype, validate_rsf_axis


class SemblanceError(ValueError):
    """Raised when semblance scan parameters are invalid."""


def semblance_scan(
    input_path: str | Path,
    output_path: str | Path,
    *,
    vmin: float,
    vmax: float,
    dv: float,
    axis: int = 1,
    offset_axis: int = 2,
    offset: str | Path | np.ndarray | None = None,
    half: bool = True,
    h0: float = 0.0,
    stretch: float | None = 0.5,
    smooth: int = 0,
) -> RSFArray:
    """Compute a velocity semblance panel from a CMP gather.

    The output RSF axes are ``n1=time`` and ``n2=velocity``. Extra gather axes
    from the input are preserved after the velocity axis.
    """

    velocities = _velocity_samples(vmin, vmax, dv)
    h0_value = _finite_scalar(h0, "h0")
    stretch_value = _stretch_value(stretch)
    smooth_value = _nonnegative_int(smooth, "smooth")

    rsf = read_rsf(input_path)
    cube = Hypercube.from_header(rsf.header)
    try:
        axis = validate_rsf_axis(axis, cube.ndim)
        offset_axis = validate_rsf_axis(offset_axis, cube.ndim)
    except ValueError as exc:
        raise SemblanceError(str(exc)) from exc
    if axis == offset_axis:
        raise SemblanceError("time axis and offset axis must be different")
    _validate_gather_contract(rsf, cube, axis=axis, offset_axis=offset_axis, offset=offset)

    try:
        dtype = real_output_dtype(rsf.data)
    except ValueError as exc:
        raise SemblanceError(str(exc)) from exc
    moved, restore_axes = _move_to_offset_time(np.asarray(rsf.data, dtype=dtype), axis, offset_axis)
    gather_shape = moved.shape[:-2]
    nh, nt = moved.shape[-2:]
    gather_count = int(np.prod(gather_shape, dtype=np.int64)) if gather_shape else 1
    gathers = moved.reshape((gather_count, nh, nt))
    time = cube.axis(axis).coordinates()
    try:
        offsets = _prepare_offsets(offset, rsf.header, nh, gather_count, offset_axis)
    except NMOError as exc:
        message = str(exc)
        if "offset data has" in message:
            message = f"offset vector length mismatch: {message}"
        raise SemblanceError(message) from exc

    panels = np.empty((gather_count, velocities.size, nt), dtype=np.float32)
    for igather in range(gather_count):
        for ivel, velocity in enumerate(velocities):
            corrected = _apply_nmo_gather(
                gathers[igather],
                time,
                np.full(nt, velocity, dtype=np.float64),
                offsets[igather],
                half=half,
                h0=h0_value,
                stretch=stretch_value,
                inverse=False,
            )
            panels[igather, ivel] = _semblance(corrected, smooth=smooth_value)

    moved_output = panels.reshape(gather_shape + (velocities.size, nt))
    output = moved_output
    header = _semblance_header(
        rsf.header,
        velocities,
        axis,
        offset_axis,
        offset_source="axis" if offset is None else "explicit",
    )
    header["semblance_half"] = "y" if half else "n"
    header["semblance_h0"] = h0_value
    header["semblance_stretch"] = 0.0 if stretch_value is None else stretch_value
    header["semblance_smooth"] = smooth_value
    return write_rsf(output_path, np.ascontiguousarray(output), header)


def _semblance(corrected: np.ndarray, *, smooth: int) -> np.ndarray:
    live = corrected != 0.0
    fold = np.sum(live, axis=0).astype(np.float64)
    numerator = np.square(np.sum(np.where(live, corrected, 0.0), axis=0, dtype=np.float64))
    denominator = fold * np.sum(np.where(live, corrected * corrected, 0.0), axis=0, dtype=np.float64)
    if smooth > 0:
        kernel = np.ones(2 * smooth + 1, dtype=np.float64)
        numerator = np.convolve(numerator, kernel, mode="same")
        denominator = np.convolve(denominator, kernel, mode="same")
    return np.divide(numerator, denominator, out=np.zeros_like(numerator), where=denominator > 0.0).astype(np.float32)


def _velocity_samples(vmin: float, vmax: float, dv: float) -> np.ndarray:
    start = _positive_finite(vmin, "vmin")
    stop = _positive_finite(vmax, "vmax")
    step = _positive_finite(dv, "dv")
    if step <= 0.0:
        raise SemblanceError("dv= must be positive")
    if stop < start:
        raise SemblanceError("vmax= must be greater than or equal to vmin=")
    count = int(np.floor((stop - start) / step + 0.5)) + 1
    velocities = start + step * np.arange(count, dtype=np.float64)
    output = velocities[velocities <= stop + 0.5 * step]
    if output.size < 1:
        raise SemblanceError("velocity scan must contain at least one sample")
    return output


def _semblance_header(
    header: Any,
    velocities: np.ndarray,
    axis: int,
    offset_axis: int,
    *,
    offset_source: str,
):
    cube = Hypercube.from_header(header)
    time_axis = cube.axis(axis)
    offset_axis_obj = cube.axis(offset_axis)
    axes = [
        time_axis,
        Axis(
            n=int(velocities.size),
            o=float(velocities[0]),
            d=float(velocities[1] - velocities[0]) if velocities.size > 1 else 1.0,
            label="Velocity",
            unit=_velocity_unit(time_axis.unit, cube.axis(offset_axis).unit),
            index=2,
        ),
    ]
    for index in range(1, cube.ndim + 1):
        if index not in {axis, offset_axis}:
            axes.append(cube.axis(index))
    output = Hypercube(axes).to_header(header.copy())
    output["semblance_algorithm"] = "simple_nmo_stack_ratio"
    output["semblance_reference_source"] = "../src-master/system/seismic/Mvscan.c"
    output["semblance_madagascar_subset"] = "velocity_panel_semblance_only"
    output["semblance_offset_source"] = offset_source
    output["axis2_role"] = "velocity"
    output["coordinate_sampling"] = "regular"
    output["semblance_input_offset_n"] = offset_axis_obj.n
    output["semblance_input_offset_o"] = offset_axis_obj.o
    output["semblance_input_offset_d"] = offset_axis_obj.d
    if offset_axis_obj.label is not None:
        output["semblance_input_offset_label"] = offset_axis_obj.label
    if offset_axis_obj.unit is not None:
        output["semblance_input_offset_unit"] = offset_axis_obj.unit
    for key in (
        "axis2_role",
        "coordinate_sampling",
        "offset_sign_convention",
        "offset_geometry",
        "source_receiver_geometry",
        "trace_header_model",
    ):
        if header.get(key) is not None:
            output[f"semblance_input_{key}"] = header.get(key)
    output["semblance_velocity_min"] = float(velocities[0])
    output["semblance_velocity_max"] = float(velocities[-1])
    output["semblance_velocity_count"] = int(velocities.size)
    output["semblance_interpolation"] = "linear"
    return output


def _velocity_unit(time_unit: str | None, offset_unit: str | None) -> str | None:
    if time_unit and offset_unit:
        return f"{offset_unit}/{time_unit}"
    return None


def _validate_gather_contract(
    rsf: RSFArray,
    cube: Hypercube,
    *,
    axis: int,
    offset_axis: int,
    offset: str | Path | np.ndarray | None,
) -> None:
    if rsf.data.ndim < 2:
        raise SemblanceError("semblance scan requires at least a 2D gather")
    if not bool(np.all(np.isfinite(rsf.data))):
        raise SemblanceError("input gather must contain only finite samples")

    time_axis = cube.axis(axis)
    if not np.isfinite(time_axis.o):
        raise SemblanceError(f"o{axis}= must be finite")
    if not np.isfinite(time_axis.d) or time_axis.d <= 0.0:
        raise SemblanceError(f"d{axis}= must be positive")
    if time_axis.n < 2:
        raise SemblanceError("semblance scan requires at least two time samples")

    if offset is None:
        regular_offset_axis = cube.axis(offset_axis)
        if not np.isfinite(regular_offset_axis.o):
            raise SemblanceError(f"o{offset_axis}= must be finite")
        if not np.isfinite(regular_offset_axis.d) or regular_offset_axis.d <= 0.0:
            raise SemblanceError(
                f"d{offset_axis}= must be positive when offset= is not provided"
            )


def _finite_scalar(value: float, name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise SemblanceError(f"{name}= must be finite") from exc
    if not np.isfinite(result):
        raise SemblanceError(f"{name}= must be finite")
    return result


def _positive_finite(value: float, name: str) -> float:
    result = _finite_scalar(value, name)
    if result <= 0.0:
        raise SemblanceError(f"{name}= must be positive")
    return result


def _stretch_value(stretch: float | None) -> float | None:
    if stretch is None:
        return None
    result = _finite_scalar(stretch, "stretch")
    if result < 0.0:
        raise SemblanceError("stretch= must be non-negative")
    return result


def _nonnegative_int(value: int, name: str) -> int:
    try:
        scalar = float(value)
    except (TypeError, ValueError) as exc:
        raise SemblanceError(f"{name}= must be an integer") from exc
    if not np.isfinite(scalar) or not scalar.is_integer():
        raise SemblanceError(f"{name}= must be an integer")
    result = int(scalar)
    if result < 0:
        raise SemblanceError(f"{name}= must be non-negative")
    return result
