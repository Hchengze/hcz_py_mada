"""L0-1 localization travel-time primitive contract tests."""

from __future__ import annotations

import json
from typing import Any

import numpy as np
import pytest

import pymadagascar
import pymadagascar.api as public_api
from pymadagascar.localization import (
    LocalizationError,
    diffraction_travel_time_2d,
    direct_travel_time_2d,
    euclidean_distance_2d,
    grid_search_point_location_2d,
    grid_search_point_location_velocity_2d,
    travel_time_residuals,
)


def test_euclidean_and_direct_travel_time_match_hand_calculation() -> None:
    receivers = np.array([[3.0, 4.0], [6.0, 8.0]], dtype=np.float64)
    distances = euclidean_distance_2d(receivers, np.array([0.0, 0.0]))

    np.testing.assert_allclose(distances, np.array([5.0, 10.0]))
    np.testing.assert_allclose(
        direct_travel_time_2d([0.0, 0.0], receivers, velocity=2.0),
        np.array([2.5, 5.0]),
    )
    assert direct_travel_time_2d([0.0, 0.0], [3.0, 4.0], 5.0) == pytest.approx(1.0)


def test_diffraction_travel_time_matches_source_target_receiver_path() -> None:
    source = np.array([0.0, 0.0])
    diffractor = np.array([3.0, 4.0])
    receivers = np.array([[6.0, 8.0], [3.0, 8.0]], dtype=np.float64)

    times = diffraction_travel_time_2d(source, receivers, diffractor, velocity=2.0)

    np.testing.assert_allclose(times, np.array([(5.0 + 5.0) / 2.0, (5.0 + 4.0) / 2.0]))


@pytest.mark.parametrize("velocity", [0.0, -1.0, np.nan, np.inf])
def test_velocity_must_be_positive_finite(velocity: float) -> None:
    with pytest.raises(LocalizationError, match="velocity"):
        direct_travel_time_2d([0.0, 0.0], [1.0, 0.0], velocity)


@pytest.mark.parametrize(
    ("source", "receiver", "message"),
    [
        ([0.0, np.nan], [1.0, 0.0], "finite"),
        ([0.0, 0.0, 1.0], [1.0, 0.0], "shape"),
        ([0.0, 0.0], [[1.0, 0.0, 2.0]], "shape"),
    ],
)
def test_coordinate_validation_rejects_nonfinite_or_invalid_shapes(
    source: list[float],
    receiver: list[float] | list[list[float]],
    message: str,
) -> None:
    with pytest.raises(LocalizationError, match=message):
        direct_travel_time_2d(source, receiver, 100.0)


def test_travel_time_residuals_use_observed_minus_predicted_convention() -> None:
    predicted = np.array([1.0, 2.0, 4.0])
    observed = np.array([1.5, 1.0, 5.0])

    residual = travel_time_residuals(predicted, observed)
    weighted = travel_time_residuals(predicted, observed, weights=np.array([4.0, 1.0, 9.0]))

    np.testing.assert_allclose(residual, np.array([0.5, -1.0, 1.0]))
    np.testing.assert_allclose(weighted, np.array([1.0, -1.0, 3.0]))


@pytest.mark.parametrize("weights", [[1.0, 0.0], [1.0, np.inf], [[1.0, 2.0]]])
def test_weights_must_be_positive_finite_and_shape_compatible(weights: Any) -> None:
    with pytest.raises(LocalizationError, match="weights"):
        travel_time_residuals([1.0, 2.0], [1.0, 2.0], weights=weights)


def test_grid_search_recovers_known_diffractor_and_metadata_is_json_safe() -> None:
    source = np.array([0.0, 0.0])
    receivers = np.column_stack(
        [np.linspace(-10.0, 10.0, 9), np.zeros(9, dtype=np.float64)]
    )
    true_diffractor = np.array([2.0, 6.0])
    velocity = 300.0
    observed = diffraction_travel_time_2d(source, receivers, true_diffractor, velocity)

    result = grid_search_point_location_2d(
        source,
        receivers,
        observed,
        velocity,
        x_grid=np.arange(-4.0, 5.0, 1.0),
        z_grid=np.arange(2.0, 9.0, 1.0),
    )

    assert result.best_x == pytest.approx(true_diffractor[0])
    assert result.best_z == pytest.approx(true_diffractor[1])
    assert result.best_objective == pytest.approx(0.0, abs=1e-24)
    assert result.objective_grid.shape == (7, 9)
    np.testing.assert_allclose(result.predicted_times_at_best, observed)
    np.testing.assert_allclose(result.residuals_at_best, np.zeros_like(observed), atol=1e-14)
    assert result.metadata["method"] == "grid_search_point_location_2d"
    assert result.metadata["travel_time_model"] == "source_diffractor_receiver_kinematic"
    assert result.metadata["residual_convention"] == "observed_minus_predicted"
    assert result.metadata["coordinate_frame"] == "local_2d_x_z"
    assert result.metadata["depth_positive"] == "down"
    assert result.metadata["grid_shape"] == [7, 9]
    assert result.metadata["receiver_count"] == receivers.shape[0]
    json.dumps(result.metadata)
    assert not _contains_local_absolute_path(result.metadata)


