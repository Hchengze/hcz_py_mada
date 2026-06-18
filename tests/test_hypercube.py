import numpy as np

from pymadagascar.core.axis import Axis
from pymadagascar.core.hypercube import Hypercube
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf


def test_1d_axis_coordinates_and_copy() -> None:
    axis = Axis(n=4, o=1.0, d=0.5, label="Time", unit="s", index=1)

    np.testing.assert_allclose(axis.coordinates(), np.array([1.0, 1.5, 2.0, 2.5]))

    updated = axis.copy(n=2, o=2.0)
    assert updated.n == 2
    assert updated.o == 2.0
    assert updated.d == 0.5
    assert updated.label == "Time"
    assert axis.n == 4


def test_2d_hypercube_properties() -> None:
    cube = Hypercube(
        [
            Axis(5, o=0.0, d=0.004, label="Time", unit="s"),
            Axis(3, o=100.0, d=25.0, label="Offset", unit="m"),
        ]
    )

    assert cube.ndim == 2
    assert cube.shape == (5, 3)
    assert cube.numpy_shape == (3, 5)
    assert cube.size == 15
    assert cube.leftsize(0) == 15
    assert cube.leftsize(1) == 3
    assert cube.leftsize(2) == 1
    assert cube.axis(1).label == "Time"
    assert cube.axis(2).label == "Offset"
    assert cube.axis(2).index == 2


def test_3d_hypercube_update_axis() -> None:
    cube = Hypercube([Axis(4), Axis(3), Axis(2, label="CMP")])

    updated = cube.update_axis(2, n=7, o=10.0, d=2.0, label="Offset")

    assert updated.shape == (4, 7, 2)
    assert updated.axis(2).o == 10.0
    assert updated.axis(2).d == 2.0
    assert updated.axis(2).label == "Offset"
    assert updated.axis(2).index == 2
    assert cube.shape == (4, 3, 2)


def test_header_to_hypercube() -> None:
    header = RSFHeader(
        {
            "n1": 4,
            "o1": 0.1,
            "d1": 0.004,
            "label1": "Time",
            "unit1": "s",
            "n2": 3,
            "o2": 100.0,
            "d2": 25.0,
            "label2": "Offset",
            "unit2": "m",
            "data_format": "native_float",
            "in": "./x.rsf@",
        }
    )

    cube = Hypercube.from_header(header)

    assert cube.shape == (4, 3)
    assert cube.numpy_shape == header.shape
    assert cube.axis(1) == Axis(4, o=0.1, d=0.004, label="Time", unit="s", index=1)
    assert cube.axis(2) == Axis(3, o=100.0, d=25.0, label="Offset", unit="m", index=2)


def test_hypercube_to_header_preserves_base_fields_and_axes() -> None:
    cube = Hypercube(
        [
            Axis(4, o=0.1, d=0.004, label="Time", unit="s"),
            Axis(3, o=100.0, d=25.0, label="Offset", unit="m"),
        ]
    )
    base = RSFHeader(
        {
            "data_format": "native_float",
            "esize": 4,
            "in": "./x.rsf@",
            "n3": 99,
            "label3": "stale",
        }
    )

    header = cube.to_header(base)

    assert header["data_format"] == "native_float"
    assert header["esize"] == "4"
    assert header["in"] == "./x.rsf@"
    assert header["n1"] == "4"
    assert header["o1"] == "0.1"
    assert header["d1"] == "0.004"
    assert header["label1"] == "Time"
    assert header["unit2"] == "m"
    assert "n3" not in header
    assert "label3" not in header


def test_window_updates_axis_metadata() -> None:
    cube = Hypercube([Axis(10, o=1.0, d=0.5, label="Time", unit="s"), Axis(4)])

    windowed = cube.window(axis=1, start=2, count=3, stride=3)

    assert windowed.axis(1).n == 3
    assert windowed.axis(1).o == 2.0
    assert windowed.axis(1).d == 1.5
    assert windowed.axis(1).label == "Time"
    assert windowed.shape == (3, 4)


def test_transpose_updates_axis_order_and_indexes() -> None:
    cube = Hypercube(
        [
            Axis(4, label="Time"),
            Axis(3, label="Offset"),
            Axis(2, label="CMP"),
        ]
    )

    transposed = cube.transpose([2, 1, 3])

    assert transposed.shape == (3, 4, 2)
    assert [axis.label for axis in transposed.axes] == ["Offset", "Time", "CMP"]
    assert [axis.index for axis in transposed.axes] == [1, 2, 3]


def test_transpose_accepts_zero_based_order() -> None:
    cube = Hypercube([Axis(4, label="Time"), Axis(3, label="Offset")])

    transposed = cube.transpose([1, 0])

    assert transposed.shape == (3, 4)
    assert [axis.label for axis in transposed.axes] == ["Offset", "Time"]


def test_hypercube_cooperates_with_rsf_array_header(tmp_path) -> None:
    data = np.arange(24, dtype=np.float32).reshape(2, 3, 4)
    path = tmp_path / "cube.rsf"
    write_rsf(
        path,
        data,
        RSFHeader(
            {
                "label1": "Time",
                "unit1": "s",
                "label2": "Offset",
                "label3": "CMP",
            }
        ),
    )

    rsf = read_rsf(path)
    cube = Hypercube.from_header(rsf.header)

    assert cube.shape == (4, 3, 2)
    assert cube.numpy_shape == rsf.data.shape
    assert cube.to_header(rsf.header).dimensions == rsf.header.dimensions
