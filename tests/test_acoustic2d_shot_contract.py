import json

import numpy as np
import pytest

from pymadagascar.modeling import (
    Acoustic2DError,
    AcousticAcquisition2D,
    AcousticModelGrid2D,
    AcousticShotRecord2D,
    GeometryError,
    PointSource2D,
    receiver_line_2d,
    run_acoustic2d_shot,
)


def _assert_no_local_paths(payload: object) -> None:
    text = json.dumps(payload, sort_keys=True)
    for marker in ("E:\\", "D:\\", "/home/hcz", "/mnt/"):
        assert marker not in text


def _grid() -> AcousticModelGrid2D:
    return AcousticModelGrid2D(nx=21, nz=19, dx=10.0, dz=10.0)


def _velocity(grid: AcousticModelGrid2D) -> np.ndarray:
    return np.full((grid.nx, grid.nz), 1000.0, dtype=np.float32)


def _acquisition() -> AcousticAcquisition2D:
    return AcousticAcquisition2D(
        source=PointSource2D(100.0, 90.0),
        receivers=receiver_line_2d(x_start=80.0, x_stop=120.0, z=50.0, spacing=20.0),
    )


def test_run_acoustic2d_shot_accepts_geometry_and_returns_record() -> None:
    grid = _grid()
    acquisition = _acquisition()

    record = run_acoustic2d_shot(
        _velocity(grid),
        grid,
        acquisition,
        nt=60,
        dt=0.001,
        fpeak=20.0,
        t0=0.04,
        nb=5,
    )

    assert isinstance(record, AcousticShotRecord2D)
    assert record.data.shape == (acquisition.receivers.receiver_count, 60)
    assert record.metadata["data_layout"] == "receiver_time"
    assert record.metadata["numerical_core"] == "acoustic2d_forward"
    assert np.max(np.abs(record.data)) > 0.0


def test_shot_record_time_axis_and_coordinates_match_input_acquisition() -> None:
    grid = _grid()
    acquisition = _acquisition()

    record = run_acoustic2d_shot(
        _velocity(grid),
        grid,
        acquisition,
        nt=40,
        dt=0.002,
        fpeak=15.0,
        t0=0.03,
        nb=5,
    )

    assert record.time.shape == (40,)
    assert record.time[0] == pytest.approx(0.0)
    assert record.time[1] - record.time[0] == pytest.approx(0.002)
    np.testing.assert_allclose(record.source_coordinate, np.array([100.0, 90.0]))
    np.testing.assert_allclose(record.receiver_coordinates, acquisition.receivers.coordinates)


def test_shot_metadata_is_json_safe_path_free_and_documents_boundaries() -> None:
    grid = _grid()
    acquisition = _acquisition()

    record = run_acoustic2d_shot(
        _velocity(grid),
        grid,
        acquisition,
        nt=20,
        dt=0.001,
        fpeak=20.0,
        t0=0.02,
        nb=5,
    )
    metadata = record.metadata
    json.dumps(metadata, sort_keys=True)

    assert metadata["method"] == "acoustic2d_shot"
    assert metadata["coordinate_frame"] == "local_2d_x_z"
    assert metadata["distance_unit"] == "m"
    assert metadata["time_unit"] == "s"
    assert metadata["velocity_unit"] == "m/s"
    assert metadata["velocity_shape"] == [21, 19]
    assert metadata["source_index"] == [10, 9]
    assert metadata["receiver_indices"] == [[8, 5], [10, 5], [12, 5]]
    assert metadata["receiver_index_order"] == "x_index_z_index"
    assert metadata["data_shape"] == [3, 20]
    assert metadata["prototype"] is True
    assert metadata["field_ready"] is False
    assert metadata["multi_shot"] is False
    assert metadata["source_interpolation"] is False
    assert metadata["receiver_interpolation"] is False
    assert metadata["acquisition"]["geometry_kind"] == "acoustic_acquisition_2d"
    _assert_no_local_paths(metadata)


def test_velocity_shape_mismatch_is_rejected() -> None:
    grid = _grid()

    with pytest.raises(Acoustic2DError, match="velocity shape"):
        run_acoustic2d_shot(
            np.ones((grid.nx, grid.nz + 1), dtype=np.float32),
            grid,
            _acquisition(),
            nt=10,
            dt=0.001,
        )


def test_out_of_bounds_source_or_receiver_is_rejected() -> None:
    grid = _grid()
    bad_source = AcousticAcquisition2D(
        source=PointSource2D(1000.0, 90.0),
        receivers=receiver_line_2d(x_start=80.0, x_stop=120.0, z=50.0, spacing=20.0),
    )
    bad_receiver = AcousticAcquisition2D(
        source=PointSource2D(100.0, 90.0),
        receivers=receiver_line_2d(x_start=80.0, x_stop=1000.0, z=50.0, spacing=920.0),
    )

    with pytest.raises(GeometryError):
        run_acoustic2d_shot(_velocity(grid), grid, bad_source, nt=10, dt=0.001)
    with pytest.raises(GeometryError):
        run_acoustic2d_shot(_velocity(grid), grid, bad_receiver, nt=10, dt=0.001)


def test_modeling_topic_export_available_without_root_stable_api_promotion() -> None:
    import pymadagascar
    import pymadagascar.api as api
    import pymadagascar.modeling as modeling

    assert modeling.AcousticShotRecord2D is AcousticShotRecord2D
    assert modeling.run_acoustic2d_shot is run_acoustic2d_shot
    assert not hasattr(api, "AcousticShotRecord2D")
    assert not hasattr(api, "run_acoustic2d_shot")
    assert not hasattr(pymadagascar, "AcousticShotRecord2D")
    assert not hasattr(pymadagascar, "run_acoustic2d_shot")