def test_grid_search_weights_change_objective_but_not_exact_best_location() -> None:
    source = np.array([0.0, 0.0])
    receivers = np.array([[-5.0, 0.0], [0.0, 0.0], [5.0, 0.0]], dtype=np.float64)
    true_diffractor = np.array([0.0, 4.0])
    observed = diffraction_travel_time_2d(source, receivers, true_diffractor, 200.0)

    result = grid_search_point_location_2d(
        source,
        receivers,
        observed,
        200.0,
        x_grid=np.array([-1.0, 0.0, 1.0]),
        z_grid=np.array([3.0, 4.0, 5.0]),
        weights=np.array([10.0, 1.0, 2.0]),
    )

    assert result.best_x == pytest.approx(0.0)
    assert result.best_z == pytest.approx(4.0)
    assert result.metadata["weighting"] == "positive_weights"


def test_grid_search_rejects_incompatible_inputs() -> None:
    source = np.array([0.0, 0.0])
    receivers = np.array([[0.0, 0.0], [1.0, 0.0]])

    with pytest.raises(LocalizationError, match="observed_times length"):
        grid_search_point_location_2d(source, receivers, [1.0], 100.0, [0.0], [1.0])
    with pytest.raises(LocalizationError, match="x_grid"):
        grid_search_point_location_2d(source, receivers, [1.0, 1.1], 100.0, [], [1.0])
    with pytest.raises(LocalizationError, match="z_grid"):
        grid_search_point_location_2d(source, receivers, [1.0, 1.1], 100.0, [0.0], [])


def test_variable_velocity_closed_form_slowness_recovers_known_location_and_velocity() -> None:
    source = np.array([0.0, 0.0])
    receivers = np.column_stack(
        [np.linspace(-8.0, 12.0, 11), np.zeros(11, dtype=np.float64)]
    )
    true_diffractor = np.array([3.0, 5.0])
    true_velocity = 250.0
    observed = diffraction_travel_time_2d(source, receivers, true_diffractor, true_velocity)

    result = grid_search_point_location_velocity_2d(
        source,
        receivers,
        observed,
        x_grid=np.arange(-2.0, 7.0, 1.0),
        z_grid=np.arange(2.0, 8.0, 1.0),
        velocity_bounds=(150.0, 400.0),
    )

    assert result.best_x == pytest.approx(true_diffractor[0])
    assert result.best_z == pytest.approx(true_diffractor[1])
    assert result.best_velocity == pytest.approx(true_velocity)
    assert result.best_objective == pytest.approx(0.0, abs=1e-24)
    assert result.objective_grid.shape == (6, 9)
    assert result.velocity_grid.shape == (6, 9)
    assert np.all(result.velocity_grid >= 150.0)
    assert np.all(result.velocity_grid <= 400.0)
    np.testing.assert_allclose(result.predicted_times_at_best, observed)
    np.testing.assert_allclose(result.residuals_at_best, np.zeros_like(observed), atol=1e-14)
    assert result.metadata["method"] == "grid_search_point_location_velocity_2d"
    assert result.metadata["velocity_mode"] == "closed_form_slowness"
    assert result.metadata["travel_time_model"] == "source_diffractor_receiver_kinematic"
    assert result.metadata["residual_convention"] == "observed_minus_predicted"
    assert result.metadata["coordinate_frame"] == "local_2d_x_z"
    assert result.metadata["depth_positive"] == "down"
    assert result.metadata["grid_shape"] == [6, 9]
    assert result.metadata["grid_axis_order"] == "z_x"
    assert result.metadata["receiver_count"] == receivers.shape[0]
    assert result.metadata["prototype"] is True
    assert result.metadata["automatic_picking"] is False
    assert result.metadata["field_ready"] is False
    json.dumps(result.metadata)
    assert not _contains_local_absolute_path(result.metadata)


def test_variable_velocity_explicit_velocity_grid_recovers_known_model() -> None:
    source = np.array([0.0, 0.0])
    receivers = np.array(
        [[-6.0, 0.0], [-3.0, 0.0], [0.0, 0.0], [3.0, 0.0], [6.0, 0.0]],
        dtype=np.float64,
    )
    true_diffractor = np.array([-1.0, 4.0])
    true_velocity = 320.0
    observed = diffraction_travel_time_2d(source, receivers, true_diffractor, true_velocity)

    result = grid_search_point_location_velocity_2d(
        source,
        receivers,
        observed,
        x_grid=np.array([-2.0, -1.0, 0.0, 1.0]),
        z_grid=np.array([3.0, 4.0, 5.0]),
        velocity_grid=np.array([280.0, 300.0, 320.0, 340.0]),
    )

    assert result.best_x == pytest.approx(true_diffractor[0])
    assert result.best_z == pytest.approx(true_diffractor[1])
    assert result.best_velocity == pytest.approx(true_velocity)
    assert result.best_objective == pytest.approx(0.0, abs=1e-24)
    assert result.objective_grid.shape == (3, 4)
    assert result.velocity_grid.shape == (3, 4)
    assert result.metadata["velocity_mode"] == "explicit_velocity_grid"
    assert result.metadata["velocity_grid_count"] == 4
    np.testing.assert_allclose(
        result.predicted_times_at_best,
        diffraction_travel_time_2d(source, receivers, true_diffractor, true_velocity),
    )


