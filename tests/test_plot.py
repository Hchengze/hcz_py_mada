from pathlib import Path

import numpy as np
import pytest

from pymadagascar.cli.graph import main as graph_main
from pymadagascar.cli.grey import main as grey_main
from pymadagascar.cli.wiggle import main as wiggle_main
from pymadagascar.io.rsf import RSFHeader, write_rsf
from pymadagascar.plot._common import PlotError, pyplot
from pymadagascar.plot.graph import graph
from pymadagascar.plot.grey import grey
from pymadagascar.plot.wiggle import wiggle


def _header() -> RSFHeader:
    return RSFHeader(
        {
            "o1": 0.0,
            "d1": 0.004,
            "label1": "Time",
            "unit1": "s",
            "o2": 100.0,
            "d2": 25.0,
            "label2": "Trace",
            "unit2": "m",
        }
    )


def _assert_png(path: Path) -> None:
    assert path.exists()
    assert path.stat().st_size > 100
    assert path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def _assert_pdf(path: Path) -> None:
    assert path.exists()
    assert path.stat().st_size > 100
    assert path.read_bytes()[:4] == b"%PDF"


def _close(fig: object) -> None:
    pyplot().close(fig)


def test_graph_writes_png(tmp_path: Path) -> None:
    output = tmp_path / "graph.png"
    data = np.linspace(-1.0, 1.0, 64, dtype=np.float32)

    fig = graph(data, _header(), output_path=output, title="Trace")
    _close(fig)

    _assert_png(output)


def test_graph_writes_pdf(tmp_path: Path) -> None:
    output = tmp_path / "graph.pdf"
    data = np.linspace(-1.0, 1.0, 64, dtype=np.float32)

    fig = graph(data, _header(), output_path=output)
    _close(fig)

    _assert_pdf(output)


def test_grey_writes_png(tmp_path: Path) -> None:
    output = tmp_path / "grey.png"
    data = np.arange(60, dtype=np.float32).reshape(6, 10)

    fig = grey(data, _header(), output_path=output, clip=30.0, cmap="viridis")
    _close(fig)

    _assert_png(output)


def test_grey_transpose_writes_png(tmp_path: Path) -> None:
    output = tmp_path / "grey_transpose.png"
    data = np.arange(60, dtype=np.float32).reshape(6, 10)

    fig = grey(data, _header(), output_path=output, transpose=True, pclip=95.0)
    _close(fig)

    _assert_png(output)


def test_wiggle_writes_png(tmp_path: Path) -> None:
    output = tmp_path / "wiggle.png"
    x = np.linspace(0.0, 2.0 * np.pi, 80, dtype=np.float32)
    data = np.stack([np.sin(x + phase) for phase in np.linspace(0, 1, 8)], axis=0).astype(np.float32)

    fig = wiggle(data, _header(), output_path=output, scale=0.5)
    _close(fig)

    _assert_png(output)


def test_plot_rejects_bad_output_extension(tmp_path: Path) -> None:
    output = tmp_path / "figure.bmp"

    with pytest.raises(PlotError, match="out= must end"):
        graph(np.arange(5, dtype=np.float32), _header(), output_path=output)

    assert not output.exists()


def test_graph_rejects_2d_data(tmp_path: Path) -> None:
    with pytest.raises(PlotError, match="graph expects 1D"):
        graph(np.ones((2, 3), dtype=np.float32), _header(), output_path=tmp_path / "bad.png")


def test_grey_rejects_1d_data(tmp_path: Path) -> None:
    with pytest.raises(PlotError, match="grey expects 2D"):
        grey(np.ones(3, dtype=np.float32), _header(), output_path=tmp_path / "bad.png")


def test_wiggle_rejects_bad_scale(tmp_path: Path) -> None:
    with pytest.raises(PlotError, match="scale= must be positive"):
        wiggle(np.ones((2, 3), dtype=np.float32), _header(), output_path=tmp_path / "bad.png", scale=0)


def test_grey_cli(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output = tmp_path / "grey.png"
    write_rsf(input_path, np.arange(60, dtype=np.float32).reshape(6, 10), _header())

    code = grey_main([str(input_path), "out=" + str(output), "title=Panel", "pclip=90", "cmap=magma"])

    assert code == 0
    _assert_png(output)


def test_graph_cli(tmp_path: Path) -> None:
    input_path = tmp_path / "trace.rsf"
    output = tmp_path / "graph.png"
    write_rsf(input_path, np.linspace(0.0, 1.0, 32, dtype=np.float32), _header())

    code = graph_main([str(input_path), "out=" + str(output), "clip=1.0"])

    assert code == 0
    _assert_png(output)


def test_wiggle_cli(tmp_path: Path) -> None:
    input_path = tmp_path / "panel.rsf"
    output = tmp_path / "wiggle.png"
    x = np.linspace(0.0, 2.0 * np.pi, 48, dtype=np.float32)
    data = np.stack([np.sin(x + phase) for phase in np.linspace(0, 1, 5)], axis=0).astype(np.float32)
    write_rsf(input_path, data, _header())

    code = wiggle_main([str(input_path), "out=" + str(output), "scale=0.6", "fill=no"])

    assert code == 0
    _assert_png(output)


def test_cli_reports_parameter_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    input_path = tmp_path / "input.rsf"
    output = tmp_path / "bad.bmp"
    write_rsf(input_path, np.linspace(0.0, 1.0, 16, dtype=np.float32), _header())

    code = graph_main([str(input_path), "out=" + str(output)])

    assert code == 2
    assert "out= must end with .png or .pdf" in capsys.readouterr().err
    assert not output.exists()
