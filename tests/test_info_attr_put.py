from pathlib import Path

import numpy as np
import pytest

from pymadagascar.cli.attr import main as attr_main
from pymadagascar.cli.info import main as info_main
from pymadagascar.cli.put import main as put_main
from pymadagascar.generic.attr import attr_rsf, format_attr
from pymadagascar.generic.info import format_info, info_rsf
from pymadagascar.generic.put import PutHeaderError, put_header
from pymadagascar.io.rsf import RSFHeader, read_header, read_rsf, write_rsf
from pymadagascar.testing.compare import assert_rsf_allclose, compare_arrays
from pymadagascar.testing.runner import original_madagascar_available, run_original_madagascar


def _write_sample(path: Path, data: np.ndarray | None = None) -> np.ndarray:
    if data is None:
        data = np.array([[0.0, 1.0, 2.0], [3.0, 4.0, 5.0]], dtype=np.float32)
    write_rsf(
        path,
        data,
        RSFHeader(
            {
                "o1": 1.0,
                "d1": 0.5,
                "label1": "Time",
                "unit1": "s",
                "o2": 10.0,
                "d2": 2.0,
                "label2": "Trace",
                "unit2": "km",
            }
        ),
    )
    return data


def test_info_rsf_returns_header_and_file_details(tmp_path: Path) -> None:
    path = tmp_path / "sample.rsf"
    data = _write_sample(path)

    info = info_rsf(path)
    text = format_info(info)

    assert info["path"] == path
    assert info["data_format"] == "native_float"
    assert info["dimensions"] == (3, 2)
    assert info["numpy_shape"] == data.shape
    assert info["sample_count"] == data.size
    assert info["binary_exists"] is True
    assert info["expected_bytes"] == data.nbytes
    assert "dimensions: n1=3 n2=2" in text
    assert "axis1 o=1 d=0.5 label=Time unit=s" in text


def test_attr_rsf_statistics(tmp_path: Path) -> None:
    path = tmp_path / "stats.rsf"
    data = np.array([0.0, 1.0, 2.0, np.nan, 4.0], dtype=np.float32)
    write_rsf(path, data, {"label1": "Sample"})

    stats = attr_rsf(path)
    text = format_attr(stats)

    valid = np.array([0.0, 1.0, 2.0, 4.0])
    assert stats["shape"] == (5,)
    assert stats["dtype"] == np.dtype("float32")
    assert stats["min"] == 0.0
    assert stats["max"] == 4.0
    assert stats["mean"] == float(np.mean(valid))
    assert stats["rms"] == float(np.sqrt(np.mean(valid * valid)))
    assert stats["variance"] == float(np.var(valid, ddof=1))
    assert stats["nonzero_count"] == 3
    assert stats["nan_count"] == 1
    assert "nan_count: 1" in text
    assert "nonzero_count: 3" in text


def test_put_header_modifies_axis_metadata_and_adds_key(tmp_path: Path) -> None:
    path = tmp_path / "input.rsf"
    output = tmp_path / "output.rsf"
    data = _write_sample(path)

    result = put_header(
        path,
        {"o1": 2.5, "d1": 0.25, "label1": "Depth", "unit1": "m", "survey": "demo"},
        output_path=output,
    )
    loaded = read_rsf(output)

    assert result.header_path == output.resolve()
    assert loaded.header["o1"] == "2.5"
    assert loaded.header["d1"] == "0.25"
    assert loaded.header["label1"] == "Depth"
    assert loaded.header["unit1"] == "m"
    assert loaded.header["survey"] == "demo"
    np.testing.assert_array_equal(loaded.data, data)


def test_put_header_default_output_does_not_overwrite_input(tmp_path: Path) -> None:
    path = tmp_path / "input.rsf"
    _write_sample(path)
    original_header = read_header(path)

    result = put_header(path, {"label1": "Changed"})

    assert result.header_path == (tmp_path / "input_put.rsf").resolve()
    assert read_header(path)["label1"] == original_header["label1"]
    assert read_header(result.header_path)["label1"] == "Changed"