def test_variable_velocity_weights_follow_weighted_objective_convention() -> None:
    source = np.array([0.0, 0.0])
    receivers = np.array([[-4.0, 0.0], [0.0, 0.0], [4.0, 0.0]], dtype=np.float64)
    target = np.array([1.0, 3.0])
    observed = diffraction_travel_time_2d(source, receivers, target, 200.0)
    observed = observed + np.array([0.02, -0.01, 0.03])
    weights = np.array([4.0, 1.0, 9.0])

    result = grid_search_point_location_velocity_2d(
        source,
        receivers,
        observed,
        x_grid=np.array([1.0]),
        z_grid=np.array([3.0]),
        velocity_grid=np.array([200.0]),
        weights=weights,
    )

    predicted = diffraction_travel_time_2d(source, receivers, target, 200.0)
    residuals = observed - predicted
    expected_objective = 0.5 * float(np.sum(weights * residuals * residuals))

    assert result.metadata["weighting"] == "positive_weights"
    assert result.best_objective == pytest.approx(expected_objective)
    np.testing.assert_allclose(result.residuals_at_best, residuals)


def test_variable_velocity_bounds_clip_best_velocity_to_requested_range() -> None:
    source = np.array([0.0, 0.0])
    receivers = np.array([[-5.0, 0.0], [0.0, 0.0], [5.0, 0.0]], dtype=np.float64)
    target = np.array([0.0, 4.0])
    observed = diffraction_travel_time_2d(source, receivers, target, 500.0)

    result = grid_search_point_location_velocity_2d(
        source,
        receivers,
        observed,
        x_grid=np.array([0.0]),
        z_grid=np.array([4.0]),
        velocity_bounds=(100.0, 300.0),
    )

    assert result.best_velocity == pytest.approx(300.0)
    assert np.all(result.velocity_grid <= 300.0)


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"velocity_bounds": (100.0,)},
        {"velocity_bounds": (0.0, 100.0)},
        {"velocity_bounds": (200.0, 100.0)},
        {"velocity_bounds": (100.0, 200.0), "velocity_grid": [100.0, 200.0]},
        {"velocity_grid": []},
        {"velocity_grid": [100.0, 0.0]},
        {"velocity_grid": [100.0, np.nan]},
    ],
)
def test_variable_velocity_rejects_invalid_velocity_modes(kwargs: dict[str, Any]) -> None:
    source = np.array([0.0, 0.0])
    receivers = np.array([[0.0, 0.0], [1.0, 0.0]], dtype=np.float64)
    observed = np.array([0.01, 0.02])

    with pytest.raises(LocalizationError, match="velocity"):
        grid_search_point_location_velocity_2d(
            source,
            receivers,
            observed,
            x_grid=[0.0],
            z_grid=[1.0],
            **kwargs,
        )


def test_variable_velocity_rejects_shape_mismatch_and_invalid_weights() -> None:
    source = np.array([0.0, 0.0])
    receivers = np.array([[0.0, 0.0], [1.0, 0.0]], dtype=np.float64)

    with pytest.raises(LocalizationError, match="observed_times length"):
        grid_search_point_location_velocity_2d(
            source,
            receivers,
            [0.01],
            x_grid=[0.0],
            z_grid=[1.0],
            velocity_bounds=(100.0, 300.0),
        )
    with pytest.raises(LocalizationError, match="weights"):
        grid_search_point_location_velocity_2d(
            source,
            receivers,
            [0.01, 0.02],
            x_grid=[0.0],
            z_grid=[1.0],
            velocity_bounds=(100.0, 300.0),
            weights=[1.0, np.inf],
        )


def test_localization_primitives_are_not_root_or_api_exports() -> None:
    for namespace in (pymadagascar, public_api):
        assert not hasattr(namespace, "grid_search_point_location_2d")
        assert not hasattr(namespace, "grid_search_point_location_velocity_2d")
        assert not hasattr(namespace, "direct_travel_time_2d")


def _contains_local_absolute_path(value: Any) -> bool:
    if isinstance(value, dict):
        return any(_contains_local_absolute_path(item) for item in value.values())
    if isinstance(value, list | tuple):
        return any(_contains_local_absolute_path(item) for item in value)
    if isinstance(value, str):
        normalized = value.replace("\\\\", "/")
        return any(
            marker in normalized
            for marker in ("E:/", "D:/", "/home/hcz", "/mnt/")
        )
    return False
