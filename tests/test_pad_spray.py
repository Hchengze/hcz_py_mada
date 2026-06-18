from pathlib import Path

import numpy as np
import pytest

from pymadagascar.cli.pad import main as pad_main
from pymadagascar.cli.spray import main as spray_main
from pymadagascar.cli.tile import main as tile_main
from pymadagascar.generic.pad import PadError, pad_rsf
from pymadagascar.generic.spray import SprayError, spray_rsf, tile_rsf
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf
from pymadagascar.testing.compare import assert_rsf_allclose
from pymadagascar.testing.runner import original_madagascar_available, run_original_madagascar


def _header(**updates: object) -> RSFHeader:
    values = {
        "o1": 10.0,
        "d1": 2.0,
        "label1": "Time",
        "unit1": "s",
        "o2": 100.0,
        "d2": 25.0,
        "label2": "Trace",
        "unit2": "m",
    }
    values.update(updates)
    return RSFHeader({key: value for key, value in values.items() if value is not None})


def _write(path: Path, data: np.ndarray, header: RSFHeader | None = None) -> None:
    write_rsf(path, data, header or _header())


def test_1d_padding_updates_origin_and_length(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "padded.rsf"
    data = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    _write(input_path, data, _header(o2=None, d2=None, label2=None, unit2=None))

    pad_rsf(input_path, output_path, beg={1: 2}, end={1: 1})
    loaded = read_rsf(output_path)

    np.testing.assert_array_equal(
        loaded.data,
        np.array([0.0, 0.0, 1.0, 2.0, 3.0, 0.0], dtype=np.float32),
    )
    assert loaded.header.dimensions == (6,)
    assert loaded.header["o1"] == "6"
    assert loaded.header["d1"] == "2"
    assert loaded.header["label1"] == "Time"


def test_2d_padding_with_requested_n_and_fill_value(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "padded.rsf"
    data = np.arange(6, dtype=np.float32).reshape(2, 3)
    _write(input_path, data)

    pad_rsf(input_path, output_path, n={1: 5}, beg={1: 1}, value=-1.0)
    loaded = read_rsf(output_path)

    expected = np.array(
        [
            [-1.0, 0.0, 1.0, 2.0, -1.0],
            [-1.0, 3.0, 4.0, 5.0, -1.0],
        ],
        dtype=np.float32,
    )
    np.testing.assert_array_equal(loaded.data, expected)
    assert loaded.header.dimensions == (5, 2)
    assert loaded.header["o1"] == "8"
    assert loaded.header["d1"] == "2"
    assert loaded.header["o2"] == "100"


def test_padding_can_extend_new_axis(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "padded.rsf"
    data = np.array([1.0, 2.0], dtype=np.float32)
    _write(input_path, data, _header(o2=None, d2=None, label2=None, unit2=None))

    pad_rsf(input_path, output_path, n={2: 3}, beg={2: 1})
    loaded = read_rsf(output_path)

    assert loaded.header.dimensions == (2, 3)
    assert loaded.data.shape == (3, 2)
    np.testing.assert_array_equal(
        loaded.data,
        np.array([[0.0, 0.0], [1.0, 2.0], [0.0, 0.0]], dtype=np.float32),
    )


def test_padding_rejects_too_small_requested_n(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "bad.rsf"
    _write(input_path, np.ones(3, dtype=np.float32))

    with pytest.raises(PadError, match="too small"):
        pad_rsf(input_path, output_path, n={1: 3}, beg={1: 1})

    assert not output_path.exists()


def test_spray_generates_new_axis_and_copies_data(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "sprayed.rsf"
    data = np.array([1.0, 2.0], dtype=np.float32)
    _write(input_path, data, _header(o2=None, d2=None, label2=None, unit2=None))

    spray_rsf(input_path, output_path, axis=2, n=3, o=5.0, d=0.5, label="Offset", unit="km")
    loaded = read_rsf(output_path)

    assert loaded.header.dimensions == (2, 3)
    assert loaded.header["o2"] == "5"
    assert loaded.header["d2"] == "0.5"
    assert loaded.header["label2"] == "Offset"
    assert loaded.header["unit2"] == "km"
    np.testing.assert_array_equal(
        loaded.data,
        np.array([[1.0, 2.0], [1.0, 2.0], [1.0, 2.0]], dtype=np.float32),
    )


def test_spray_can_insert_axis_before_existing_axes(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "sprayed.rsf"
    data = np.arange(6, dtype=np.float32).reshape(2, 3)
    _write(input_path, data)

    spray_rsf(input_path, output_path, axis=1, n=2)
    loaded = read_rsf(output_path)

    assert loaded.header.dimensions == (2, 3, 2)
    assert loaded.data.shape == (2, 3, 2)
    np.testing.assert_array_equal(loaded.data[..., 0], data)
    np.testing.assert_array_equal(loaded.data[..., 1], data)


def test_tile_repeats_complete_axis_blocks(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "tiled.rsf"
    data = np.arange(6, dtype=np.float32).reshape(2, 3)
    _write(input_path, data)

    tile_rsf(input_path, output_path, axis=2, repeat=2)
    loaded = read_rsf(output_path)

    assert loaded.header.dimensions == (3, 4)
    assert loaded.header["o2"] == "100"
    assert loaded.header["d2"] == "25"
    np.testing.assert_array_equal(loaded.data, np.concatenate([data, data], axis=0))


def test_tile_rejects_invalid_axis(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "bad.rsf"
    _write(input_path, np.ones((2, 3), dtype=np.float32))

    with pytest.raises(SprayError, match="axis must be between"):
        tile_rsf(input_path, output_path, axis=3, repeat=2)

    assert not output_path.exists()


def test_pad_cli(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "padded.rsf"
    data = np.array([1.0, 2.0], dtype=np.float32)
    _write(input_path, data, _header(o2=None, d2=None, label2=None, unit2=None))

    code = pad_main([str(input_path), "out=" + str(output_path), "beg1=1", "n1=4"])
    loaded = read_rsf(output_path)

    assert code == 0
    np.testing.assert_array_equal(loaded.data, np.array([0.0, 1.0, 2.0, 0.0], dtype=np.float32))
    assert loaded.header["o1"] == "8"


def test_spray_cli(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "sprayed.rsf"
    data = np.array([1.0, 2.0], dtype=np.float32)
    _write(input_path, data, _header(o2=None, d2=None, label2=None, unit2=None))

    code = spray_main(
        [
            str(input_path),
            "out=" + str(output_path),
            "axis=2",
            "n=2",
            "o=3",
            "d=4",
            "label=Copy",
            "unit=count",
        ]
    )
    loaded = read_rsf(output_path)

    assert code == 0
    assert loaded.header.dimensions == (2, 2)
    assert loaded.header["label2"] == "Copy"
    assert loaded.header["unit2"] == "count"
    np.testing.assert_array_equal(loaded.data, np.stack([data, data], axis=0))


def test_tile_cli(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "tiled.rsf"
    data = np.arange(6, dtype=np.float32).reshape(2, 3)
    _write(input_path, data)

    code = tile_main([str(input_path), "out=" + str(output_path), "axis=1", "repeat=2"])
    loaded = read_rsf(output_path)

    assert code == 0
    assert loaded.header.dimensions == (6, 2)
    np.testing.assert_array_equal(loaded.data, np.concatenate([data, data], axis=1))


def test_original_sfpad_comparison_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfpad"):
        pytest.skip("Original Madagascar sfpad is not installed")

    input_path = tmp_path / "input.rsf"
    original = tmp_path / "original.rsf"
    python = tmp_path / "python.rsf"
    _write(input_path, np.array([1.0, 2.0, 3.0], dtype=np.float32), _header())

    run_original_madagascar(
        ["sfpad", "in=input.rsf", "out=original.rsf", "beg1=1", "end1=2"],
        cwd=tmp_path,
        require_program="sfpad",
    )
    pad_rsf(input_path, python, beg={1: 1}, end={1: 2})

    assert_rsf_allclose(
        original,
        python,
        ignore_keys={
            "in",
            "beg1",
            "end1",
            "o2",
            "d2",
            "label2",
            "unit2",
        },
    )


def test_original_sfspray_values_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfspray"):
        pytest.skip("Original Madagascar sfspray is not installed")

    input_path = tmp_path / "input.rsf"
    original = tmp_path / "original.rsf"
    python = tmp_path / "python.rsf"
    data = np.array([1.0, 2.0], dtype=np.float32)
    _write(input_path, data, _header(o2=None, d2=None, label2=None, unit2=None))

    run_original_madagascar(
        [
            "sfspray",
            "in=input.rsf",
            "out=original.rsf",
            "axis=2",
            "n=3",
            "o=5",
            "d=0.5",
            "label=Offset",
            "unit=km",
        ],
        cwd=tmp_path,
        require_program="sfspray",
    )
    spray_rsf(input_path, python, axis=2, n=3, o=5.0, d=0.5, label="Offset", unit="km")

    original_rsf = read_rsf(original)
    python_rsf = read_rsf(python)
    np.testing.assert_array_equal(np.squeeze(original_rsf.data), python_rsf.data)
    assert python_rsf.header["n2"] == "3"
    assert python_rsf.header["label2"] == "Offset"
