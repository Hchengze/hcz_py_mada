"""2D kinematic travel-time primitives for small localization prototypes.

This module is a pure-Python prototype surface. It provides deterministic
local-coordinate helpers for learning, tests, and small workflow experiments;
it is not a full Madagascar command clone, automatic picker, eikonal solver,
or field-scale location engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


class LocalizationError(ValueError):
    """Raised when localization inputs or parameters are invalid."""


@dataclass(frozen=True)
class LocalizationGridSearchResult:
    """Result from a small 2D point-location grid search.

    objective_grid has shape (len(z_grid), len(x_grid)). Coordinates use the
    local x-z convention: x is horizontal distance and z is depth, positive
    downward.
    """

    best_x: float
    best_z: float
    best_objective: float
    objective_grid: np.ndarray
    predicted_times_at_best: np.ndarray
    residuals_at_best: np.ndarray
    metadata: dict[str, Any]


@dataclass(frozen=True)
class VariableVelocityLocalizationGridSearchResult:
    """Result from a small 2D point-location and velocity grid search.

    objective_grid has shape (len(z_grid), len(x_grid)) and stores the minimum
    objective found for each x-z candidate after estimating or scanning the
    homogeneous velocity. velocity_grid has the same shape and stores the
    selected velocity for each x-z candidate. Coordinates use the local x-z
    convention: x is horizontal distance and z is depth, positive downward.
    """

    best_x: float
    best_z: float
    best_velocity: float
    best_objective: float
    objective_grid: np.ndarray
    velocity_grid: np.ndarray
    predicted_times_at_best: np.ndarray
    residuals_at_best: np.ndarray
    metadata: dict[str, Any]


def euclidean_distance_2d(points: Any, origin: Any) -> np.ndarray:
    """Return Euclidean distance from 2D origin to points.

    points must have shape (..., 2) and origin must have shape (2,). Units are
    supplied by the caller and are not converted here.
    """

    point_array = _as_points_2d(points, "points")
    origin_array = _as_point_2d(origin, "origin")
    return np.linalg.norm(point_array - origin_array, axis=-1)


def direct_travel_time_2d(source_xy: Any, receiver_xy: Any, velocity: float) -> np.ndarray:
    """Return direct travel time ||receiver - source|| / velocity."""

    speed = _positive_finite_scalar(velocity, "velocity")
    source = _as_point_2d(source_xy, "source_xy")
    receiver = _as_points_2d(receiver_xy, "receiver_xy")
    return euclidean_distance_2d(receiver, source) / speed


def diffraction_travel_time_2d(
    source_xy: Any,
    receiver_xy: Any,
    diffractor_xy: Any,
    velocity: float,
) -> np.ndarray:
    """Return source-diffractor-receiver kinematic diffraction travel time.

    The model is (||diffractor - source|| + ||receiver - diffractor||) /
    velocity. It deliberately models only travel time, not amplitude,
    waveforms, frequency dispersion, attenuation, gauge-length strain response,
    or automatic picking.
    """

    speed = _positive_finite_scalar(velocity, "velocity")
    source = _as_point_2d(source_xy, "source_xy")
    diffractor = _as_point_2d(diffractor_xy, "diffractor_xy")
    receiver = _as_points_2d(receiver_xy, "receiver_xy")
    source_to_diffractor = float(euclidean_distance_2d(diffractor, source))
    receiver_to_diffractor = euclidean_distance_2d(receiver, diffractor)
    return (source_to_diffractor + receiver_to_diffractor) / speed


def travel_time_residuals(predicted: Any, observed: Any, weights: Any | None = None) -> np.ndarray:
    """Return travel-time residuals with observed-minus-predicted convention.

    Without weights, this is observed - predicted. With positive finite
    weights, the returned residuals are sqrt(weights) * (observed - predicted),
    so 0.5 * sum(residuals**2) equals the weighted least-squares objective.
    """

    predicted_array = _finite_array(predicted, "predicted")
    observed_array = _finite_array(observed, "observed")
    try:
        residual = observed_array - predicted_array
    except ValueError as exc:
        raise LocalizationError("predicted and observed must be broadcast-compatible") from exc
    if weights is None:
        return np.asarray(residual, dtype=np.float64)
    weight_array = _positive_finite_weights(weights, np.shape(residual))
    return np.sqrt(weight_array) * residual


def grid_search_point_location_2d(
    source_xy: Any,
    receiver_xy: Any,
    observed_times: Any,
    velocity: float,
    x_grid: Any,
    z_grid: Any,
    *,
    weights: Any | None = None,
) -> LocalizationGridSearchResult:
    """Locate a 2D point diffractor by exhaustive deterministic grid search.

    For each candidate m = (x, z), the objective is
    0.5 * sum_i weights_i * (observed_i - predicted_i(m))**2.

    The objective grid is indexed as objective_grid[iz, ix] with shape
    (len(z_grid), len(x_grid)). x is horizontal coordinate and z is depth,
    positive downward.
    """

    source = _as_point_2d(source_xy, "source_xy")
    receivers = _as_receiver_array(receiver_xy)
    speed = _positive_finite_scalar(velocity, "velocity")
    observed = _finite_1d(observed_times, "observed_times")
    if observed.size != receivers.shape[0]:
        raise LocalizationError("observed_times length must match receiver count")

    x_values = _finite_1d(x_grid, "x_grid")
    z_values = _finite_1d(z_grid, "z_grid")
    if x_values.size == 0:
        raise LocalizationError("x_grid must contain at least one candidate")
    if z_values.size == 0:
        raise LocalizationError("z_grid must contain at least one candidate")

    if weights is None:
        weight_values = np.ones_like(observed, dtype=np.float64)
        weighting = "none"
    else:
        weight_values = _positive_finite_weights(weights, observed.shape)
        weighting = "positive_weights"

    objective_grid = np.empty((z_values.size, x_values.size), dtype=np.float64)
    for iz, z_value in enumerate(z_values):
        for ix, x_value in enumerate(x_values):
            candidate = np.array([x_value, z_value], dtype=np.float64)
            predicted = diffraction_travel_time_2d(source, receivers, candidate, speed)
            residual = observed - predicted
            objective_grid[iz, ix] = 0.5 * float(np.sum(weight_values * residual * residual))

    best_flat_index = int(np.argmin(objective_grid))
    best_iz, best_ix = np.unravel_index(best_flat_index, objective_grid.shape)
    best_x = float(x_values[best_ix])
    best_z = float(z_values[best_iz])
    best_candidate = np.array([best_x, best_z], dtype=np.float64)
    predicted_at_best = np.asarray(
        diffraction_travel_time_2d(source, receivers, best_candidate, speed),
        dtype=np.float64,
    )
    residuals_at_best = np.asarray(observed - predicted_at_best, dtype=np.float64)
    best_objective = float(objective_grid[best_iz, best_ix])

    metadata: dict[str, Any] = {
        "method": "grid_search_point_location_2d",
        "travel_time_model": "source_diffractor_receiver_kinematic",
        "residual_convention": "observed_minus_predicted",
        "objective": "0.5_sum_weighted_squared_residuals",
        "coordinate_frame": "local_2d_x_z",
        "depth_positive": "down",
        "distance_unit": "m",
        "time_unit": "s",
        "velocity_unit": "m/s",
        "grid_shape": [int(z_values.size), int(x_values.size)],
        "grid_axis_order": "z_x",
        "receiver_count": int(receivers.shape[0]),
        "weighting": weighting,
        "prototype": True,
        "stable_root_api": False,
        "automatic_picking": False,
        "field_performance_claim": False,
    }
    return LocalizationGridSearchResult(
        best_x=best_x,
        best_z=best_z,
        best_objective=best_objective,
        objective_grid=objective_grid,
        predicted_times_at_best=predicted_at_best,
        residuals_at_best=residuals_at_best,
        metadata=metadata,
    )


def grid_search_point_location_velocity_2d(
    source_xy: Any,
    receiver_xy: Any,
    observed_times: Any,
    x_grid: Any,
    z_grid: Any,
    *,
    velocity_bounds: tuple[float, float] | None = None,
    velocity_grid: Any | None = None,
    weights: Any | None = None,
) -> VariableVelocityLocalizationGridSearchResult:
    """Locate a 2D point diffractor while estimating homogeneous velocity.

    For each candidate m = (x, z), path_i(m) is the
    source-diffractor-receiver distance. The residual convention is
    observed_i - path_i / velocity, and the objective is
    0.5 * sum_i weights_i * residual_i**2.

    Exactly one of velocity_bounds or velocity_grid must be provided. With
    velocity_bounds=(vmin, vmax), the prototype estimates bounded slowness for
    each x-z candidate by weighted least squares and then converts it to
    velocity. With velocity_grid, it scans the supplied positive finite
    velocities and stores only the best velocity/objective per x-z candidate,
    not a full 3D objective volume.
    """

    source = _as_point_2d(source_xy, "source_xy")
    receivers = _as_receiver_array(receiver_xy)
    observed = _finite_1d(observed_times, "observed_times")
    if observed.size != receivers.shape[0]:
        raise LocalizationError("observed_times length must match receiver count")

    x_values = _finite_1d(x_grid, "x_grid")
    z_values = _finite_1d(z_grid, "z_grid")
    if x_values.size == 0:
        raise LocalizationError("x_grid must contain at least one candidate")
    if z_values.size == 0:
        raise LocalizationError("z_grid must contain at least one candidate")

    if weights is None:
        weight_values = np.ones_like(observed, dtype=np.float64)
        weighting = "none"
    else:
        weight_values = _positive_finite_weights(weights, observed.shape)
        weighting = "positive_weights"

    has_velocity_bounds = velocity_bounds is not None
    has_velocity_grid = velocity_grid is not None
    if has_velocity_bounds == has_velocity_grid:
        raise LocalizationError("provide exactly one of velocity_bounds or velocity_grid")

    if has_velocity_bounds:
        vmin, vmax = _velocity_bounds(velocity_bounds)
        velocity_values = None
        velocity_mode = "closed_form_slowness"
        velocity_metadata: dict[str, Any] = {
            "velocity_bounds": [vmin, vmax],
            "slowness_bounds": [1.0 / vmax, 1.0 / vmin],
        }
    else:
        velocity_values = _velocity_candidates(velocity_grid)
        velocity_mode = "explicit_velocity_grid"
        velocity_metadata = {
            "velocity_grid_count": int(velocity_values.size),
            "velocity_grid_min": float(np.min(velocity_values)),
            "velocity_grid_max": float(np.max(velocity_values)),
        }

    objective_grid = np.empty((z_values.size, x_values.size), dtype=np.float64)
    best_velocity_grid = np.empty_like(objective_grid)
    for iz, z_value in enumerate(z_values):
        for ix, x_value in enumerate(x_values):
            candidate = np.array([x_value, z_value], dtype=np.float64)
            path_lengths = _diffraction_path_lengths_2d(source, receivers, candidate)
            if velocity_values is None:
                velocity = _bounded_velocity_from_paths(
                    path_lengths,
                    observed,
                    weight_values,
                    vmin,
                    vmax,
                )
                predicted = path_lengths / velocity
                residual = observed - predicted
                objective = _weighted_objective(residual, weight_values)
            else:
                velocity, objective = _best_velocity_from_grid(
                    path_lengths,
                    observed,
                    weight_values,
                    velocity_values,
                )
            objective_grid[iz, ix] = objective
            best_velocity_grid[iz, ix] = velocity

    best_flat_index = int(np.argmin(objective_grid))
    best_iz, best_ix = np.unravel_index(best_flat_index, objective_grid.shape)
    best_x = float(x_values[best_ix])
    best_z = float(z_values[best_iz])
    best_velocity = float(best_velocity_grid[best_iz, best_ix])
    best_candidate = np.array([best_x, best_z], dtype=np.float64)
    predicted_at_best = np.asarray(
        diffraction_travel_time_2d(source, receivers, best_candidate, best_velocity),
        dtype=np.float64,
    )
    residuals_at_best = np.asarray(observed - predicted_at_best, dtype=np.float64)
    best_objective = float(objective_grid[best_iz, best_ix])

    metadata: dict[str, Any] = {
        "method": "grid_search_point_location_velocity_2d",
        "travel_time_model": "source_diffractor_receiver_kinematic",
        "velocity_mode": velocity_mode,
        "residual_convention": "observed_minus_predicted",
        "objective": "0.5_sum_weighted_squared_residuals",
        "coordinate_frame": "local_2d_x_z",
        "depth_positive": "down",
        "distance_unit": "m",
        "time_unit": "s",
        "velocity_unit": "m/s",
        "grid_shape": [int(z_values.size), int(x_values.size)],
        "grid_axis_order": "z_x",
        "objective_grid_shape": [int(z_values.size), int(x_values.size)],
        "velocity_grid_shape": [int(z_values.size), int(x_values.size)],
        "objective_grid_representation": "minimum_objective_per_z_x_candidate",
        "velocity_grid_representation": "selected_velocity_per_z_x_candidate",
        "receiver_count": int(receivers.shape[0]),
        "weighting": weighting,
        "prototype": True,
        "stable_root_api": False,
        "cli": False,
        "automatic_picking": False,
        "uncertainty_estimation": False,
        "field_ready": False,
        "field_performance_claim": False,
    }
    metadata.update(velocity_metadata)
    return VariableVelocityLocalizationGridSearchResult(
        best_x=best_x,
        best_z=best_z,
        best_velocity=best_velocity,
        best_objective=best_objective,
        objective_grid=objective_grid,
        velocity_grid=best_velocity_grid,
        predicted_times_at_best=predicted_at_best,
        residuals_at_best=residuals_at_best,
        metadata=metadata,
    )


def _as_point_2d(value: Any, name: str) -> np.ndarray:
    array = _finite_array(value, name)
    if array.shape != (2,):
        raise LocalizationError(f"{name} must have shape (2,)")
    return np.asarray(array, dtype=np.float64)


def _as_points_2d(value: Any, name: str) -> np.ndarray:
    array = _finite_array(value, name)
    if array.shape == (2,):
        return np.asarray(array, dtype=np.float64)
    if array.ndim < 1 or array.shape[-1] != 2:
        raise LocalizationError(f"{name} must have shape (..., 2)")
    return np.asarray(array, dtype=np.float64)


def _as_receiver_array(value: Any) -> np.ndarray:
    array = _as_points_2d(value, "receiver_xy")
    if array.shape == (2,):
        return array.reshape(1, 2)
    return array.reshape(-1, 2)


def _finite_array(value: Any, name: str) -> np.ndarray:
    try:
        array = np.asarray(value, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise LocalizationError(f"{name} must be numeric") from exc
    if not bool(np.all(np.isfinite(array))):
        raise LocalizationError(f"{name} must contain only finite values")
    return array


def _finite_1d(value: Any, name: str) -> np.ndarray:
    array = _finite_array(value, name)
    if array.ndim != 1:
        raise LocalizationError(f"{name} must be 1D")
    return np.asarray(array, dtype=np.float64)


def _positive_finite_scalar(value: Any, name: str) -> float:
    try:
        scalar = float(value)
    except (TypeError, ValueError) as exc:
        raise LocalizationError(f"{name} must be a positive finite scalar") from exc
    if not np.isfinite(scalar) or scalar <= 0.0:
        raise LocalizationError(f"{name} must be a positive finite scalar")
    return scalar


def _positive_finite_weights(weights: Any, shape: tuple[int, ...]) -> np.ndarray:
    weight_array = _finite_array(weights, "weights")
    try:
        broadcast = np.broadcast_to(weight_array, shape)
    except ValueError as exc:
        raise LocalizationError("weights must be broadcast-compatible with residuals") from exc
    if not bool(np.all(broadcast > 0.0)):
        raise LocalizationError("weights must be positive finite values")
    return np.asarray(broadcast, dtype=np.float64)


def _velocity_bounds(value: Any) -> tuple[float, float]:
    bounds = _finite_1d(value, "velocity_bounds")
    if bounds.shape != (2,):
        raise LocalizationError("velocity_bounds must have shape (2,)")
    vmin = float(bounds[0])
    vmax = float(bounds[1])
    if vmin <= 0.0 or vmax <= 0.0 or vmin > vmax:
        raise LocalizationError("velocity_bounds must be positive finite values with vmin <= vmax")
    return vmin, vmax


def _velocity_candidates(value: Any) -> np.ndarray:
    candidates = _finite_1d(value, "velocity_grid")
    if candidates.size == 0:
        raise LocalizationError("velocity_grid must contain at least one candidate")
    if not bool(np.all(candidates > 0.0)):
        raise LocalizationError("velocity_grid must contain positive finite values")
    return np.asarray(candidates, dtype=np.float64)


def _diffraction_path_lengths_2d(
    source: np.ndarray,
    receivers: np.ndarray,
    diffractor: np.ndarray,
) -> np.ndarray:
    source_to_diffractor = float(euclidean_distance_2d(diffractor, source))
    receiver_to_diffractor = euclidean_distance_2d(receivers, diffractor)
    return np.asarray(source_to_diffractor + receiver_to_diffractor, dtype=np.float64)


def _bounded_velocity_from_paths(
    path_lengths: np.ndarray,
    observed: np.ndarray,
    weights: np.ndarray,
    vmin: float,
    vmax: float,
) -> float:
    denominator = float(np.sum(weights * path_lengths * path_lengths))
    if denominator <= 0.0:
        raise LocalizationError("path lengths must not all be zero for velocity estimation")
    estimated_slowness = float(np.sum(weights * path_lengths * observed) / denominator)
    slowness_min = 1.0 / vmax
    slowness_max = 1.0 / vmin
    bounded_slowness = float(np.clip(estimated_slowness, slowness_min, slowness_max))
    return 1.0 / bounded_slowness


def _best_velocity_from_grid(
    path_lengths: np.ndarray,
    observed: np.ndarray,
    weights: np.ndarray,
    velocity_values: np.ndarray,
) -> tuple[float, float]:
    best_velocity = float(velocity_values[0])
    predicted = path_lengths / best_velocity
    best_objective = _weighted_objective(observed - predicted, weights)
    for velocity in velocity_values[1:]:
        speed = float(velocity)
        predicted = path_lengths / speed
        objective = _weighted_objective(observed - predicted, weights)
        if objective < best_objective:
            best_velocity = speed
            best_objective = objective
    return best_velocity, best_objective


def _weighted_objective(residual: np.ndarray, weights: np.ndarray) -> float:
    return 0.5 * float(np.sum(weights * residual * residual))
