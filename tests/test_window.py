from pathlib import Path

import numpy as np
import pytest

from pymadagascar.cli.window import main as window_main
from pymadagascar.generic.window import WindowError, window, window_rsf
from pymadagascar.io.rsf import RSFArray, RSFHeader, read_rsf, write_rsf
from pymadagascar.testing.compare import assert_rsf_allclose
from pymadagascar.testing.runner import original_madagascar_available, run_original_madagascar


def _header(shape: tuple[int, ...]) -> RSFHeader:
    header = RSFHeader({"data_format": "native_float", "esize": 4})
    for axis, size in enumerate(shape, start=1):
        header[f"n{axis}"] = size
        header[f"o{axis}"] = float(axis)
        header[f"d{axis}"] = float(axis) * 0.5
        header[f"label{axis}"] = f"Axis {axis}"
        header[f"unit{axis}"] = f"u{axis}"
    return header


def test_api_1d_window_updates_header() -> None:
    data = np.arange(6, dtype=np.float32)
    header = _header((6,))

    result = window(data, header, axis=1, f=2, n=3, j=1)

    np.testing.assert_array_equal(result.data, np.array([2, 3, 4], dtype=np.float32))
    assert result.header["n1"] == "3"
    assert result.header["o1"] == "2"
    assert result.header["d1"] == "0.5"
    assert result.header["label1"] == "Axis 1"
    assert result.header["unit1"] == "u1"


def test_api_2d_window_uses_rsf_axis_order() -> None:
    data = np.arange(12, dtype=np.float32).reshape(3, 4)
    header = _header((4, 3))

    result = window(data, header, axis=(1, 2), f=(1, 1), n=(2, 2), j=(1, 1))

    np.testing.assert_array_equal(result.data, data[1:3, 1:3])
    assert result.header.dimensions == (2, 2)
    assert result.header["o1"] == "1.5"
    assert result.header["o2"] == "3"


def test_api_3d_window_multiple_axes() -> None:
    data = np.arange(24, dtype=np.float32).reshape(2, 3, 4)
    header = _header((4, 3, 2))

    result = window(data, header, n={1: 2, 2: 2, 3: 1}, f={1: 1, 2: 0, 3: 1})

    np.testing.assert_array_equal(result.data, data[1:2, 0:2, 1:3])
    assert result.header.dimensions == (2, 2, 1)
    assert result.header["o1"] == "1.5"
    assert result.header["o3"] == "4.5"


def test_api_stride_decimation_updates_d() -> None:
    data = np.arange(8, dtype=np.float32)
    header = _header((8,))

    result = window(data, header, axis=1, f=1, n=3, j=2)

    np.testing.assert_array_equal(result.data, np.array([1, 3, 5], dtype=np.float32))
    assert result.header["n1"] == "3"
    assert result.header["o1"] == "1.5"
    assert result.header["d1"] == "1"


def test_window_rsf_default_count_with_stride() -> None:
    data = np.arange(8, dtype=np.float32)
    result = window_rsf(RSFArray(data, _header((8,))), {"f1": 1, "j1": 2})

    np.testing.assert_array_equal(result.data, np.array([1, 3, 5, 7], dtype=np.float32))
    assert result.header["n1"] == "4"
    assert result.header["d1"] == "1"


def test_window_rsf_min_max_parameters() -> None:
    data = np.arange(6, dtype=np.float32)
    header = RSFHeader(
        {
            "n1": 6,
            "o1": 10.0,
            "d1": 2.0,
            "label1": "Depth",
            "unit1": "m",
            "data_format": "native_float",
            "esize": 4,
        }
    )

    result = window_rsf(RSFArray(data, header), {"min1": 14.0, "max1": 18.0})

    np.testing.assert_array_equal(result.data, np.array([2, 3, 4], dtype=np.float32))
    assert result.header["n1"] == "3"
    assert result.header["o1"] == "14"
    assert result.header["d1"] == "2"
    assert result.header["label1"] == "Depth"
    assert result.header["unit1"] == "m"


def test_window_rsf_negative_f_counts_from_end() -> None:
    data = np.arange(6, dtype=np.float32)

    result = window_rsf(RSFArray(data, _header((6,))), {"f1": -2, "n1": 2})

    np.testing.assert_array_equal(result.data, np.array([4, 5], dtype=np.float32))
    assert result.header["o1"] == "3"


def test_window_rsf_squeeze_moves_singleton_axes_to_end() -> None:
    data = np.arange(24, dtype=np.float32).reshape(2, 3, 4)
    header = _header((4, 3, 2))

    result = window_rsf(RSFArray(data, header), {"f2": 1, "n2": 1})

    assert result.header.dimensions == (4, 2, 1)
    assert result.header["label1"] == "Axis 1"
    assert result.header["label2"] == "Axis 3"
    assert result.header["label3"] == "Axis 2"
    assert result.data.shape == (1, 2, 4)


def test_window_rsf_squeeze_can_be_disabled() -> None:
    data = np.arange(24, dtype=np.float32).reshape(2, 3, 4)
    header = _header((4, 3, 2))

    result = window_rsf(RSFArray(data, header), {"f2": 1, "n2": 1, "squeeze": "n"})

    assert result.header.dimensions == (4, 1, 2)
    assert result.data.shape == (2, 1, 4)


def test_window_out_of_bounds_error_is_clear() -> None:
    data = np.arange(5, dtype=np.float32)

    with pytest.raises(WindowError, match="window exceeds axis 1"):
        window(data, _header((5,)), axis=1, f=3, n=3)


def test_cli_window_writes_output(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "output.rsf"
    data = np.arange(12, dtype=np.float32).reshape(3, 4)
    write_rsf(input_path, data, _header((4, 3)))

    code = window_main(
        [
            str(input_path),
            "out=" + str(output_path),
            "f1=1",
            "n1=2",
            "f2=1",
            "n2=2",
            "squeeze=n",
        ]
    )
    result = read_rsf(output_path)

    assert code == 0
    np.testing.assert_array_equal(result.data, data[1:3, 1:3])
    assert result.header.dimensions == (2, 2)
    assert result.header["o1"] == "1.5"
    assert result.header["o2"] == "3"


def test_cli_reports_out_of_bounds(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "output.rsf"
    write_rsf(input_path, np.arange(5, dtype=np.float32), _header((5,)))

    code = window_main([str(input_path), "out=" + str(output_path), "f1=4", "n1=2"])

    assert code == 2
    assert "window exceeds axis 1" in capsys.readouterr().err
    assert not output_path.exists()


def test_cli_original_sfwindow_comparison_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfwindow"):
        pytest.skip("Original Madagascar sfwindow is not installed")

    input_path = tmp_path / "input.rsf"
    original = tmp_path / "original.rsf"
    python = tmp_path / "python.rsf"
    data = np.arange(12, dtype=np.float32).reshape(3, 4)
    write_rsf(input_path, data, _header((4, 3)))

    run_original_madagascar(
        [
            "sfwindow",
            "in=input.rsf",
            "out=original.rsf",
            "f1=1",
            "n1=2",
            "f2=1",
            "n2=2",
            "squeeze=n",
        ],
        cwd=tmp_path,
        require_program="sfwindow",
    )
    assert window_main(
        [
            str(input_path),
            "out=" + str(python),
            "f1=1",
            "n1=2",
            "f2=1",
            "n2=2",
            "squeeze=n",
        ]
    ) == 0

    assert_rsf_allclose(
        original,
        python,
        ignore_keys={"in", "f1", "f2", "squeeze"},
    )
