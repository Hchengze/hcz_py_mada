"""Synthetic 2D acoustic velocity model builders.

These helpers create small, deterministic velocity arrays for the existing
acoustic2d prototypes. Arrays follow the project modeling convention:
velocity.shape == (grid.nx, grid.nz), with x as the first NumPy axis and
z/depth as the second axis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

import numpy as np

from .geometry import AcousticModelGrid2D, GeometryError


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


def _base_metadata(
    grid: AcousticModelGrid2D,
    *,
    model_kind: str,
    velocity_unit: str,
) -> dict[str, Any]:
    return {
        "model_kind": model_kind,
        "velocity_unit": velocity_unit,
        "coordinate_frame": grid.coordinate_frame,
        "distance_unit": grid.distance_unit,
        "depth_positive": grid.depth_positive,
        "grid_nx": grid.nx,
        "grid_nz": grid.nz,
        "velocity_shape": [grid.nx, grid.nz],
        "numpy_velocity_shape": [grid.nx, grid.nz],
        "dx": grid.dx,
        "dz": grid.dz,
        "ox": grid.ox,
        "oz": grid.oz,
        "x_stop": grid.x_stop,
        "z_stop": grid.z_stop,
        "rsf_axis_convention": "n1=z,n2=x",
        "array_axis_order": "x_z",
        "prototype": True,
        "field_ready": False,
    }


def _validate_grid(grid: AcousticModelGrid2D) -> AcousticModelGrid2D:
    if not isinstance(grid, AcousticModelGrid2D):
        raise GeometryError("grid must be an AcousticModelGrid2D")
    return grid


def _validate_velocity_unit(velocity_unit: str) -> str:
    if not isinstance(velocity_unit, str) or not velocity_unit:
        raise GeometryError("velocity_unit must be a non-empty string")
    return velocity_unit


def _validate_velocity_array(velocity: Any, grid: AcousticModelGrid2D) -> np.ndarray:
    array = np.asarray(velocity, dtype=float)
    if array.shape != (grid.nx, grid.nz):
        raise GeometryError(f"velocity shape must be {(grid.nx, grid.nz)}")
    if np.any(~np.isfinite(array)):
        raise GeometryError("velocity values must be finite")
    if np.any(array <= 0.0):
        raise GeometryError("velocity values must be positive")
    return np.array(array, dtype=float, copy=True)


@dataclass(frozen=True)
class AcousticVelocityModel2D:
    """Velocity model and JSON-safe metadata for acoustic2d prototypes."""

    velocity: np.ndarray
    grid: AcousticModelGrid2D
    metadata: Mapping[str, Any] | None = field(default=None)

    def __post_init__(self) -> None:
        grid = _validate_grid(self.grid)
        object.__setattr__(self, "velocity", _validate_velocity_array(self.velocity, grid))
        metadata = _json_safe_copy(self.metadata)
        if "model_kind" not in metadata:
            metadata.update(_base_metadata(grid, model_kind="acoustic_velocity_model_2d", velocity_unit="m/s"))
        object.__setattr__(self, "metadata", metadata)

    def to_metadata(self) -> dict[str, Any]:
        """Return a JSON-safe metadata copy."""

        return _json_safe_copy(self.metadata)


def constant_velocity_model_2d(
    grid: AcousticModelGrid2D,
    velocity: float,
    *,
    velocity_unit: str = "m/s",
) -> AcousticVelocityModel2D:
    """Build a constant positive velocity model with shape (nx, nz)."""

    grid = _validate_grid(grid)
    value = _positive_finite_float(velocity, "velocity")
    unit = _validate_velocity_unit(velocity_unit)
    array = np.full((grid.nx, grid.nz), value, dtype=float)
    metadata = _base_metadata(grid, model_kind="constant_velocity_2d", velocity_unit=unit)
    metadata["velocity"] = value
    metadata["anomalies"] = []
    metadata["anomaly_count"] = 0
    return AcousticVelocityModel2D(array, grid, metadata)


def layered_velocity_model_2d(
    grid: AcousticModelGrid2D,
    layers: Sequence[Mapping[str, Any]],
    *,
    background_velocity: float | None = None,
    velocity_unit: str = "m/s",
) -> AcousticVelocityModel2D:
    """Build a horizontal layered velocity model.

    Each layer starts at z_top and applies downward until the next z_top.
    Layers are sorted internally by z_top and recorded in metadata. z_top
    values must lie within sampled grid extents.
    """

    grid = _validate_grid(grid)
    unit = _validate_velocity_unit(velocity_unit)
    if not layers:
        raise GeometryError("layers must contain at least one layer")

    parsed_layers: list[dict[str, float]] = []
    for index, layer in enumerate(layers):
        if not isinstance(layer, Mapping):
            raise GeometryError(f"layers[{index}] must be a mapping")
        if "z_top" not in layer or "velocity" not in layer:
            raise GeometryError(f"layers[{index}] must contain z_top and velocity")
        z_top = _finite_float(layer["z_top"], f"layers[{index}].z_top")
        velocity = _positive_finite_float(layer["velocity"], f"layers[{index}].velocity")
        if not grid.oz <= z_top <= grid.z_stop:
            raise GeometryError(f"layers[{index}].z_top is outside grid z extents")
        parsed_layers.append({"z_top": z_top, "velocity": velocity})

    parsed_layers.sort(key=lambda item: item["z_top"])
    for previous, current in zip(parsed_layers, parsed_layers[1:]):
        if previous["z_top"] == current["z_top"]:
            raise GeometryError("layer z_top values must be unique")

    if background_velocity is None:
        array = np.full((grid.nx, grid.nz), parsed_layers[0]["velocity"], dtype=float)
    else:
        array = np.full(
            (grid.nx, grid.nz),
            _positive_finite_float(background_velocity, "background_velocity"),
            dtype=float,
        )

    z_values = grid.oz + np.arange(grid.nz, dtype=float) * grid.dz
    for layer in parsed_layers:
        array[:, z_values >= layer["z_top"]] = layer["velocity"]

    metadata = _base_metadata(grid, model_kind="layered_velocity_2d", velocity_unit=unit)
    metadata["layers"] = [dict(layer) for layer in parsed_layers]
    metadata["layer_z_tops"] = [layer["z_top"] for layer in parsed_layers]
    metadata["background_velocity"] = None if background_velocity is None else float(background_velocity)
    metadata["interface_geometry"] = "horizontal"
    metadata["smoothing"] = False
    metadata["velocity_gradient"] = False
    metadata["anomalies"] = []
    metadata["anomaly_count"] = 0
    return AcousticVelocityModel2D(array, grid, metadata)


def add_rectangular_velocity_anomaly_2d(
    model: AcousticVelocityModel2D,
    *,
    x_min: float,
    x_max: float,
    z_min: float,
    z_max: float,
    velocity: float | None = None,
    velocity_delta: float | None = None,
) -> AcousticVelocityModel2D:
    """Return a new model with an inclusive rectangular velocity anomaly."""

    base = _validate_model(model)
    x0 = _finite_float(x_min, "x_min")
    x1 = _finite_float(x_max, "x_max")
    z0 = _finite_float(z_min, "z_min")
    z1 = _finite_float(z_max, "z_max")
    if x1 < x0:
        raise GeometryError("x_max must be greater than or equal to x_min")
    if z1 < z0:
        raise GeometryError("z_max must be greater than or equal to z_min")
    _validate_region_overlaps_grid(base.grid, x0, x1, z0, z1, "rectangular anomaly")

    replacement, delta, mode = _validate_anomaly_velocity(velocity, velocity_delta)
    x_values, z_values = _coordinate_mesh(base.grid)
    mask = (x_values >= x0) & (x_values <= x1) & (z_values >= z0) & (z_values <= z1)
    if not np.any(mask):
        raise GeometryError("rectangular anomaly does not include any grid samples")
    anomaly = {
        "kind": "rectangular_velocity_anomaly_2d",
        "x_min": x0,
        "x_max": x1,
        "z_min": z0,
        "z_max": z1,
        "boundary_policy": "inclusive",
        "mode": mode,
        "velocity": replacement,
        "velocity_delta": delta,
        "sample_count": int(np.count_nonzero(mask)),
    }
    return _model_with_anomaly(base, mask, anomaly, replacement=replacement, delta=delta)


def add_circular_velocity_anomaly_2d(
    model: AcousticVelocityModel2D,
    *,
    center_x: float,
    center_z: float,
    radius: float,
    velocity: float | None = None,
    velocity_delta: float | None = None,
) -> AcousticVelocityModel2D:
    """Return a new model with an inclusive-radius circular velocity anomaly."""

    base = _validate_model(model)
    cx = _finite_float(center_x, "center_x")
    cz = _finite_float(center_z, "center_z")
    radius_value = _positive_finite_float(radius, "radius")
    _validate_region_overlaps_grid(
        base.grid,
        cx - radius_value,
        cx + radius_value,
        cz - radius_value,
        cz + radius_value,
        "circular anomaly",
    )

    replacement, delta, mode = _validate_anomaly_velocity(velocity, velocity_delta)
    x_values, z_values = _coordinate_mesh(base.grid)
    mask = (x_values - cx) ** 2 + (z_values - cz) ** 2 <= radius_value**2
    if not np.any(mask):
        raise GeometryError("circular anomaly does not include any grid samples")
    anomaly = {
        "kind": "circular_velocity_anomaly_2d",
        "center_x": cx,
        "center_z": cz,
        "radius": radius_value,
        "boundary_policy": "inclusive_radius",
        "mode": mode,
        "velocity": replacement,
        "velocity_delta": delta,
        "sample_count": int(np.count_nonzero(mask)),
    }
    return _model_with_anomaly(base, mask, anomaly, replacement=replacement, delta=delta)


def velocity_model_summary(model: AcousticVelocityModel2D) -> dict[str, Any]:
    """Return compact JSON-safe velocity model summary metadata."""

    base = _validate_model(model)
    metadata = base.to_metadata()
    anomalies = metadata.get("anomalies", [])
    return {
        "model_kind": metadata.get("model_kind", "acoustic_velocity_model_2d"),
        "grid_nx": base.grid.nx,
        "grid_nz": base.grid.nz,
        "velocity_shape": [base.grid.nx, base.grid.nz],
        "velocity_min": float(np.min(base.velocity)),
        "velocity_max": float(np.max(base.velocity)),
        "velocity_mean": float(np.mean(base.velocity)),
        "anomaly_count": len(anomalies) if isinstance(anomalies, list) else int(metadata.get("anomaly_count", 0)),
        "velocity_unit": metadata.get("velocity_unit", "m/s"),
        "coordinate_frame": base.grid.coordinate_frame,
        "depth_positive": base.grid.depth_positive,
        "prototype": True,
        "field_ready": False,
    }


def _validate_model(model: AcousticVelocityModel2D) -> AcousticVelocityModel2D:
    if not isinstance(model, AcousticVelocityModel2D):
        raise GeometryError("model must be an AcousticVelocityModel2D")
    return model


def _validate_anomaly_velocity(
    velocity: float | None,
    velocity_delta: float | None,
) -> tuple[float | None, float | None, str]:
    if (velocity is None) == (velocity_delta is None):
        raise GeometryError("exactly one of velocity or velocity_delta must be provided")
    if velocity is not None:
        return _positive_finite_float(velocity, "velocity"), None, "replace"
    return None, _finite_float(velocity_delta, "velocity_delta"), "delta"


def _validate_region_overlaps_grid(
    grid: AcousticModelGrid2D,
    x_min: float,
    x_max: float,
    z_min: float,
    z_max: float,
    name: str,
) -> None:
    if x_max < grid.ox or x_min > grid.x_stop or z_max < grid.oz or z_min > grid.z_stop:
        raise GeometryError(f"{name} is outside grid extents")


def _coordinate_mesh(grid: AcousticModelGrid2D) -> tuple[np.ndarray, np.ndarray]:
    x_values = grid.ox + np.arange(grid.nx, dtype=float)[:, np.newaxis] * grid.dx
    z_values = grid.oz + np.arange(grid.nz, dtype=float)[np.newaxis, :] * grid.dz
    return x_values, z_values


def _model_with_anomaly(
    model: AcousticVelocityModel2D,
    mask: np.ndarray,
    anomaly: dict[str, Any],
    *,
    replacement: float | None,
    delta: float | None,
) -> AcousticVelocityModel2D:
    velocity = np.array(model.velocity, dtype=float, copy=True)
    if replacement is not None:
        velocity[mask] = replacement
    else:
        velocity[mask] = velocity[mask] + float(delta)
    if np.any(velocity <= 0.0):
        raise GeometryError("anomaly would create non-positive velocity values")

    metadata = model.to_metadata()
    anomalies = list(metadata.get("anomalies", []))
    anomalies.append(_json_safe_copy(anomaly))
    metadata["model_kind"] = "velocity_model_with_anomalies"
    metadata["base_model_kind"] = metadata.get(
        "base_model_kind",
        model.metadata.get("model_kind", "acoustic_velocity_model_2d"),
    )
    metadata["anomalies"] = anomalies
    metadata["anomaly_count"] = len(anomalies)
    metadata["smoothing"] = False
    metadata["random_model"] = False
    return AcousticVelocityModel2D(velocity, model.grid, metadata)


__all__ = [
    "AcousticVelocityModel2D",
    "add_circular_velocity_anomaly_2d",
    "add_rectangular_velocity_anomaly_2d",
    "constant_velocity_model_2d",
    "layered_velocity_model_2d",
    "velocity_model_summary",
]
