from pathlib import Path

import numpy as np
import pytest

from pymadagascar.cli.cat import main as cat_main
from pymadagascar.generic.cat import CatError, cat_arrays, cat_rsf
from pymadagascar.io.rsf import RSFArray, RSFHeader, read_rsf, write_rsf
from pymadagascar.testing.compare import assert_rsf_allclose
from pymadagascar.testing.runner import original_madagascar_available, run_original_madagascar


def _header(**updates: object) -> RSFHeader:
    values = {
        "o1": 1.0,
        "d1": 0.5,
        "label1": "Fast",
        "unit1": "s",
        "o2": 10.0,
        "d2": 2.0,
        "label2": "Slow",
        "unit2": "km",
        "o3": 100.0,
        "d3": 25.0,
        "label3": "Slice",
        "unit3": "m",
    }
    values.update(updates)
    return RSFHeader(values)


def _write(path: Path, data: np.ndarray, header: RSFHeader | None = None) -> RSFArray:
    return write_rsf(path, data, header or _header())


def test_1d_cat_arrays() -> None:
    first = RSFArray(np.array([1, 2], dtype=np.float32), _header(n1=2, data_format="native_float", esize=4))
    second = RSFArray(np.array([3, 4, 5], dtype=np.float32), _header(n1=3, data_format="native_float", esize=4))

    result = cat_arrays([first.data, second.data], [first.header, second.header], axis=1)

    np.testing.assert_array_equal(result.data, np.array([1, 2, 3, 4, 5], dtype=np.float32))
    assert result.header.dimensions == (5,)
    assert result.header["label1"] == "Fast"
    assert result.header["unit1"] == "s"


def test_2d_cat_along_axis1() -> None:
    first_data = np.arange(6, dtype=np.float32).reshape(2, 3)
    second_data = 10 + np.arange(4, dtype=np.float32).reshape(2, 2)
    first = RSFArray(first_data, _header(n1=3, n2=2, data_format="native_float", esize=4))
    second = RSFArray(second_data, _header(n1=2, n2=2, data_format="native_float", esize=4))

    result = cat_arrays([first.data, second.data], [first.header, second.header], axis=1)

    np.testing.assert_array_equal(result.data, np.concatenate([first_data, second_data], axis=1))
    assert result.header.dimensions == (5, 2)
    assert result.header["o1"] == "1"
    assert result.header["d1"] == "0.5"


def test_2d_cat_along_axis2() -> None:
    first_data = np.arange(6, dtype=np.float32).reshape(2, 3)
    second_data = 10 + np.arange(3, dtype=np.float32).reshape(1, 3)
    first = RSFArray(first_data, _header(n1=3, n2=2, data_format="native_float", esize=4))
    second = RSFArray(second_data, _header(n1=3, n2=1, data_format="native_float", esize=4))

    result = cat_arrays([first.data, second.data], [first.header, second.header], axis=2)

    np.testing.assert_array_equal(result.data, np.concatenate([first_data, second_data], axis=0))
    assert result.header.dimensions == (3, 3)
    assert result.header["label2"] == "Slow"
    assert result.header["unit2"] == "km"


def test_2d_cat_along_new_axis3() -> None:
    first_data = np.arange(6, dtype=np.float32).reshape(2, 3)
    second_data = 10 + np.arange(6, dtype=np.float32).reshape(2, 3)
    first = RSFArray(first_data, _header(n1=3, n2=2, data_format="native_float", esize=4))
    second = RSFArray(second_data, _header(n1=3, n2=2, data_format="native_float", esize=4))

    result = cat_arrays([first.data, second.data], [first.header, second.header], axis=3)

    expected = np.stack([first_data, second_data], axis=0)
    np.testing.assert_array_equal(result.data, expected)
    assert result.header.dimensions == (3, 2, 2)
    assert result.header["n3"] == "2"


def test_3d_cat_along_axis3() -> None:
    first_data = np.arange(24, dtype=np.float32).reshape(2, 3, 4)
    second_data = 100 + np.arange(12, dtype=np.float32).reshape(1, 3, 4)
    first = RSFArray(first_data, _header(n1=4, n2=3, n3=2, data_format="native_float", esize=4))
    second = RSFArray(second_data, _header(n1=4, n2=3, n3=1, data_format="native_float", esize=4))

    result = cat_arrays([first.data, second.data], [first.header, second.header], axis=3)

    np.testing.assert_array_equal(result.data, np.concatenate([first_data, second_data], axis=0))
    assert result.header.dimensions == (4, 3, 3)
    assert result.header["label1"] == "Fast"
    assert result.header["label2"] == "Slow"
    assert result.header["label3"] == "Slice"


