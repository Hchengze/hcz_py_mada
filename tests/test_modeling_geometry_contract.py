import json

import numpy as np
import pytest

from pymadagascar.modeling import (
    AcousticAcquisition2D,
    AcousticModelGrid2D,
    GeometryError,
    PointSource2D,
    ReceiverArray2D,
    acquisition_to_acoustic2d_indices,
    receiver_line_2d,
)


def _grid() -> AcousticModelGrid2D:
    return AcousticModelGrid2D(nx=6, nz=5, dx=10.0, dz=2.0, ox=100.0, oz=1.0)


def _assert_no_local_paths(payload: object) -> None:
    text = json.dumps(payload, sort_keys=True)
    for marker in ("E:\\", "D:\\", "/home/hcz", "/mnt/"):
        assert marker not in text


def test_acoustic_model_grid_validates_regular_local_x_z_contract() -> None:
    grid = _grid()

    assert grid.nx == 6
    assert grid.nz == 5
    assert grid.distance_unit == "m"
    assert grid.coordinate_frame == "local_2d_x_z"
    assert grid.depth_positive == "down"
    assert grid.to_metadata()["numpy_velocity_shape"] == [6, 5]
    assert grid.to_metadata()["rsf_axis_convention"] == "n1=z,n2=x"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"nx": 0, "nz": 5, "dx": 1.0, "dz": 1.0},
        {"nx": 5, "nz": -1, "dx": 1.0, "dz": 1.0},
        {"nx": 5, "nz": 5, "dx": 0.0, "dz": 1.0},
        {"nx": 5, "nz": 5, "dx": 1.0, "dz": float("nan")},
        {"nx": 5, "nz": 5, "dx": 1.0, "dz": 1.0, "ox": float("inf")},
        {"nx": 5, "nz": 5, "dx": 1.0, "dz": 1.0, "coordinate_frame": "utm"},
        {"nx": 5, "nz": 5, "dx": 1.0, "dz": 1.0, "depth_positive": "up"},
    ],
)
def test_acoustic_model_grid_rejects_invalid_values(kwargs: dict[str, object]) -> None:
    with pytest.raises(GeometryError):
        AcousticModelGrid2D(**kwargs)


def test_index_to_coordinate_and_nearest_index_are_hand_calculated() -> None:
    grid = _grid()

    assert grid.index_to_coordinate(2, 3) == pytest.approx((120.0, 7.0))
    assert grid.coordinate_to_nearest_index(121.0, 6.1) == (2, 3)
    assert grid.contains_index(5, 4)
    assert not grid.contains_index(6, 4)
    assert grid.contains_coordinate(150.0, 9.0)
    assert not grid.contains_coordinate(151.0, 9.0)


@pytest.mark.parametrize("ix, iz", [(-1, 0), (6, 0), (0, 5)])
def test_index_to_coordinate_rejects_out_of_bounds(ix: int, iz: int) -> None:
    with pytest.raises(GeometryError):
        _grid().index_to_coordinate(ix, iz)


@pytest.mark.parametrize("x, z", [(99.0, 1.0), (151.0, 1.0), (100.0, 10.0)])
def test_coordinate_to_nearest_index_rejects_out_of_bounds(x: float, z: float) -> None:
    with pytest.raises(GeometryError):
        _grid().coordinate_to_nearest_index(x, z)


def test_point_source_and_receiver_array_convert_to_acoustic2d_indices() -> None:
    grid = _grid()
    source = PointSource2D(120.0, 5.0)
    receivers = ReceiverArray2D(np.array([[100.0, 3.0], [130.0, 7.0]]))

    assert source.to_index(grid) == (2, 2)
    assert receivers.to_indices(grid) == [(0, 1), (3, 3)]


def test_receiver_array_validation() -> None:
    with pytest.raises(GeometryError):
        ReceiverArray2D(np.array([1.0, 2.0]))
    with pytest.raises(GeometryError):
        ReceiverArray2D(np.empty((0, 2)))
    with pytest.raises(GeometryError):
        ReceiverArray2D(np.array([[0.0, float("nan")]]))


def test_receiver_line_2d_generates_regular_line_with_documented_endpoint_policy() -> None:
    line = receiver_line_2d(x_start=100.0, x_stop=140.0, z=3.0, spacing=20.0)

    assert line.kind == "receiver_line"
    assert line.receiver_count == 3
    np.testing.assert_allclose(line.coordinates, np.array([[100.0, 3.0], [120.0, 3.0], [140.0, 3.0]]))
    metadata = line.to_metadata()
    assert metadata["line_geometry"] == "regular_x_line"
    assert metadata["endpoint_policy"] == "included_when_on_spacing_grid"
    assert metadata["endpoint_included"] is True


def test_receiver_line_2d_rejects_invalid_spacing_and_reversed_extent() -> None:
    with pytest.raises(GeometryError):
        receiver_line_2d(x_start=0.0, x_stop=10.0, z=0.0, spacing=0.0)
    with pytest.raises(GeometryError):
        receiver_line_2d(x_start=10.0, x_stop=0.0, z=0.0, spacing=1.0)


def test_acquisition_metadata_is_json_safe_and_path_free() -> None:
    grid = _grid()
    acquisition = AcousticAcquisition2D(
        source=PointSource2D(120.0, 5.0, kind="synthetic_point_source"),
        receivers=receiver_line_2d(x_start=100.0, x_stop=140.0, z=3.0, spacing=20.0),
    )

    metadata = acquisition.to_metadata(grid)
    json.dumps(metadata, sort_keys=True)

    assert metadata["geometry_kind"] == "acoustic_acquisition_2d"
    assert metadata["coordinate_frame"] == "local_2d_x_z"
    assert metadata["distance_unit"] == "m"
    assert metadata["depth_positive"] == "down"
    assert metadata["source_kind"] == "synthetic_point_source"
    assert metadata["receiver_count"] == 3
    assert metadata["source_index"] == [2, 2]
    assert metadata["receiver_indices"] == [[0, 1], [2, 1], [4, 1]]
    _assert_no_local_paths(metadata)


def test_acquisition_to_acoustic2d_indices_matches_current_forward_signature() -> None:
    grid = _grid()
    acquisition = AcousticAcquisition2D(
        source=PointSource2D(120.0, 5.0),
        receivers=receiver_line_2d(x_start=100.0, x_stop=140.0, z=3.0, spacing=20.0),
    )

    sx, sz, receiver_indices = acquisition_to_acoustic2d_indices(grid, acquisition)

    assert (sx, sz) == (2, 2)
    assert receiver_indices == [(0, 1), (2, 1), (4, 1)]
    assert all(isinstance(pair, tuple) and len(pair) == 2 for pair in receiver_indices)


def test_modeling_topic_exports_are_available_without_root_stable_api_promotion() -> None:
    import pymadagascar
    import pymadagascar.api as api
    import pymadagascar.modeling as modeling

    assert modeling.AcousticModelGrid2D is AcousticModelGrid2D
    assert modeling.receiver_line_2d is receiver_line_2d
    assert not hasattr(api, "AcousticModelGrid2D")
    assert not hasattr(api, "receiver_line_2d")
    assert not hasattr(pymadagascar, "AcousticModelGrid2D")
