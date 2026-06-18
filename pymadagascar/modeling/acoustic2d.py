"""Small 2D acoustic finite-difference forward-modeling prototype."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np

from pymadagascar.core.hypercube import Hypercube
from pymadagascar.io.rsf import RSFArray, RSFHeader, read_rsf, write_rsf
from pymadagascar.signal.wavelet import WaveletError, ricker_wavelet as _signal_ricker_wavelet


class Acoustic2DError(ValueError):
    """Raised when an acoustic FD modeling request is invalid."""


ReceiverSpec = Sequence[tuple[int, int]] | np.ndarray | None


def ricker_wavelet(
    nt: int,
    dt: float,
    fpeak: float,
    *,
    t0: float | None = None,
    dtype: str | np.dtype[Any] = "float32",
) -> np.ndarray:
    """Return a Ricker wavelet sampled for ``nt`` time samples."""

    try:
        return _signal_ricker_wavelet(
            frequency=fpeak,
            dt=dt,
            nt=nt,
            peak_time=t0,
            dtype=dtype,
        )
    except WaveletError as exc:
        message = str(exc).replace("frequency=", "fpeak=")
        raise Acoustic2DError(message) from exc


def absorbing_boundary_simple(
    field: np.ndarray,
    *,
    nb: int = 20,
    strength: float = 0.015,
    damping: np.ndarray | None = None,
) -> np.ndarray:
    """Return ``field`` multiplied by a simple exponential sponge boundary."""

    array = np.asarray(field)
    if array.ndim != 2:
        raise Acoustic2DError("absorbing_boundary_simple requires a 2D field")
    if damping is None:
        damping = _absorbing_mask(array.shape, nb=nb, strength=strength)
    if damping.shape != array.shape:
        raise Acoustic2DError("damping mask shape must match field shape")
    return (array * damping).astype(array.dtype, copy=False)


def acoustic2d_forward(
    velocity_path: str | Path,
    output_path: str | Path,
    *,
    nt: int,
    dt: float,
    sx: int,
    sz: int,
    receivers: ReceiverSpec = None,
    fpeak: float = 25.0,
    t0: float | None = None,
    nb: int = 20,
    boundary_strength: float = 0.015,
    snapshot_interval: int | None = None,
    snapshot_path: str | Path | None = None,
    check_stability: bool = True,
) -> RSFArray:
    """Run a small 2D acoustic scalar-wave FD simulation.

    The velocity RSF is interpreted as ``n1=z`` and ``n2=x``; its NumPy shape
    is therefore ``(nx, nz)``. Source and receiver positions are integer
    samples in ``(x_index, z_index)`` order.
    """

    velocity_rsf = read_rsf(velocity_path)
    velocity = np.asarray(velocity_rsf.data, dtype=np.float32)
    cube = _validate_velocity_model(velocity_rsf.header, velocity)
    z_axis = cube.axis(1)
    x_axis = cube.axis(2)
    dz = float(z_axis.d)
    dx = float(x_axis.d)
    nt_value = int(nt)
    dt_value = float(dt)
    source = _validate_point((sx, sz), velocity.shape, "source")
    receiver_points = _prepare_receivers(receivers, velocity.shape, default_z=source[1])
    cfl = _check_stability(velocity, dt_value, dx, dz, enabled=check_stability)

    wavelet = ricker_wavelet(nt_value, dt_value, fpeak, t0=t0, dtype="float32")
    damping = _absorbing_mask(velocity.shape, nb=nb, strength=boundary_strength)
    shot = _propagate(
        velocity,
        wavelet,
        dt=dt_value,
        dx=dx,
        dz=dz,
        source=source,
        receivers=receiver_points,
        damping=damping,
        snapshot_interval=snapshot_interval,
    )

    header = _shot_header(
        velocity_rsf.header,
        receiver_points,
        nt=nt_value,
        dt=dt_value,
        fpeak=fpeak,
        t0=t0,
        nb=nb,
        cfl=cfl,
        velocity_path=velocity_path,
    )
    result = write_rsf(output_path, np.ascontiguousarray(shot.data), header)

    if snapshot_path is not None:
        if shot.snapshots is None:
            raise Acoustic2DError("snapshot_interval= is required when snapshot_path is provided")
        snapshot_header = _snapshot_header(velocity_rsf.header, shot.snapshot_times, dt=dt_value)
        write_rsf(snapshot_path, np.ascontiguousarray(shot.snapshots), snapshot_header)

    return result


class _ForwardResult:
    def __init__(
        self,
        data: np.ndarray,
        snapshots: np.ndarray | None,
        snapshot_times: np.ndarray,
    ) -> None:
        self.data = data
        self.snapshots = snapshots
        self.snapshot_times = snapshot_times


def _propagate(
    velocity: np.ndarray,
    wavelet: np.ndarray,
    *,
    dt: float,
    dx: float,
    dz: float,
    source: tuple[int, int],
    receivers: list[tuple[int, int]],
    damping: np.ndarray,
    snapshot_interval: int | None,
) -> _ForwardResult:
    nt = wavelet.size
    nr = len(receivers)
    velocity2_dt2 = np.square(velocity.astype(np.float32)) * (dt * dt)
    p_prev = np.zeros_like(velocity, dtype=np.float32)
    p_curr = np.zeros_like(velocity, dtype=np.float32)
    p_next = np.zeros_like(velocity, dtype=np.float32)
    lap = np.zeros_like(velocity, dtype=np.float32)
    shot = np.zeros((nr, nt), dtype=np.float32)
    snapshots: list[np.ndarray] = []
    snapshot_times: list[int] = []

    jsnap = _normalize_snapshot_interval(snapshot_interval)
    sx, sz = source

    for it in range(nt):
        lap.fill(0.0)
        lap[1:-1, 1:-1] = (
            (p_curr[2:, 1:-1] - 2.0 * p_curr[1:-1, 1:-1] + p_curr[:-2, 1:-1]) / (dx * dx)
            + (p_curr[1:-1, 2:] - 2.0 * p_curr[1:-1, 1:-1] + p_curr[1:-1, :-2]) / (dz * dz)
        )
        p_next[:] = 2.0 * p_curr - p_prev + velocity2_dt2 * lap
        p_next[sx, sz] += wavelet[it]
        p_next *= damping
        p_curr *= damping

        for irec, (rx, rz) in enumerate(receivers):
            shot[irec, it] = p_next[rx, rz]

        if jsnap is not None and it % jsnap == 0:
            snapshots.append(p_next.copy())
            snapshot_times.append(it)

        p_prev, p_curr, p_next = p_curr, p_next, p_prev

    snapshot_array = np.stack(snapshots, axis=0).astype(np.float32) if snapshots else None
    return _ForwardResult(shot, snapshot_array, np.asarray(snapshot_times, dtype=np.int32))


def _validate_velocity_model(header: RSFHeader, velocity: np.ndarray) -> Hypercube:
    cube = Hypercube.from_header(header)
    if cube.ndim != 2:
        raise Acoustic2DError(f"2D velocity model required, got {cube.ndim}D")
    if velocity.ndim != 2:
        raise Acoustic2DError("velocity array must be 2D")
    if cube.axis(1).d <= 0.0 or cube.axis(2).d <= 0.0:
        raise Acoustic2DError("velocity model d1= and d2= must be positive")
    if np.any(~np.isfinite(velocity)):
        raise Acoustic2DError("velocity model contains non-finite values")
    if np.any(velocity <= 0.0):
        raise Acoustic2DError("velocity values must be positive")
    return cube


def _check_stability(
    velocity: np.ndarray,
    dt: float,
    dx: float,
    dz: float,
    *,
    enabled: bool,
) -> float:
    if dt <= 0.0:
        raise Acoustic2DError("dt= must be positive")
    cfl = float(np.max(velocity) * dt * np.sqrt(1.0 / (dx * dx) + 1.0 / (dz * dz)))
    if enabled and cfl > 1.0:
        raise Acoustic2DError(
            f"stability condition violated: vmax*dt*sqrt(1/dx^2+1/dz^2)={cfl:g} > 1"
        )
    return cfl


def _validate_point(point: tuple[int, int], shape: tuple[int, int], name: str) -> tuple[int, int]:
    x, z = int(point[0]), int(point[1])
    nx, nz = shape
    if x < 0 or x >= nx or z < 0 or z >= nz:
        raise Acoustic2DError(f"{name} index {(x, z)} is outside model shape {(nx, nz)}")
    return x, z


def _prepare_receivers(
    receivers: ReceiverSpec,
    shape: tuple[int, int],
    *,
    default_z: int,
) -> list[tuple[int, int]]:
    nx, _ = shape
    if receivers is None:
        return [_validate_point((ix, default_z), shape, "receiver") for ix in range(nx)]
    array = np.asarray(receivers, dtype=np.int64)
    if array.ndim != 2 or array.shape[1] != 2:
        raise Acoustic2DError("receivers must be an array/list of (x_index, z_index) pairs")
    return [_validate_point((int(x), int(z)), shape, "receiver") for x, z in array]


def _absorbing_mask(shape: tuple[int, int], *, nb: int, strength: float) -> np.ndarray:
    nb_value = int(nb)
    strength_value = float(strength)
    if nb_value < 0:
        raise Acoustic2DError("nb= must be non-negative")
    if strength_value < 0.0:
        raise Acoustic2DError("boundary_strength= must be non-negative")
    nx, nz = shape
    if nb_value == 0:
        return np.ones(shape, dtype=np.float32)
    nb_value = min(nb_value, max(nx, nz))
    x_distance = np.minimum(np.arange(nx), np.arange(nx)[::-1])
    z_distance = np.minimum(np.arange(nz), np.arange(nz)[::-1])
    x_taper = _edge_taper(x_distance, nb_value, strength_value)
    z_taper = _edge_taper(z_distance, nb_value, strength_value)
    return (x_taper.reshape(nx, 1) * z_taper.reshape(1, nz)).astype(np.float32)


def _edge_taper(distance: np.ndarray, nb: int, strength: float) -> np.ndarray:
    taper = np.ones(distance.shape, dtype=np.float64)
    edge = distance < nb
    taper[edge] = np.exp(-strength * np.square(nb - distance[edge]))
    return taper


def _normalize_snapshot_interval(snapshot_interval: int | None) -> int | None:
    if snapshot_interval is None:
        return None
    value = int(snapshot_interval)
    if value < 1:
        raise Acoustic2DError("snapshot_interval= must be positive")
    return value


def _shot_header(
    velocity_header: RSFHeader,
    receivers: list[tuple[int, int]],
    *,
    nt: int,
    dt: float,
    fpeak: float,
    t0: float | None,
    nb: int,
    cfl: float,
    velocity_path: str | Path,
) -> RSFHeader:
    cube = Hypercube.from_header(velocity_header)
    x_axis = cube.axis(2)
    z_axis = cube.axis(1)
    rx = np.asarray([point[0] for point in receivers], dtype=np.float64)
    rz = np.asarray([point[1] for point in receivers], dtype=np.float64)
    receiver_x = x_axis.o + rx * x_axis.d
    receiver_z = z_axis.o + rz * z_axis.d
    header = RSFHeader(
        {
            "n1": nt,
            "o1": 0.0,
            "d1": dt,
            "label1": "Time",
            "unit1": "s",
            "n2": len(receivers),
            "o2": float(receiver_x[0]) if receiver_x.size else 0.0,
            "d2": _regular_spacing(receiver_x, default=1.0),
            "label2": "Receiver",
            "unit2": x_axis.unit or "index",
            "receiver_x": ",".join(f"{value:g}" for value in receiver_x),
            "receiver_z": ",".join(f"{value:g}" for value in receiver_z),
            "acoustic2d_equation": "p_tt=v^2*(p_xx+p_zz)+s",
            "acoustic2d_fd_time_order": 2,
            "acoustic2d_fd_space_order": 2,
            "acoustic2d_velocity": str(velocity_path),
            "acoustic2d_fpeak": fpeak,
            "acoustic2d_t0": (1.0 / float(fpeak)) if t0 is None else t0,
            "acoustic2d_nb": nb,
            "acoustic2d_cfl": cfl,
        }
    )
    return header


def _snapshot_header(
    velocity_header: RSFHeader,
    snapshot_times: np.ndarray,
    *,
    dt: float,
) -> RSFHeader:
    header = velocity_header.copy()
    header["n3"] = int(snapshot_times.size)
    header["o3"] = float(snapshot_times[0] * dt) if snapshot_times.size else 0.0
    header["d3"] = float((snapshot_times[1] - snapshot_times[0]) * dt) if snapshot_times.size > 1 else dt
    header["label3"] = "Snapshot Time"
    header["unit3"] = "s"
    return header


def _regular_spacing(values: np.ndarray, *, default: float) -> float:
    if values.size < 2:
        return default
    diffs = np.diff(values)
    if np.allclose(diffs, diffs[0], rtol=1e-6, atol=1e-12):
        return float(diffs[0])
    return default
