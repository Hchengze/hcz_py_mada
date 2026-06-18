from pathlib import Path
import sys

import numpy as np
import pytest

from pymadagascar.cli.dd import main as dd_main
from pymadagascar.generic.dd import (
    DDError,
    convert_dtype_rsf,
    convert_endian_rsf,
    convert_to_ascii_float_rsf,
    copy_rsf,
)
from pymadagascar.io.rsf import RSFHeader, read_header, read_rsf, write_rsf
from pymadagascar.testing.compare import assert_rsf_allclose
from pymadagascar.testing.runner import original_madagascar_available, run_original_madagascar


def _header() -> RSFHeader:
    return RSFHeader(
        {
            "o1": 1.0,
            "d1": 0.5,
            "label1": "Sample",
            "unit1": "s",
            "o2": 10.0,
            "d2": 2.0,
            "label2": "Trace",
            "unit2": "km",
        }
    )


def _write_input(path: Path, data: np.ndarray | None = None) -> np.ndarray:
    values = (
        np.array([[0.2, 1.6, -1.6], [4.0, 5.0, 6.0]], dtype=np.float32)
        if data is None
        else data
    )
    write_rsf(path, values, _header())
    return values


def test_copy_rsf_preserves_data_and_metadata(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "copy.rsf"
    data = _write_input(input_path)

    result = copy_rsf(input_path, output_path)
    loaded = read_rsf(output_path)

    assert result.header_path == output_path.resolve()
    assert loaded.header["data_format"] == "native_float"
    assert loaded.header["label1"] == "Sample"
    np.testing.assert_array_equal(loaded.data, data)


def test_convert_float32_to_float64(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "double.rsf"
    data = _write_input(input_path)

    convert_dtype_rsf(input_path, output_path, "float64")
    loaded = read_rsf(output_path)

    assert loaded.data.dtype == np.float64
    assert loaded.header["data_format"] == "native_double"
    assert loaded.header["esize"] == "8"
    np.testing.assert_allclose(loaded.data, data.astype(np.float64))


def test_convert_float32_to_int32_rounds_by_default(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "int.rsf"
    _write_input(input_path)

    convert_dtype_rsf(input_path, output_path, "int32")
    loaded = read_rsf(output_path)

    assert loaded.data.dtype == np.int32
    assert loaded.header["data_format"] == "native_int"
    np.testing.assert_array_equal(
        loaded.data,
        np.array([[0, 2, -2], [4, 5, 6]], dtype=np.int32),
    )


def test_convert_float32_to_int32_can_truncate(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "int_trunc.rsf"
    _write_input(input_path)

    convert_dtype_rsf(input_path, output_path, "int", trunc=True)
    loaded = read_rsf(output_path)

    np.testing.assert_array_equal(
        loaded.data,
        np.array([[0, 1, -1], [4, 5, 6]], dtype=np.int32),
    )


def test_convert_float32_to_complex64(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "complex.rsf"
    data = _write_input(input_path)

    convert_dtype_rsf(input_path, output_path, "complex64")
    loaded = read_rsf(output_path)

    assert loaded.data.dtype == np.complex64
    assert loaded.header["data_format"] == "native_complex"
    assert loaded.header["esize"] == "8"
    np.testing.assert_allclose(loaded.data, data.astype(np.complex64))


def test_convert_endian_to_big_writes_xdr_payload(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "big.rsf"
    data = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    _write_input(input_path, data)

    convert_endian_rsf(input_path, output_path, "big")
    header = read_header(output_path)
    loaded = read_rsf(output_path)

    assert header["data_format"] == "xdr_float"
    assert header["esize"] == "4"
    assert header.binary_path(output_path).read_bytes()[:4] == b"\x3f\x80\x00\x00"
    np.testing.assert_array_equal(loaded.data, data)


def test_convert_endian_to_little_writes_native_little_payload(tmp_path: Path) -> None:
    if sys.byteorder != "little":
        pytest.skip("little-endian native RSF output is host-dependent")

    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "little.rsf"
    data = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    _write_input(input_path, data)

    convert_endian_rsf(input_path, output_path, "little")
    header = read_header(output_path)
    loaded = read_rsf(output_path)

    assert header["data_format"] == "native_float"
    assert header.binary_path(output_path).read_bytes()[:4] == b"\x00\x00\x80\x3f"
    np.testing.assert_array_equal(loaded.data, data)


def test_convert_dtype_rejects_unsupported_type(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "bad.rsf"
    _write_input(input_path)

    with pytest.raises(DDError, match="supported dtypes"):
        convert_dtype_rsf(input_path, output_path, "complex128")

    assert not output_path.exists()


def test_dd_cli_type_conversion(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "double.rsf"
    data = _write_input(input_path)

    code = dd_main([str(input_path), "out=" + str(output_path), "type=float64"])
    loaded = read_rsf(output_path)

    assert code == 0
    assert loaded.header["data_format"] == "native_double"
    np.testing.assert_allclose(loaded.data, data.astype(np.float64))


def test_dd_cli_endian_conversion(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "big.rsf"
    _write_input(input_path, np.array([1.0, 2.0], dtype=np.float32))

    code = dd_main([str(input_path), "out=" + str(output_path), "endian=big"])
    header = read_header(output_path)

    assert code == 0
    assert header["data_format"] == "xdr_float"


def test_convert_to_ascii_float_writes_text_sidecar(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "ascii.rsf"
    data = _write_input(input_path)

    convert_to_ascii_float_rsf(input_path, output_path)
    header = read_header(output_path)
    loaded = read_rsf(output_path)

    assert header["data_format"] == "ascii_float"
    assert header["esize"] == "0"
    assert b"\x00\x00\x80\x3f" not in header.binary_path(output_path).read_bytes()
    np.testing.assert_allclose(loaded.data, data)


def test_dd_cli_form_ascii_converts_to_ascii_float(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "ascii.rsf"
    data = _write_input(input_path)

    code = dd_main([str(input_path), "out=" + str(output_path), "form=ascii"])
    loaded = read_rsf(output_path)

    assert code == 0
    assert loaded.header["data_format"] == "ascii_float"
    assert loaded.header["esize"] == "0"
    np.testing.assert_allclose(loaded.data, data)


def test_dd_cli_ascii_float_to_native_binary(tmp_path: Path) -> None:
    ascii_path = tmp_path / "ascii.rsf"
    native_path = tmp_path / "native.rsf"
    data = np.array([[1.0, 2.5, -3.0]], dtype=np.float32)
    write_rsf(ascii_path, data, _header(), data_format="ascii_float")

    code = dd_main([str(ascii_path), "out=" + str(native_path), "form=native"])
    header = read_header(native_path)
    loaded = read_rsf(native_path)

    assert code == 0
    assert header["data_format"] == "native_float"
    assert header["esize"] == "4"
    np.testing.assert_allclose(loaded.data, data)


def test_dd_cli_form_ascii_rejects_non_float_type(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "ascii_int.rsf"
    _write_input(input_path)

    code = dd_main([str(input_path), "out=" + str(output_path), "form=ascii", "type=int32"])

    assert code == 2
    assert "form=ascii only supports float32/float64" in capsys.readouterr().err
    assert not output_path.exists()


def test_original_sfdd_copy_comparison_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfdd"):
        pytest.skip("Original Madagascar sfdd is not installed")

    input_path = tmp_path / "input.rsf"
    original = tmp_path / "original.rsf"
    python = tmp_path / "python.rsf"
    _write_input(input_path, np.arange(6, dtype=np.float32))

    run_original_madagascar(
        ["sfdd", "in=input.rsf", "out=original.rsf", "type=float"],
        cwd=tmp_path,
        require_program="sfdd",
    )
    assert dd_main([str(input_path), "out=" + str(python), "type=float32"]) == 0

    assert_rsf_allclose(original, python, ignore_keys={"in"})


def test_original_sfdd_ascii_float_comparison_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfdd"):
        pytest.skip("Original Madagascar sfdd is not installed")

    input_path = tmp_path / "input.rsf"
    original = tmp_path / "original_ascii.rsf"
    python = tmp_path / "python_ascii.rsf"
    _write_input(input_path, np.arange(6, dtype=np.float32).reshape(2, 3) / 3.0)

    run_original_madagascar(
        ["sfdd", "in=input.rsf", "out=original_ascii.rsf", "form=ascii", "type=float"],
        cwd=tmp_path,
        require_program="sfdd",
    )
    assert dd_main([str(input_path), "out=" + str(python), "form=ascii", "type=float32"]) == 0

    assert_rsf_allclose(original, python, ignore_keys={"in", "esize"})
