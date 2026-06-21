import json

import numpy as np
import pytest

from pymadagascar.modeling import (
    Acoustic2DError,
    AcousticAcquisition2D,
    AcousticModelGrid2D,
    AcousticShotRecord2D,
    AcousticSurveyRecord2D,
    PointSource2D,
    receiver_line_2d,
    run_acoustic2d_survey,
)


def _assert_no_local_paths(payload: object) -> None:
    text = json.dumps(payload, sort_keys=True)
    for marker in ("E:\\", "D:\\", "/home/hcz", "/mnt/"):
        assert marker not in text


def _grid() -> AcousticModelGrid2D:
    return AcousticModelGrid2D(nx=21, nz=19, dx=10.0, dz=10.0)


def _velocity(grid: AcousticModelGrid2D) -> np.ndarray:
    return np.full((grid.nx, grid.nz), 1000.0, dtype=np.float32)


def _acquisitions() -> list[AcousticAcquisition2D]:
    return [
        AcousticAcquisition2D(
            source=PointSource2D(80.0, 90.0),
            receivers=receiver_line_2d(x_start=70.0, x_stop=110.0, z=50.0, spacing=20.0),
        ),
        AcousticAcquisition2D(
            source=PointSource2D(120.0, 90.0),
            receivers=receiver_line_2d(x_start=90.0, x_stop=150.0, z=50.0, spacing=20.0),
        ),
    ]


def test_run_acoustic2d_survey_returns_ordered_shot_records() -> None:
    grid = _grid()
    acquisitions = _acquisitions()

    survey = run_acoustic2d_survey(
        _velocity(grid),
        grid,
        acquisitions,
        nt=40,
        dt=0.001,
        fpeak=20.0,
        t0=0.03,
        nb=5,
    )

    assert isinstance(survey, AcousticSurveyRecord2D)
    assert len(survey.shots) == 2
    assert all(isinstance(shot, AcousticShotRecord2D) for shot in survey.shots)
    for index, shot in enumerate(survey.shots):
        assert shot.data.shape == (acquisitions[index].receivers.receiver_count, 40)
        assert shot.time.shape == (40,)
        assert shot.metadata["shot_index"] == index
        assert shot.metadata["shot_count"] == 2
        assert shot.metadata["shot_order"] == "input_order"
        np.testing.assert_allclose(
            shot.source_coordinate,
            np.array([acquisitions[index].source.x, acquisitions[index].source.z]),
        )
        np.testing.assert_allclose(
            shot.receiver_coordinates,
            acquisitions[index].receivers.coordinates,
        )
    np.testing.assert_allclose(survey.shots[0].source_coordinate, np.array([80.0, 90.0]))
    np.testing.assert_allclose(survey.shots[1].source_coordinate, np.array([120.0, 90.0]))


def test_survey_metadata_is_json_safe_path_free_and_documents_boundaries() -> None:
    grid = _grid()
    survey = run_acoustic2d_survey(
        _velocity(grid),
        grid,
        _acquisitions(),
        nt=30,
        dt=0.002,
        fpeak=15.0,
        t0=0.03,
        nb=5,
    )
    metadata = survey.metadata
    json.dumps(metadata, sort_keys=True)

    assert metadata["method"] == "acoustic2d_survey"
    assert metadata["numerical_core"] == "acoustic2d_forward"
    assert metadata["shot_wrapper"] == "run_acoustic2d_shot"
    assert metadata["coordinate_frame"] == "local_2d_x_z"
    assert metadata["distance_unit"] == "m"
    assert metadata["time_unit"] == "s"
    assert metadata["velocity_unit"] == "m/s"
    assert metadata["velocity_shape"] == [21, 19]
    assert metadata["shot_count"] == 2
    assert metadata["shot_indices"] == [0, 1]
    assert metadata["shot_order"] == "input_order"
    assert metadata["receiver_count_per_shot"] == [3, 4]
    assert metadata["receiver_count_consistency"] == "variable"
    assert metadata["data_layout_per_shot"] == "receiver_time"
    assert metadata["survey_tensor_layout"] is None
    assert metadata["survey_tensor_layout_status"] == "not_committed"
    assert metadata["multi_shot"] is True
    assert metadata["parallel"] is False
    assert metadata["cache"] is False
    assert metadata["prototype"] is True
    assert metadata["field_ready"] is False
    assert metadata["source_interpolation"] is False
    assert metadata["receiver_interpolation"] is False
    _assert_no_local_paths(metadata)


def test_survey_rejects_empty_or_invalid_acquisitions() -> None:
    grid = _grid()

    with pytest.raises(Acoustic2DError, match="at least one"):
        run_acoustic2d_survey(_velocity(grid), grid, [], nt=10, dt=0.001)

    with pytest.raises(Acoustic2DError, match=r"acquisitions\[1\]"):
        run_acoustic2d_survey(
            _velocity(grid),
            grid,
            [_acquisitions()[0], object()],
            nt=10,
            dt=0.001,
        )


def test_survey_rejects_velocity_shape_mismatch() -> None:
    grid = _grid()

    with pytest.raises(Acoustic2DError, match="velocity shape"):
        run_acoustic2d_survey(
            np.ones((grid.nx + 1, grid.nz), dtype=np.float32),
            grid,
            _acquisitions(),
            nt=10,
            dt=0.001,
        )


def test_survey_rejects_single_shot_file_output_kwargs(tmp_path) -> None:
    grid = _grid()

    with pytest.raises(Acoustic2DError, match="single-shot file output"):
        run_acoustic2d_survey(
            _velocity(grid),
            grid,
            _acquisitions(),
            nt=10,
            dt=0.001,
            output_path=tmp_path / "shot.rsf",
        )


def test_modeling_topic_export_available_without_root_stable_api_promotion() -> None:
    import pymadagascar
    import pymadagascar.api as api
    import pymadagascar.modeling as modeling

    assert modeling.AcousticSurveyRecord2D is AcousticSurveyRecord2D
    assert modeling.run_acoustic2d_survey is run_acoustic2d_survey
    assert not hasattr(api, "AcousticSurveyRecord2D")
    assert not hasattr(api, "run_acoustic2d_survey")
    assert not hasattr(pymadagascar, "AcousticSurveyRecord2D")
    assert not hasattr(pymadagascar, "run_acoustic2d_survey")