def test_put_header_rejects_shape_header_mismatch(tmp_path: Path) -> None:
    path = tmp_path / "input.rsf"
    _write_sample(path)

    with pytest.raises(PutHeaderError, match="do not match binary data shape"):
        put_header(path, {"n1": 4}, output_path=tmp_path / "bad.rsf")

    assert not (tmp_path / "bad.rsf").exists()


def test_put_header_rejects_protected_binary_keys(tmp_path: Path) -> None:
    path = tmp_path / "input.rsf"
    _write_sample(path)

    with pytest.raises(PutHeaderError, match="data_format"):
        put_header(path, {"data_format": "native_double"}, output_path=tmp_path / "bad.rsf")


def test_info_cli_outputs_text(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "sample.rsf"
    _write_sample(path)

    code = info_main([str(path)])
    captured = capsys.readouterr()

    assert code == 0
    assert "data_format: native_float" in captured.out
    assert "dimensions: n1=3 n2=2" in captured.out
    assert "axis1 o=1 d=0.5 label=Time unit=s" in captured.out


def test_attr_cli_outputs_statistics(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "stats.rsf"
    write_rsf(path, np.array([0.0, 2.0, 4.0], dtype=np.float32))

    code = attr_main([str(path)])
    captured = capsys.readouterr()

    assert code == 0
    assert "min: 0" in captured.out
    assert "max: 4" in captured.out
    assert "mean: 2" in captured.out
    assert "nonzero_count: 2" in captured.out


def test_put_cli_writes_updated_copy(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "input.rsf"
    output = tmp_path / "output.rsf"
    data = _write_sample(path)

    code = put_main([str(path), "out=" + str(output), "label1=Depth", "unit1=m", "survey=demo"])
    captured = capsys.readouterr()
    loaded = read_rsf(output)

    assert code == 0
    assert "wrote:" in captured.out
    assert loaded.header["label1"] == "Depth"
    assert loaded.header["unit1"] == "m"
    assert loaded.header["survey"] == "demo"
    np.testing.assert_array_equal(loaded.data, data)
    assert read_header(path)["label1"] == "Time"


def test_put_cli_reports_shape_mismatch(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "input.rsf"
    output = tmp_path / "bad.rsf"
    _write_sample(path)

    code = put_main([str(path), "out=" + str(output), "n1=4"])
    captured = capsys.readouterr()

    assert code == 2
    assert "do not match binary data shape" in captured.err
    assert not output.exists()


def test_original_sfin_smoke_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfin"):
        pytest.skip("Original Madagascar sfin is not installed")

    path = tmp_path / "sample.rsf"
    _write_sample(path)
    result = run_original_madagascar(
        ["sfin", "sample.rsf"],
        cwd=tmp_path,
        require_program="sfin",
        decode_stdout=True,
    )

    assert result.returncode == 0
    assert "n1=3" in result.stdout


def test_original_sfattr_smoke_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfattr"):
        pytest.skip("Original Madagascar sfattr is not installed")

    path = tmp_path / "sample.rsf"
    _write_sample(path, np.array([0.0, 1.0, 2.0], dtype=np.float32))
    result = run_original_madagascar(
        ["sfattr"],
        cwd=tmp_path,
        require_program="sfattr",
        stdin_path=path,
        decode_stdout=True,
    )

    assert result.returncode == 0
    assert "mean" in result.stdout


def test_original_sfput_comparison_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfput"):
        pytest.skip("Original Madagascar sfput is not installed")

    path = tmp_path / "sample.rsf"
    original = tmp_path / "original.rsf"
    python = tmp_path / "python.rsf"
    data = _write_sample(path)

    run_original_madagascar(
        ["sfput", "in=sample.rsf", "out=original.rsf", "label1=Depth", "unit1=m"],
        cwd=tmp_path,
        require_program="sfput",
    )
    put_header(path, {"label1": "Depth", "unit1": "m"}, output_path=python)

    assert read_header(python)["label1"] == "Depth"
    assert read_header(python)["unit1"] == "m"
    assert compare_arrays(read_rsf(original).data, data)
    assert_rsf_allclose(original, python, ignore_keys={"in"})
