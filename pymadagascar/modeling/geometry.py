"""Small 2D model/acquisition geometry helpers for acoustic prototypes.

The current pymadagascar.modeling.acoustic2d forward model uses integer source
and receiver samples in (x_index, z_index) order. This module provides a thin,
pure-Python geometry contract for converting local physical coordinates to
those integer samples without changing the finite-difference solver itself.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

import numpy as np


class GeometryError(ValueError):
    """Raised when a modeling geometry request is invalid."""


def _finite_float(value: Any, name: str) -> float:
    result = float(value)
    if not np.isfinite(result):
        raise GeometryError(f"{name} must be finite")
    return result


def _positive_finite_float(value: Any, name: str) -> float:
    result = _finite_float(value, name)
    if result <= 0.0:
        raise GeometryError(f"{name} must be positive")
    return result


def _positive_int(value: Any, name: str) -> int:
    result = int(value)
    if result != value or result <= 0:
        raise GeometryError(f"{name} must be a positive integer")
    return result


def _json_safe_copy(metadata: Mapping[str, Any] | None) -> dict[str, Any]:
    if metadata is None:
        return {}
    result: dict[str, Any] = {}
    for key, value in metadata.items():
        if not isinstance(key, str):
            raise GeometryError("metadata keys must be strings")
        result[key] = _json_safe_value(value, f"metadata[{key!r}]")
    return result


def _json_safe_value(value: Any, name: str) -> Any:
    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        result = float(value)
        if not np.isfinite(result):
            raise GeometryError(f"{name} must be finite for JSON metadata")
        return result
    if isinstance(value, np.ndarray):
        return [_json_safe_value(item, name) for item in value.tolist()]
    if isinstance(value, (list, tuple)):
        return [_json_safe_value(item, name) for item in value]
    if isinstance(value, Mapping):
        return _json_safe_copy(value)
    raise GeometryError(f"{name} is not JSON-safe")


@dataclass(frozen=True)
class AcousticModelGrid2D:
    """Regular local 2D acoustic model grid.

    Coordinates follow x = ox + ix * dx and z = oz + iz * dz with z positive
    downward. The acoustic2d prototype stores velocity arrays as (nx, nz) and
    maps RSF axes as n1=z and n2=x.
    """

    nx: int
    nz: int
    dx: float
    dz: float
    ox: float = 0.0
    oz: float = 0.0
    distance_unit: str = "m"
    coordinate_frame: str = "local_2d_x_z"
    depth_positive: str = "down"

    def __post_init__(self) -> None:
        object.__setattr__(self, "nx", _positive_int(self.nx, "nx"))
        object.__setattr__(self, "nz", _positive_int(self.nz, "nz"))
        object.__setattr__(self, "dx", _positive_finite_float(self.dx, "dx"))
        object.__setattr__(self, "dz", _positive_finite_float(self.dz, "dz"))
        object.__setattr__(self, "ox", _finite_float(self.ox, "ox"))
        object.__setattr__(self, "oz", _finite_float(self.oz, "oz"))
        if not isinstance(self.distance_unit, str) or not self.distance_unit:
            raise GeometryError("distance_unit must be a non-empty string")
        if self.coordinate_frame != "local_2d_x_z":
            raise GeometryError("coordinate_frame must be 'local_2d_x_z'")
        if self.depth_positive != "down":
            raise GeometryError("depth_positive must be 'down'")

    @property
    def x_stop(self) -> float:
        """Physical x coordinate of the last grid sample."""

        return self.ox + (self.nx - 1) * self.dx

    @property
    def z_stop(self) -> float:
        """Physical z coordinate of the last grid sample."""

        return self.oz + (self.nz - 1) * self.dz

    def contains_index(self, ix: int, iz: int) -> bool:
        """Return whether (ix, iz) lies inside the model grid."""

        return 0 <= int(ix) < self.nx and 0 <= int(iz) < self.nz

    def contains_coordinate(self, x: float, z: float) -> bool:
        """Return whether a physical coordinate lies within sampled extents."""

        x_value = _finite_float(x, "x")
        z_value = _finite_float(z, "z")
        x_tol = 1.0e-9 * max(1.0, abs(self.ox), abs(self.x_stop), self.dx)
        z_tol = 1.0e-9 * max(1.0, abs(self.oz), abs(self.z_stop), self.dz)
        return (
            self.ox - x_tol <= x_value <= self.x_stop + x_tol
            and self.oz - z_tol <= z_value <= self.z_stop + z_tol
        )

    def index_to_coordinate(self, ix: int, iz: int) -> tuple[float, float]:
        """Return (x, z) for integer (x_index, z_index) samples."""

        ix_value = int(ix)
        iz_value = int(iz)
        if not self.contains_index(ix_value, iz_value):
            raise GeometryError(f"index {(ix_value, iz_value)} is outside grid {(self.nx, self.nz)}")
        return (self.ox + ix_value * self.dx, self.oz + iz_value * self.dz)

    def coordinate_to_nearest_index(self, x: float, z: float) -> tuple[int, int]:
        """Map a coordinate to the nearest integer sample without interpolation."""

        x_value = _finite_float(x, "x")
        z_value = _finite_float(z, "z")
        if not self.contains_coordinate(x_value, z_value):
            raise GeometryError(f"coordinate {(x_value, z_value)} is outside grid extents")
        ix = int(np.floor((x_value - self.ox) / self.dx + 0.5))
        iz = int(np.floor((z_value - self.oz) / self.dz + 0.5))
        if not self.contains_index(ix, iz):
            raise GeometryError(f"coordinate {(x_value, z_value)} rounds outside grid")
        return ix, iz

    def to_metadata(self) -> dict[str, Any]:
        """Return JSON-safe model-grid metadata."""

        return {
            "geometry_kind": "acoustic_model_grid_2d",
            "coordinate_frame": self.coordinate_frame,
            "distance_unit": self.distance_unit,
            "depth_positive": self.depth_positive,
            "nx": self.nx,
            "nz": self.nz,
            "dx": self.dx,
            "dz": self.dz,
            "ox": self.ox,
            "oz": self.oz,
            "x_stop": self.x_stop,
            "z_stop": self.z_stop,
            "numpy_velocity_shape": [self.nx, self.nz],
            "rsf_axis_convention": "n1=z,n2=x",
            "index_order": "x_index,z_index",
            "coordinate_formula": "x=ox+ix*dx; z=oz+iz*dz",
            "interpolation": "not_modeled",
        }


@dataclass(frozen=True)
class PointSource2D:
    """Point-source coordinate for local 2D acoustic prototype geometry."""

    x: float
    z: float
    kind: str = "point_source"

    def __post_init__(self) -> None:
        object.__setattr__(self, "x", _finite_float(self.x, "source x"))
        object.__setattr__(self, "z", _finite_float(self.z, "source z"))
        if not isinstance(self.kind, str) or not self.kind:
            raise GeometryError("source kind must be a non-empty string")

    def to_index(self, grid: AcousticModelGrid2D) -> tuple[int, int]:
        """Return the nearest (x_index, z_index) on grid."""

        return grid.coordinate_to_nearest_index(self.x, self.z)

    def to_metadata(self) -> dict[str, Any]:
        """Return JSON-safe source metadata."""

        return {"source_kind": self.kind, "source_x": self.x, "source_z": self.z}


@dataclass(frozen=True)
class ReceiverArray2D:
    """Receiver coordinates with columns x,z in a local 2D frame."""

    coordinates: np.ndarray
    kind: str = "receiver_array"
    metadata: Mapping[str, Any] | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        array = np.asarray(self.coordinates, dtype=float)
        if array.ndim != 2 or array.shape[1] != 2:
            raise GeometryError("receiver coordinates must have shape (nr, 2) with columns x,z")
        if array.shape[0] <= 0:
            raise GeometryError("receiver array must contain at least one receiver")
        if np.any(~np.isfinite(array)):
            raise GeometryError("receiver coordinates must be finite")
        object.__setattr__(self, "coordinates", np.array(array, dtype=float, copy=True))
        if not isinstance(self.kind, str) or not self.kind:
            raise GeometryError("receiver kind must be a non-empty string")
        object.__setattr__(self, "metadata", _json_safe_copy(self.metadata))

    @property
    def receiver_count(self) -> int:
        """Number of receiver coordinates."""

        return int(self.coordinates.shape[0])

    def to_indices(self, grid: AcousticModelGrid2D) -> list[tuple[int, int]]:
        """Return nearest (x_index, z_index) pairs for acoustic2d."""

        return [grid.coordinate_to_nearest_index(float(x), float(z)) for x, z in self.coordinates]

    def to_metadata(self) -> dict[str, Any]:
        """Return JSON-safe receiver-array metadata."""

        x_values = self.coordinates[:, 0]
        z_values = self.coordinates[:, 1]
        result: dict[str, Any] = {
            "receiver_kind": self.kind,
            "receiver_count": self.receiver_count,
            "receiver_x_min": float(np.min(x_values)),
            "receiver_x_max": float(np.max(x_values)),
            "receiver_z_min": float(np.min(z_values)),
            "receiver_z_max": float(np.max(z_values)),
            "coordinates": self.coordinates.tolist(),
        }
        result.update(_json_safe_copy(self.metadata))
        return result


def receiver_line_2d(
    *,
    x_start: float,
    x_stop: float,
    z: float,
    spacing: float,
) -> ReceiverArray2D:
    """Build a regular horizontal receiver line.

    The line starts at x_start and advances by spacing while samples are <=
    x_stop. The final endpoint is included only when it falls on the spacing
    grid within floating-point tolerance.
    """

    start = _finite_float(x_start, "x_start")
    stop = _finite_float(x_stop, "x_stop")
    z_value = _finite_float(z, "z")
    step = _positive_finite_float(spacing, "spacing")
    if stop < start:
        raise GeometryError("x_stop must be greater than or equal to x_start")
    count = int(np.floor((stop - start) / step + 1.0e-9)) + 1
    x_values = start + step * np.arange(count, dtype=float)
    coordinates = np.column_stack([x_values, np.full_like(x_values, z_value)])
    endpoint_included = bool(np.isclose(x_values[-1], stop, rtol=0.0, atol=1.0e-9 * max(1.0, abs(stop))))
    return ReceiverArray2D(
        coordinates,
        kind="receiver_line",
        metadata={
            "line_geometry": "regular_x_line",
            "x_start": start,
            "x_stop": stop,
            "z": z_value,
            "spacing": step,
            "endpoint_policy": "included_when_on_spacing_grid",
            "endpoint_included": endpoint_included,
        },
    )


@dataclass(frozen=True)
class AcousticAcquisition2D:
    """Point-source and receiver-array acquisition geometry."""

    source: PointSource2D
    receivers: ReceiverArray2D

    def __post_init__(self) -> None:
        if not isinstance(self.source, PointSource2D):
            raise GeometryError("source must be a PointSource2D")
        if not isinstance(self.receivers, ReceiverArray2D):
            raise GeometryError("receivers must be a ReceiverArray2D")

    def to_indices(self, grid: AcousticModelGrid2D) -> tuple[int, int, list[tuple[int, int]]]:
        """Return sx, sz, receivers in acoustic2d_forward index format."""

        sx, sz = self.source.to_index(grid)
        return sx, sz, self.receivers.to_indices(grid)

    def to_metadata(self, grid: AcousticModelGrid2D | None = None) -> dict[str, Any]:
        """Return JSON-safe acquisition metadata, optionally including grid metadata."""

        result: dict[str, Any] = {
            "geometry_kind": "acoustic_acquisition_2d",
            "coordinate_frame": "local_2d_x_z",
            "distance_unit": grid.distance_unit if grid is not None else "m",
            "depth_positive": "down",
            **self.source.to_metadata(),
            **self.receivers.to_metadata(),
        }
        if grid is not None:
            result["model_grid"] = grid.to_metadata()
            sx, sz, receiver_indices = self.to_indices(grid)
            result["source_index"] = [sx, sz]
            result["receiver_indices"] = [[ix, iz] for ix, iz in receiver_indices]
        return result


def acquisition_to_acoustic2d_indices(
    grid: AcousticModelGrid2D,
    acquisition: AcousticAcquisition2D,
) -> tuple[int, int, list[tuple[int, int]]]:
    """Return sx, sz, receivers for acoustic2d_forward.

    The returned receiver list contains integer (x_index, z_index) pairs and
    performs no interpolation or sub-sample source/receiver injection.
    """

    if not isinstance(grid, AcousticModelGrid2D):
        raise GeometryError("grid must be an AcousticModelGrid2D")
    if not isinstance(acquisition, AcousticAcquisition2D):
        raise GeometryError("acquisition must be an AcousticAcquisition2D")
    return acquisition.to_indices(grid)


__all__ = [
    "AcousticAcquisition2D",
    "AcousticModelGrid2D",
    "GeometryError",
    "PointSource2D",
    "ReceiverArray2D",
    "acquisition_to_acoustic2d_indices",
    "receiver_line_2d",
]
