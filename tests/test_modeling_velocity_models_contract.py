import json

import numpy as np
import pytest

from pymadagascar.modeling import (
    AcousticModelGrid2D,
    AcousticVelocityModel2D,
    GeometryError,
    add_circular_velocity_anomaly_2d,
    add_rectangular_velocity_anomaly_2d,
    constant_velocity_model_2d,
    layered_velocity_model_2d,
    velocity_model_summary,
)


def _grid() -> AcousticModelGrid2D:
    return AcousticModelGrid2D(nx=6, nz=5, dx=10.0, dz=5.0, ox=100.0, oz=0.0)


def _assert_no_local_paths(payload: object) -> None:
    text = json.dumps(payload, sort_keys=True)
    for marker in ("E:\\", "D:\\", "/home/hcz", "/mnt/"):
        assert marker not in text


def test_constant_velocity_model_has_acoustic2d_shape_and_metadata() -> None:
    grid = _grid()

    model = constant_velocity_model_2d(grid, 1800.0)

    assert isinstance(model, AcousticVelocityModel2D)
    assert model.grid is grid
    assert model.velocity.shape == (grid.nx, grid.nz)
    assert np.all(model.velocity == pytest.approx(1800.0))
    metadata = model.to_metadata()
    assert metadata["model_kind"] == "constant_velocity_2d"
    assert metadata["velocity_unit"] == "m/s"
    assert metadata["coordinate_frame"] == "local_2d_x_z"
    assert metadata["depth_positive"] == "down"
    assert metadata["velocity_shape"] == [grid.nx, grid.nz]
    assert metadata["rsf_axis_convention"] == "n1=z,n2=x"
    json.dumps(metadata, sort_keys=True)
    _assert_no_local_paths(metadata)


def test_velocity_model_dataclass_copies_velocity_array() -> None:
    grid = _grid()
    array = np.full((grid.nx, grid.nz), 1500.0)

    model = AcousticVelocityModel2D(array, grid, {"model_kind": "manual_velocity_2d"})
    array[0, 0] = 999.0

    assert model.velocity[0, 0] == pytest.approx(1500.0)


def test_layered_velocity_model_uses_physical_z_tops_and_sorts_layers() -> None:
    grid = _grid()

    model = layered_velocity_model_2d(
        grid,
        [
            {"z_top": 10.0, "velocity": 2000.0},
            {"z_top": 0.0, "velocity": 1500.0},
            {"z_top": 20.0, "velocity": 2400.0},
        ],
    )

    np.testing.assert_allclose(model.velocity[:, 0], 1500.0)
    np.testing.assert_allclose(model.velocity[:, 1], 1500.0)
    np.testing.assert_allclose(model.velocity[:, 2], 2000.0)
    np.testing.assert_allclose(model.velocity[:, 3], 2000.0)
    np.testing.assert_allclose(model.velocity[:, 4], 2400.0)
    metadata = model.to_metadata()
    assert metadata["model_kind"] == "layered_velocity_2d"
    assert metadata["layer_z_tops"] == [0.0, 10.0, 20.0]
    assert metadata["interface_geometry"] == "horizontal"
    assert metadata["smoothing"] is False
    assert metadata["velocity_gradient"] is False
    json.dumps(metadata, sort_keys=True)
    _assert_no_local_paths(metadata)


def test_rectangular_anomaly_uses_inclusive_physical_coordinates_without_in_place_change() -> None:
    grid = _grid()
    base = constant_velocity_model_2d(grid, 1800.0)

    model = add_rectangular_velocity_anomaly_2d(
        base,
        x_min=110.0,
        x_max=130.0,
        z_min=5.0,
        z_max=15.0,
        velocity=1600.0,
    )

    assert np.all(base.velocity == pytest.approx(1800.0))
    np.testing.assert_allclose(model.velocity[1:4, 1:4], 1600.0)
    assert model.velocity[0, 1] == pytest.approx(1800.0)
    assert model.velocity[4, 3] == pytest.approx(1800.0)
    metadata = model.to_metadata()
    assert metadata["model_kind"] == "velocity_model_with_anomalies"
    assert metadata["anomaly_count"] == 1
    assert metadata["anomalies"][0]["kind"] == "rectangular_velocity_anomaly_2d"
    assert metadata["anomalies"][0]["boundary_policy"] == "inclusive"
    assert metadata["anomalies"][0]["sample_count"] == 9
    json.dumps(metadata, sort_keys=True)
    _assert_no_local_paths(metadata)


