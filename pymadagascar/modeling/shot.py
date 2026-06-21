"""Acquisition-driven wrappers for small acoustic2d shot modeling.

This module keeps the finite-difference numerical core in
pymadagascar.modeling.acoustic2d unchanged. It only adapts the F0-1
physical-coordinate geometry contract to the existing integer-index,
file-backed acoustic2d_forward prototype.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import numpy as np

from pymadagascar.io.rsf import RSFHeader, write_rsf
from pymadagascar.modeling.acoustic2d import Acoustic2DError, acoustic2d_forward
from pymadagascar.modeling.geometry import (
    AcousticAcquisition2D,
    AcousticModelGrid2D,
    acquisition_to_acoustic2d_indices,
)


@dataclass(frozen=True)
class AcousticShotRecord2D:
    """Pythonic single-shot record returned by run_acoustic2d_shot.

    data preserves the current acoustic2d_forward layout: (receiver, time)
    with shape (nr, nt). The companion time axis is a one-dimensional array of
    length nt. Receiver and source coordinates use columns/order x,z in the
    same local 2D coordinate frame as the acquisition geometry.
    """

    data: np.ndarray
    time: np.ndarray
    receiver_coordinates: np.ndarray
    source_coordinate: np.ndarray
    metadata: dict[str, Any]

    def __post_init__(self) -> None:
        data = np.asarray(self.data)
        time = np.asarray(self.time, dtype=float)
        receivers = np.asarray(self.receiver_coordinates, dtype=float)
        source = np.asarray(self.source_coordinate, dtype=float)

        if data.ndim != 2:
            raise Acoustic2DError("shot record data must have shape (receiver, time)")
        if time.ndim != 1:
            raise Acoustic2DError("shot record time axis must be one-dimensional")
        if data.shape[1] != time.size:
            raise Acoustic2DError("shot record data/time dimensions are inconsistent")
        if receivers.ndim != 2 or receivers.shape != (data.shape[0], 2):
            raise Acoustic2DError("receiver_coordinates must have shape (nr, 2)")
        if source.shape != (2,):
            raise Acoustic2DError("source_coordinate must have shape (2,)")
        if np.any(~np.isfinite(data)) or np.any(~np.isfinite(time)):
            raise Acoustic2DError("shot record data and time values must be finite")
        if np.any(~np.isfinite(receivers)) or np.any(~np.isfinite(source)):
            raise Acoustic2DError("shot record coordinates must be finite")

        object.__setattr__(self, "data", np.array(data, copy=True))
        object.__setattr__(self, "time", np.array(time, dtype=float, copy=True))
        object.__setattr__(self, "receiver_coordinates", np.array(receivers, dtype=float, copy=True))
        object.__setattr__(self, "source_coordinate", np.array(source, dtype=float, copy=True))
        object.__setattr__(self, "metadata", _json_safe_dict(self.metadata, "metadata"))


def run_acoustic2d_shot(
    velocity: np.ndarray,
    grid: AcousticModelGrid2D,
    acquisition: AcousticAcquisition2D,
    *,
    nt: int,
    dt: float,
    output_path: str | Path | None = None,
    fpeak: float = 25.0,
    t0: float | None = None,
    nb: int = 20,
    boundary_strength: float = 0.015,
    snapshot_interval: int | None = None,
    snapshot_path: str | Path | None = None,
    check_stability: bool = True,
) -> AcousticShotRecord2D:
    """Run one acoustic2d shot from physical acquisition geometry.

    The wrapper accepts a NumPy velocity model with shape (grid.nx, grid.nz)
    and an AcousticAcquisition2D in physical x,z coordinates. It converts the
    acquisition to integer (x_index, z_index) samples, writes a temporary RSF
    velocity file, calls the existing acoustic2d_forward core, and returns an
    AcousticShotRecord2D.

    This is a single-shot convenience wrapper. It does not add a new wave-
    equation solver, source/receiver interpolation, or multi-shot survey loop.
    """

    if not isinstance(grid, AcousticModelGrid2D):
        raise Acoustic2DError("grid must be an AcousticModelGrid2D")
    if not isinstance(acquisition, AcousticAcquisition2D):
        raise Acoustic2DError("acquisition must be an AcousticAcquisition2D")

    velocity_array = np.asarray(velocity, dtype=np.float32)
    if velocity_array.shape != (grid.nx, grid.nz):
        raise Acoustic2DError(
            f"velocity shape must match grid as {(grid.nx, grid.nz)}, got {velocity_array.shape}"
        )
    if np.any(~np.isfinite(velocity_array)):
        raise Acoustic2DError("velocity values must be finite")
    if np.any(velocity_array <= 0.0):
        raise Acoustic2DError("velocity values must be positive")

    nt_value = _positive_int(nt, "nt")
    dt_value = _positive_float(dt, "dt")
    sx, sz, receivers = acquisition_to_acoustic2d_indices(grid, acquisition)

    with TemporaryDirectory(prefix="pymada_acoustic2d_shot_") as tmpdir:
        tmp_path = Path(tmpdir)
        velocity_path = tmp_path / "velocity.rsf"
        shot_path = Path(output_path) if output_path is not None else tmp_path / "shot.rsf"
        write_rsf(velocity_path, np.ascontiguousarray(velocity_array), _velocity_header(grid))

        shot = acoustic2d_forward(
            velocity_path,
            shot_path,
            nt=nt_value,
            dt=dt_value,
            sx=sx,
            sz=sz,
            receivers=receivers,
            fpeak=fpeak,
            t0=t0,
            nb=nb,
            boundary_strength=boundary_strength,
            snapshot_interval=snapshot_interval,
            snapshot_path=snapshot_path,
            check_stability=check_stability,
        )
        data = np.array(shot.data, copy=True)

    time = np.arange(nt_value, dtype=float) * dt_value
    receiver_coordinates = np.array(acquisition.receivers.coordinates, dtype=float, copy=True)
    source_coordinate = np.array([acquisition.source.x, acquisition.source.z], dtype=float)
    metadata = _shot_metadata(
        grid=grid,
        acquisition=acquisition,
        source_index=(sx, sz),
        receiver_indices=receivers,
        data_shape=data.shape,
        nt=nt_value,
        dt=dt_value,
        fpeak=fpeak,
        t0=t0,
        nb=nb,
        boundary_strength=boundary_strength,
        snapshot_interval=snapshot_interval,
        check_stability=check_stability,
    )

    return AcousticShotRecord2D(
        data=data,
        time=time,
        receiver_coordinates=receiver_coordinates,
        source_coordinate=source_coordinate,
        metadata=metadata,
    )


def _velocity_header(grid: AcousticModelGrid2D) -> RSFHeader:
    return RSFHeader(
        {
            "n1": grid.nz,
            "o1": grid.oz,
            "d1": grid.dz,
            "label1": "Depth",
            "unit1": grid.distance_unit,
            "n2": grid.nx,
            "o2": grid.ox,
            "d2": grid.dx,
            "label2": "X",
            "unit2": grid.distance_unit,
        }
    )


def _shot_metadata(
    *,
    grid: AcousticModelGrid2D,
    acquisition: AcousticAcquisition2D,
    source_index: tuple[int, int],
    receiver_indices: list[tuple[int, int]],
    data_shape: tuple[int, ...],
    nt: int,
    dt: float,
    fpeak: float,
    t0: float | None,
    nb: int,
    boundary_strength: float,
    snapshot_interval: int | None,
    check_stability: bool,
) -> dict[str, Any]:
    return _json_safe_dict(
        {
            "method": "acoustic2d_shot",
            "numerical_core": "acoustic2d_forward",
            "coordinate_frame": grid.coordinate_frame,
            "distance_unit": grid.distance_unit,
            "time_unit": "s",
            "velocity_unit": "m/s",
            "velocity_shape": [grid.nx, grid.nz],
            "grid_nx": grid.nx,
            "grid_nz": grid.nz,
            "dx": grid.dx,
            "dz": grid.dz,
            "ox": grid.ox,
            "oz": grid.oz,
            "rsf_axis_convention": "n1=z,n2=x",
            "source_index": [int(source_index[0]), int(source_index[1])],
            "receiver_count": len(receiver_indices),
            "receiver_indices": [[int(ix), int(iz)] for ix, iz in receiver_indices],
            "receiver_index_order": "x_index_z_index",
            "data_shape": list(data_shape),
            "data_layout": "receiver_time",
            "nt": nt,
            "dt": dt,
            "fpeak": fpeak,
            "t0": t0,
            "nb": nb,
            "boundary_strength": boundary_strength,
            "snapshot_interval": snapshot_interval,
            "check_stability": check_stability,
            "source_coordinate": [acquisition.source.x, acquisition.source.z],
            "receiver_coordinates": acquisition.receivers.coordinates.tolist(),
            "acquisition": acquisition.to_metadata(grid),
            "prototype": True,
            "field_ready": False,
            "multi_shot": False,
            "source_interpolation": False,
            "receiver_interpolation": False,
        },
        "metadata",
    )


def _positive_int(value: Any, name: str) -> int:
    result = int(value)
    if result != value or result <= 0:
        raise Acoustic2DError(f"{name}= must be a positive integer")
    return result


def _positive_float(value: Any, name: str) -> float:
    result = float(value)
    if not np.isfinite(result) or result <= 0.0:
        raise Acoustic2DError(f"{name}= must be positive and finite")
    return result


def _json_safe_dict(value: Any, name: str) -> dict[str, Any]:
    result = _json_safe_value(value, name)
    if not isinstance(result, dict):
        raise Acoustic2DError(f"{name} must be a JSON-safe dictionary")
    return result


def _json_safe_value(value: Any, name: str) -> Any:
    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        result = float(value)
        if not np.isfinite(result):
            raise Acoustic2DError(f"{name} must be finite for JSON metadata")
        return result
    if isinstance(value, np.ndarray):
        return [_json_safe_value(item, name) for item in value.tolist()]
    if isinstance(value, (list, tuple)):
        return [_json_safe_value(item, name) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_safe_value(item, f"{name}.{key}") for key, item in value.items()}
    raise Acoustic2DError(f"{name} is not JSON-safe")


__all__ = ["AcousticShotRecord2D", "run_acoustic2d_shot"]