def test_cat_rsf_writes_output_and_updates_header(tmp_path: Path) -> None:
    first = tmp_path / "first.rsf"
    second = tmp_path / "second.rsf"
    output = tmp_path / "out.rsf"
    first_data = np.ones((2, 3), dtype=np.float32)
    second_data = 2 * np.ones((1, 3), dtype=np.float32)
    _write(first, first_data)
    _write(second, second_data)

    result = cat_rsf([first, second], output, axis=2)
    loaded = read_rsf(output)

    np.testing.assert_array_equal(loaded.data, np.concatenate([first_data, second_data], axis=0))
    assert result.header_path == output.resolve()
    assert loaded.header.dimensions == (3, 3)
    assert loaded.header["label1"] == "Fast"
    assert loaded.header["unit2"] == "km"


def test_shape_incompatibility_raises_clear_error() -> None:
    first = RSFArray(
        np.ones((2, 3), dtype=np.float32),
        _header(n1=3, n2=2, data_format="native_float", esize=4),
    )
    second = RSFArray(
        np.ones((2, 4), dtype=np.float32),
        _header(n1=4, n2=2, data_format="native_float", esize=4),
    )

    with pytest.raises(CatError, match="n1 mismatch"):
        cat_arrays([first.data, second.data], [first.header, second.header], axis=2)


def test_non_cat_axis_coordinate_mismatch_raises() -> None:
    first = RSFArray(
        np.ones((2, 3), dtype=np.float32),
        _header(n1=3, n2=2, data_format="native_float", esize=4),
    )
    second = RSFArray(
        np.ones((1, 3), dtype=np.float32),
        _header(n1=3, n2=1, o1=2.0, data_format="native_float", esize=4),
    )

    with pytest.raises(CatError, match="o1 mismatch"):
        cat_arrays([first.data, second.data], [first.header, second.header], axis=2)


def test_dtype_mismatch_raises() -> None:
    first = RSFArray(
        np.ones((2, 3), dtype=np.float32),
        _header(n1=3, n2=2, data_format="native_float", esize=4),
    )
    second = RSFArray(
        np.ones((1, 3), dtype=np.float64),
        _header(n1=3, n2=1, data_format="native_double", esize=8),
    )

    with pytest.raises(CatError, match="dtype mismatch"):
        cat_arrays([first.data, second.data], [first.header, second.header], axis=2)


def test_cli_cat_outputs_rsf(tmp_path: Path) -> None:
    first = tmp_path / "first.rsf"
    second = tmp_path / "second.rsf"
    output = tmp_path / "out.rsf"
    first_data = np.arange(6, dtype=np.float32).reshape(2, 3)
    second_data = 10 + np.arange(3, dtype=np.float32).reshape(1, 3)
    _write(first, first_data)
    _write(second, second_data)

    code = cat_main([str(first), str(second), "axis=2", "out=" + str(output)])
    result = read_rsf(output)

    assert code == 0
    np.testing.assert_array_equal(result.data, np.concatenate([first_data, second_data], axis=0))
    assert result.header.dimensions == (3, 3)


def test_cli_requires_out(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    first = tmp_path / "first.rsf"
    second = tmp_path / "second.rsf"
    _write(first, np.ones((1, 3), dtype=np.float32))
    _write(second, np.ones((1, 3), dtype=np.float32))

    code = cat_main([str(first), str(second), "axis=2"])

    assert code == 2
    assert "Missing required parameter: out=" in capsys.readouterr().err


def test_cli_original_sfcat_comparison_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfcat"):
        pytest.skip("Original Madagascar sfcat is not installed")

    first = tmp_path / "first.rsf"
    second = tmp_path / "second.rsf"
    original = tmp_path / "original.rsf"
    python = tmp_path / "python.rsf"
    first_data = np.arange(6, dtype=np.float32).reshape(2, 3)
    second_data = 10 + np.arange(3, dtype=np.float32).reshape(1, 3)
    _write(first, first_data)
    _write(second, second_data)

    run_original_madagascar(
        ["sfcat", "first.rsf", "second.rsf", "axis=2", "out=original.rsf"],
        cwd=tmp_path,
        require_program="sfcat",
    )
    assert cat_main([str(first), str(second), "axis=2", "out=" + str(python)]) == 0

    assert_rsf_allclose(
        original,
        python,
        ignore_keys={"in", "o3", "d3", "label3", "unit3"},
    )
