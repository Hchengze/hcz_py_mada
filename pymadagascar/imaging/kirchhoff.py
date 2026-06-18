"""Small 2D post-stack Kirchhoff time migration prototype."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from pymadagascar.core.hypercube import Hypercube
from pymadagascar.io.rsf import RSFArray, RSFHeader, read_rsf, write_rsf
from pymadagascar.seismic._utils import numpy_axis, real_output_dtype, validate_rsf_axis


class ImagingError(ValueError):
    """Raised when an imaging request is invalid."""


VelocityInput = str | Path | float | int | np.ndarray


def kirchhoff_time_migration(
    input_path: str | Path,
    output_path: str | Path,
    *,
    velocity: VelocityInput,
    axis: int = 1,
    x_axis: int = 2,
    aperture: float | None = None,
    normalize: bool = False,
) -> RSFArray:
    """Migrate a 2D post-stack zero-offset section with a simple Kirchhoff sum.

    This prototype keeps the input sampling and returns an image with the same
    shape as the input. Axis numbers follow RSF/Madagascar 1-based convention.
    """

    rsf = read_rsf(input_path)
    cube = _validate_input(rsf.header, axis=axis, x_axis=x_axis)
    dtype = real_output_dtype(rsf.data)
    data = _move_to_x_time(np.asarray(rsf.data, dtype=dtype), axis=axis, x_axis=x_axis)
    time = cube.axis(axis).coordinates()
    x_coords = cube.axis(x_axis).coordinates()
    velocities = _prepare_velocity(velocity, time.size)

    image = kirchhoff_time_migration_array(
        data,
        time,
        x_coords,
        velocities,
        aperture=aperture,
        normalize=normalize,
    )
    restored = _restore_from_x_time(image, axis=axis, x_axis=x_axis, ndim=rsf.data.ndim)
    header = _output_header(
        rsf.header,
        axis=axis,
        x_axis=x_axis,
        velocity=velocity,
        aperture=aperture,
        normalize=normalize,
    )
    return write_rsf(output_path, np.ascontiguousarray(restored.astype(dtype, copy=False)), header)


def kirchhoff_time_migration_array(
    data: np.ndarray,
    time: np.ndarray,
    x_coords: np.ndarray,
    velocity: np.ndarray | float,
    *,
    aperture: float | None = None,
    normalize: bool = False,
) -> np.ndarray:
    """Return a migrated image for arrays shaped ``(nx, nt)``."""

    gather = np.asarray(data, dtype=np.float64)
    if gather.ndim != 2:
        raise ImagingError("kirchhoff_time_migration_array requires a 2D array shaped (nx, nt)")

    time_values = _regular_axis_values(time, "time")
    x_values = _axis_values(x_coords, "x_coords")
    if gather.shape != (x_values.size, time_values.size):
        raise ImagingError(f"data shape must be {(x_values.size, time_values.size)}, got {gather.shape}")

    velocities = _velocity_values(velocity, time_values.size)
    if aperture is not None and aperture < 0.0:
        raise ImagingError("aperture= must be non-negative")

    nt = time_values.size
    nx = x_values.size
    t0 = float(time_values[0])
    dt = float(time_values[1] - time_values[0]) if nt > 1 else 1.0
    trace_indices = np.arange(nx)
    image = np.zeros((nx, nt), dtype=np.float64)

    for ix_image, x_image in enumerate(x_values):
        lateral = x_values - x_image
        if aperture is None:
            live = np.ones(nx, dtype=bool)
        else:
            live = np.abs(lateral) <= aperture
        live_indices = trace_indices[live]
        live_lateral = lateral[live]
        if live_indices.size == 0:
            continue

        for itau, tau in enumerate(time_values):
            vel = velocities[itau]
            travel = np.sqrt(tau * tau + np.square(2.0 * live_lateral / vel))
            image[ix_image, itau] = _sample_and_sum(
                gather,
                live_indices,
                travel,
                t0=t0,
                dt=dt,
                nt=nt,
                normalize=normalize,
            )
    return image.astype(np.float32)


def _sample_and_sum(
    gather: np.ndarray,
    trace_indices: np.ndarray,
    travel: np.ndarray,
    *,
    t0: float,
    dt: float,
    nt: int,
    normalize: bool,
) -> float:
    sample = (travel - t0) / dt
    lower = np.floor(sample).astype(np.int64)
    frac = sample - lower
    valid0 = (lower >= 0) & (lower < nt)
    valid1 = (lower + 1 >= 0) & (lower + 1 < nt)

    values = np.zeros(sample.shape, dtype=np.float64)
    if np.any(valid0):
        idx = valid0
        values[idx] += (1.0 - frac[idx]) * gather[trace_indices[idx], lower[idx]]
    if np.any(valid1):
        idx = valid1
        values[idx] += frac[idx] * gather[trace_indices[idx], lower[idx] + 1]

    live = valid0 | valid1
    total = float(np.sum(values))
    if normalize and np.any(live):
        total /= float(np.count_nonzero(live))
    return total


def _validate_input(header: RSFHeader, *, axis: int, x_axis: int) -> Hypercube:
    cube = Hypercube.from_header(header)
    if cube.ndim != 2:
        raise ImagingError(f"Kirchhoff prototype currently requires 2D input, got {cube.ndim}D")
    validate_rsf_axis(axis, cube.ndim)
    validate_rsf_axis(x_axis, cube.ndim)
    if axis == x_axis:
        raise ImagingError("axis and x_axis must be different")
    if cube.axis(axis).d <= 0.0:
        raise ImagingError(f"d{axis}= must be positive")
    return cube


def _move_to_x_time(data: np.ndarray, *, axis: int, x_axis: int) -> np.ndarray:
    time_np = numpy_axis(axis, data.ndim)
    x_np = numpy_axis(x_axis, data.ndim)
    return np.moveaxis(data, [x_np, time_np], [0, 1])


def _restore_from_x_time(data: np.ndarray, *, axis: int, x_axis: int, ndim: int) -> np.ndarray:
    time_np = numpy_axis(axis, ndim)
    x_np = numpy_axis(x_axis, ndim)
    return np.moveaxis(data, [0, 1], [x_np, time_np])


def _prepare_velocity(velocity: VelocityInput, nt: int) -> np.ndarray:
    if isinstance(velocity, np.ndarray):
        values = np.asarray(velocity, dtype=np.float64)
    elif isinstance(velocity, (int, float)):
        values = np.asarray([float(velocity)], dtype=np.float64)
    else:
        try:
            values = np.asarray([float(str(velocity))], dtype=np.float64)
        except ValueError:
            values = np.asarray(read_rsf(velocity).data, dtype=np.float64)
    return _velocity_values(values, nt)


def _velocity_values(velocity: np.ndarray | float, nt: int) -> np.ndarray:
    values = np.asarray(velocity, dtype=np.float64).reshape(-1)
    if values.size == 1:
        values = np.full(nt, values.item(), dtype=np.float64)
    elif values.size != nt:
        raise ImagingError(f"velocity has {values.size} samples, expected 1 or {nt}")
    if not np.all(np.isfinite(values)):
        raise ImagingError("velocity contains non-finite values")
    if np.any(values <= 0.0):
        raise ImagingError("velocity values must be positive")
    return values


def _regular_axis_values(values: np.ndarray, name: str) -> np.ndarray:
    axis = _axis_values(values, name)
    if axis.size > 1:
        diffs = np.diff(axis)
        if not np.allclose(diffs, diffs[0], rtol=1e-6, atol=1e-12):
            raise ImagingError(f"{name} axis must be regularly sampled")
        if diffs[0] <= 0.0:
            raise ImagingError(f"{name} axis sampling must be positive")
    return axis


def _axis_values(values: np.ndarray, name: str) -> np.ndarray:
    axis = np.asarray(values, dtype=np.float64).reshape(-1)
    if axis.size < 1:
        raise ImagingError(f"{name} must contain at least one value")
    if not np.all(np.isfinite(axis)):
        raise ImagingError(f"{name} contains non-finite values")
    return axis


def _output_header(
    header: RSFHeader,
    *,
    axis: int,
    x_axis: int,
    velocity: VelocityInput,
    aperture: float | None,
    normalize: bool,
) -> RSFHeader:
    cube = Hypercube.from_header(header)
    output = cube.update_axis(axis, label="Migrated Time").update_axis(x_axis, label="Image X").to_header(header.copy())
    output["kirchhoff_algorithm"] = "poststack_time"
    output["kirchhoff_normalize"] = "y" if normalize else "n"
    if aperture is not None:
        output["kirchhoff_aperture"] = aperture
    output["kirchhoff_velocity"] = _velocity_header_value(velocity)
    return output


def _velocity_header_value(velocity: VelocityInput) -> str:
    if isinstance(velocity, np.ndarray):
        return "array"
    if isinstance(velocity, (int, float)):
        return f"{float(velocity):g}"
    try:
        return f"{float(str(velocity)):g}"
    except ValueError:
        return str(velocity)

