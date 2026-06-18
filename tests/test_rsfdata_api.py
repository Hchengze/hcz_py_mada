from pathlib import Path

import numpy as np

import pymadagascar as pm
from pymadagascar import RSFData, read, write
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf
from pymadagascar.plot._common import pyplot


def _header_1d(n1: int = 8, d1: float = 0.1) -> RSFHeader:
    return RSFHeader(
        {
            "n1": n1,
            "o1": 0.0,
            "d1": d1,
            "label1": "Time",
            "unit1": "s",
        }
    )


def _header_2d(n1: int = 8, n2: int = 3, d1: float = 0.1) -> RSFHeader:
    header = _header_1d(n1=n1, d1=d1)
    header["n2"] = n2
    header["o2"] = 0.0
    header["d2"] = 1.0
    header["label2"] = "Trace"
    return header


def _assert_png(path: Path) -> None:
    assert path.exists()
    assert path.stat().st_size > 100
    assert path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def test_read_and_write_roundtrip(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "output.rsf"
    data = np.arange(8, dtype=np.float32)
    write_rsf(input_path, data, _header_1d())

    rsf = read(input_path)
    written = rsf.write(output_path)
    loaded = read_rsf(output_path)

    assert isinstance(rsf, RSFData)
    assert written.path == output_path.resolve()
    np.testing.assert_array_equal(loaded.data, data)
    assert loaded.header["label1"] == "Time"


def test_top_level_write_accepts_array_and_rsfdata(tmp_path: Path) -> None:
    first_path = tmp_path / "first.rsf"
    second_path = tmp_path / "second.rsf"
    data = np.arange(4, dtype=np.float32)

    first = write(first_path, data, _header_1d(n1=4))
    second = write(second_path, first)

    assert isinstance(pm.read(first_path), RSFData)
    assert second.path == second_path.resolve()
    np.testing.assert_array_equal(read_rsf(second_path).data, data)


def test_chain_window_scale_does_not_modify_original(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    data = np.arange(8, dtype=np.float32)
    write_rsf(input_path, data, _header_1d())

    original = read(input_path)
    result = original.window(axis=1, f=2, n=3).scale(2.0)

    np.testing.assert_array_equal(original.numpy(), data)
    np.testing.assert_array_equal(result.numpy(), np.array([4.0, 6.0, 8.0], dtype=np.float32))
    assert result.header["n1"] == "3"
    assert result.header["o1"] == "0.2"
    assert original.header["n1"] == "8"


def test_bandpass_chain_preserves_passband_sine(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    n = 1000
    d = 0.001
    t = np.arange(n, dtype=np.float64) * d
    data = np.sin(2.0 * np.pi * 20.0 * t).astype(np.float32)
    write_rsf(input_path, data, _header_1d(n1=n, d1=d))

    filtered = read(input_path).bandpass(flo=10.0, fhi=30.0)

    np.testing.assert_allclose(filtered.numpy(), data, atol=1e-5)
    assert filtered.header["label1"] == "Time"


def test_attr_reports_in_memory_statistics(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    data = np.array([-2.0, 0.0, 4.0], dtype=np.float32)
    write_rsf(input_path, data, _header_1d(n1=3))

    stats = read(input_path).attr()

    assert stats["path"] == input_path.resolve()
    assert stats["shape"] == (3,)
    assert stats["min"] == -2.0
    assert stats["max"] == 4.0
    assert stats["nonzero_count"] == 2


def test_plot_grey_and_graph_write_png(tmp_path: Path) -> None:
    panel = RSFData(np.arange(24, dtype=np.float32).reshape(3, 8), _header_2d())
    trace = RSFData(np.linspace(-1.0, 1.0, 16, dtype=np.float32), _header_1d(n1=16))
    grey_path = tmp_path / "panel.png"
    graph_path = tmp_path / "trace.png"

    grey_fig = panel.plot_grey(output_path=grey_path, title="Panel")
    graph_fig = trace.plot_graph(output_path=graph_path, title="Trace")
    pyplot().close(grey_fig)
    pyplot().close(graph_fig)

    _assert_png(grey_path)
    _assert_png(graph_path)


def test_header_and_numpy_are_defensive_copies() -> None:
    data = np.arange(4, dtype=np.float32)
    rsf = RSFData(data, _header_1d(n1=4))

    header = rsf.header
    header["label1"] = "Edited"
    array = rsf.numpy()
    array[0] = 99.0

    assert rsf.header["label1"] == "Time"
    np.testing.assert_array_equal(rsf.numpy(), data)


def test_copy_and_inplace_rules() -> None:
    data = np.arange(4, dtype=np.float32)
    original = RSFData(data, _header_1d(n1=4))
    copied = original.copy()

    returned = copied.scale(2.0, inplace=True)

    assert returned is copied
    np.testing.assert_array_equal(copied.numpy(), data * 2.0)
    np.testing.assert_array_equal(original.numpy(), data)


def test_stack_updates_shape_and_header() -> None:
    data = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    rsf = RSFData(data, _header_2d(n1=2, n2=2))

    stacked = rsf.stack(axis=2, nonzero=False)

    np.testing.assert_array_equal(stacked.numpy(), np.array([2.0, 3.0], dtype=np.float32))
    assert stacked.shape == (2,)
    assert stacked.header.dimensions == (2,)
    assert rsf.shape == (2, 2)
