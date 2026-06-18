from pathlib import Path

import numpy as np
import pytest

from pymadagascar.cli.reshape import main as reshape_main
from pymadagascar.cli.transp import main as transp_main
from pymadagascar.generic.transp import (
    TransposeError,
    reshape_rsf,
    transpose_array,
    transpose_rsf,
)
from pymadagascar.io.rsf import RSFArray, RSFHeader, read_rsf, write_rsf
from pymadagascar.testing.compare import assert_rsf_allclose
from pymadagascar.testing.runner import original_madagascar_available, run_original_madagascar


def _header_2d() -> RSFHeader:
    return RSFHeader(
        {
            "n1": 4,
            "n2": 3,
            "o1": 1.0,
            "d1": 0.5,
            "label1": "Time",
            "unit1": "s",
            "o2": 10.0,
            "d2": 2.0,
            "label2": "Trace",
            "unit2": "km",
            "data_format": "native_float",
            "esize": 4,
        }
    )


def _header_3d() -> RSFHeader:
    return RSFHeader(
        {
            "n1": 4,
            "n2": 3,
            "n3": 2,
            "o1": 1.0,
            "d1": 0.5,
            "label1": "Time",
            "unit1": "s",
            "o2": 10.0,
            "d2": 2.0,
            "label2": "Trace",
            "unit2": "km",
            "o3": 100.0,
            "d3": 25.0,
            "label3": "Shot",
            "unit3": "m",
            "data_format": "native_float",
            "esize": 4,
        }
    )


def test_2d_transpose_array_and_header() -> None:
    data = np.arange(12, dtype=np.float32).reshape(3, 4)

    result = transpose_array(data, _header_2d(), order=(2, 1))

    np.testing.assert_array_equal(result.data, data.T)
    assert result.header.dimensions == (3, 4)
    assert result.header["o1"] == "10"
    assert result.header["d1"] == "2"
    assert result.header["label1"] == "Trace"
    assert result.header["unit1"] == "km"
    assert result.header["o2"] == "1"
    assert result.header["d2"] == "0.5"
    assert result.header["label2"] == "Time"
    assert result.header["unit2"] == "s"


def test_3d_transpose_array() -> None:
    data = np.arange(24, dtype=np.float32).reshape(2, 3, 4)

    result = transpose_array(data, _header_3d(), order=(3, 1, 2))
    expected = np.transpose(data, axes=(1, 2, 0))

    np.testing.assert_array_equal(result.data, expected)
    assert result.header.dimensions == (2, 4, 3)
    assert result.header["label1"] == "Shot"
    assert result.header["label2"] == "Time"
    assert result.header["label3"] == "Trace"


def test_transpose_rejects_illegal_order() -> None:
    data = np.arange(12, dtype=np.float32).reshape(3, 4)

    with pytest.raises(TransposeError, match="1-based permutation"):
        transpose_array(data, _header_2d(), order=(0, 1))
    with pytest.raises(TransposeError, match="exactly 2"):
        transpose_array(data, _header_2d(), order=(2, 1, 3))


def test_transpose_rsf_writes_output(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "output.rsf"
    data = np.arange(12, dtype=np.float32).reshape(3, 4)
    write_rsf(input_path, data, _header_2d())

    result = transpose_rsf(input_path, output_path, order=(2, 1))
    loaded = read_rsf(output_path)

    assert result.header_path == output_path.resolve()
    np.testing.assert_array_equal(loaded.data, data.T)
    assert loaded.header.dimensions == (3, 4)


def test_reshape_rsf_updates_dimensions_and_preserves_dtype(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "reshaped.rsf"
    data = np.arange(12, dtype=np.float32).reshape(3, 4)
    write_rsf(input_path, data, _header_2d())

    result = reshape_rsf(input_path, output_path, shape=(6, 2))
    loaded = read_rsf(output_path)

    assert loaded.data.dtype == np.float32
    assert loaded.header.dimensions == (6, 2)
    assert loaded.data.shape == (2, 6)
    np.testing.assert_array_equal(loaded.data.ravel(), data.ravel())
    assert result.header["label1"] == "Time"
    assert result.header["label2"] == "Trace"


def test_reshape_rsf_rejects_sample_count_mismatch(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "bad.rsf"
    write_rsf(input_path, np.arange(12, dtype=np.float32).reshape(3, 4), _header_2d())

    with pytest.raises(TransposeError, match="sample count mismatch"):
        reshape_rsf(input_path, output_path, shape=(5, 2))

    assert not output_path.exists()


def test_transp_cli(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "output.rsf"
    data = np.arange(12, dtype=np.float32).reshape(3, 4)
    write_rsf(input_path, data, _header_2d())

    code = transp_main([str(input_path), "out=" + str(output_path), "order=2,1"])
    loaded = read_rsf(output_path)

    assert code == 0
    np.testing.assert_array_equal(loaded.data, data.T)
    assert loaded.header["label1"] == "Trace"


def test_transp_cli_reports_bad_order(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "bad.rsf"
    write_rsf(input_path, np.arange(12, dtype=np.float32).reshape(3, 4), _header_2d())

    code = transp_main([str(input_path), "out=" + str(output_path), "order=1,1"])

    assert code == 2
    assert "1-based permutation" in capsys.readouterr().err
    assert not output_path.exists()


def test_reshape_cli(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "reshaped.rsf"
    data = np.arange(12, dtype=np.float32).reshape(3, 4)
    write_rsf(input_path, data, _header_2d())

    code = reshape_main([str(input_path), "out=" + str(output_path), "n1=6", "n2=2"])
    loaded = read_rsf(output_path)

    assert code == 0
    assert loaded.header.dimensions == (6, 2)
    np.testing.assert_array_equal(loaded.data.ravel(), data.ravel())


def test_reshape_cli_reports_mismatch(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "bad.rsf"
    write_rsf(input_path, np.arange(12, dtype=np.float32).reshape(3, 4), _header_2d())

    code = reshape_main([str(input_path), "out=" + str(output_path), "n1=5", "n2=2"])

    assert code == 2
    assert "sample count mismatch" in capsys.readouterr().err
    assert not output_path.exists()


def test_original_sftransp_comparison_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sftransp"):
        pytest.skip("Original Madagascar sftransp is not installed")

    input_path = tmp_path / "input.rsf"
    original = tmp_path / "original.rsf"
    python = tmp_path / "python.rsf"
    data = np.arange(12, dtype=np.float32).reshape(3, 4)
    write_rsf(input_path, data, _header_2d())

    run_original_madagascar(
        ["sftransp", "in=input.rsf", "out=original.rsf", "plane=12"],
        cwd=tmp_path,
        require_program="sftransp",
    )
    assert transp_main([str(input_path), "out=" + str(python), "order=2,1"]) == 0

    assert_rsf_allclose(original, python, ignore_keys={"in"})