def test_circular_anomaly_uses_inclusive_radius_and_delta_mode() -> None:
    grid = _grid()
    base = constant_velocity_model_2d(grid, 2000.0)

    model = add_circular_velocity_anomaly_2d(
        base,
        center_x=120.0,
        center_z=10.0,
        radius=10.0,
        velocity_delta=-300.0,
    )

    assert model.velocity[2, 2] == pytest.approx(1700.0)
    assert model.velocity[1, 2] == pytest.approx(1700.0)
    assert model.velocity[3, 2] == pytest.approx(1700.0)
    assert model.velocity[2, 0] == pytest.approx(1700.0)
    assert model.velocity[0, 2] == pytest.approx(2000.0)
    assert np.all(base.velocity == pytest.approx(2000.0))
    metadata = model.to_metadata()
    assert metadata["anomalies"][0]["kind"] == "circular_velocity_anomaly_2d"
    assert metadata["anomalies"][0]["mode"] == "delta"
    assert metadata["anomalies"][0]["boundary_policy"] == "inclusive_radius"
    json.dumps(metadata, sort_keys=True)
    _assert_no_local_paths(metadata)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"velocity": 1600.0, "velocity_delta": -100.0},
        {},
    ],
)
def test_anomaly_helpers_require_exactly_one_velocity_mode(kwargs: dict[str, float]) -> None:
    base = constant_velocity_model_2d(_grid(), 1800.0)

    with pytest.raises(GeometryError, match="exactly one"):
        add_rectangular_velocity_anomaly_2d(
            base,
            x_min=100.0,
            x_max=110.0,
            z_min=0.0,
            z_max=5.0,
            **kwargs,
        )
    with pytest.raises(GeometryError, match="exactly one"):
        add_circular_velocity_anomaly_2d(
            base,
            center_x=110.0,
            center_z=5.0,
            radius=10.0,
            **kwargs,
        )


def test_anomaly_rejects_non_positive_final_velocity() -> None:
    base = constant_velocity_model_2d(_grid(), 1800.0)

    with pytest.raises(GeometryError, match="non-positive"):
        add_rectangular_velocity_anomaly_2d(
            base,
            x_min=100.0,
            x_max=110.0,
            z_min=0.0,
            z_max=5.0,
            velocity_delta=-2000.0,
        )


def test_invalid_grid_velocity_layers_and_coordinates_raise_geometry_error() -> None:
    grid = _grid()

    with pytest.raises(GeometryError):
        constant_velocity_model_2d(object(), 1500.0)  # type: ignore[arg-type]
    with pytest.raises(GeometryError):
        constant_velocity_model_2d(grid, 0.0)
    with pytest.raises(GeometryError):
        AcousticVelocityModel2D(np.ones((grid.nx + 1, grid.nz)), grid, {})
    with pytest.raises(GeometryError):
        AcousticVelocityModel2D(np.full((grid.nx, grid.nz), np.nan), grid, {})
    with pytest.raises(GeometryError):
        layered_velocity_model_2d(grid, [])
    with pytest.raises(GeometryError):
        layered_velocity_model_2d(grid, [{"z_top": 100.0, "velocity": 1800.0}])
    with pytest.raises(GeometryError):
        layered_velocity_model_2d(grid, [{"z_top": 0.0, "velocity": 1500.0}, {"z_top": 0.0, "velocity": 1600.0}])
    base = constant_velocity_model_2d(grid, 1800.0)
    with pytest.raises(GeometryError):
        add_rectangular_velocity_anomaly_2d(
            base,
            x_min=130.0,
            x_max=120.0,
            z_min=0.0,
            z_max=5.0,
            velocity=1600.0,
        )
    with pytest.raises(GeometryError):
        add_circular_velocity_anomaly_2d(base, center_x=120.0, center_z=10.0, radius=0.0, velocity=1600.0)


def test_velocity_model_summary_is_json_safe_and_path_free() -> None:
    base = constant_velocity_model_2d(_grid(), 1800.0)
    model = add_circular_velocity_anomaly_2d(base, center_x=120.0, center_z=10.0, radius=10.0, velocity=1500.0)

    summary = velocity_model_summary(model)

    assert summary["model_kind"] == "velocity_model_with_anomalies"
    assert summary["velocity_shape"] == [6, 5]
    assert summary["velocity_min"] == pytest.approx(1500.0)
    assert summary["velocity_max"] == pytest.approx(1800.0)
    assert summary["anomaly_count"] == 1
    assert summary["prototype"] is True
    assert summary["field_ready"] is False
    json.dumps(summary, sort_keys=True)
    _assert_no_local_paths(summary)


def test_modeling_topic_export_available_without_root_stable_api_promotion() -> None:
    import pymadagascar
    import pymadagascar.api as api
    import pymadagascar.modeling as modeling

    assert modeling.AcousticVelocityModel2D is AcousticVelocityModel2D
    assert modeling.constant_velocity_model_2d is constant_velocity_model_2d
    assert modeling.layered_velocity_model_2d is layered_velocity_model_2d
    assert modeling.add_rectangular_velocity_anomaly_2d is add_rectangular_velocity_anomaly_2d
    assert modeling.add_circular_velocity_anomaly_2d is add_circular_velocity_anomaly_2d
    assert modeling.velocity_model_summary is velocity_model_summary
    assert not hasattr(api, "AcousticVelocityModel2D")
    assert not hasattr(api, "constant_velocity_model_2d")
    assert not hasattr(api, "layered_velocity_model_2d")
    assert not hasattr(pymadagascar, "AcousticVelocityModel2D")
    assert not hasattr(pymadagascar, "constant_velocity_model_2d")
